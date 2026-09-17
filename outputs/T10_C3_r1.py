import copy


def validate_patch(document, operations, protected_paths) -> dict:
    """
    Validate JSON patch operations against allowed operations, valid paths,
    the existing document structure, and protected paths.
    
    Returns dict with "valid" (bool) and "errors" (list of str).
    Never raises.
    """
    errors = []
    
    try:
        # Input validation
        if not isinstance(operations, list):
            return {"valid": False, "errors": ["operations must be a list"]}
        
        if not isinstance(protected_paths, list):
            return {"valid": False, "errors": ["protected_paths must be a list"]}
        
        # Validate protected_paths are strings
        for path in protected_paths:
            if not isinstance(path, str):
                return {"valid": False, "errors": ["protected_paths must contain only strings"]}
        
        # Work on a copy of the document
        working_doc = copy.deepcopy(document)
        
        # Process each operation
        for i, operation in enumerate(operations):
            op_errors = validate_operation(operation, working_doc, protected_paths)
            if op_errors:
                for error in op_errors:
                    errors.append(f"Operation {i}: {error}")
            else:
                # Apply operation to working copy on success
                try:
                    working_doc = apply_operation(working_doc, operation)
                except Exception as e:
                    errors.append(f"Operation {i}: Failed to apply - {str(e)}")
    
    except Exception as e:
        return {"valid": False, "errors": [f"Validation error: {str(e)}"]}
    
    return {"valid": len(errors) == 0, "errors": errors}


def unescape_json_pointer(token):
    """Unescape JSON Pointer tokens (RFC 6901)"""
    token = token.replace("~1", "/")
    token = token.replace("~0", "~")
    return token


def parse_pointer(path):
    """Parse a JSON Pointer path into tokens. Returns None if invalid."""
    if not isinstance(path, str):
        return None
    if path == "":
        return []
    if not path.startswith("/"):
        return None
    
    tokens = path[1:].split("/")
    return [unescape_json_pointer(token) for token in tokens]


def get_value(doc, tokens):
    """Get value at path, return (exists, value)"""
    current = doc
    for token in tokens:
        if isinstance(current, dict):
            if token in current:
                current = current[token]
            else:
                return False, None
        elif isinstance(current, list):
            try:
                index = int(token)
                if -len(current) <= index < len(current):
                    current = current[index]
                else:
                    return False, None
            except ValueError:
                return False, None
        else:
            return False, None
    return True, current


def get_parent(doc, tokens):
    """Get parent object and last token, return (exists, parent, last_token)"""
    if not tokens:
        return False, None, None
    
    parent_tokens = tokens[:-1]
    last_token = tokens[-1]
    
    exists, parent = get_value(doc, parent_tokens)
    return exists, parent, last_token


def is_protected(path, protected_paths):
    """Check if operating on path would violate protected paths"""
    for protected in protected_paths:
        if path == protected:
            return True
        if protected and path.startswith(protected + "/"):
            return True
    return False


def would_remove_protected(path, protected_paths):
    """Check if removing path would also remove a protected path"""
    for protected in protected_paths:
        if protected.startswith(path + "/"):
            return True
    return False


def validate_operation(operation, doc, protected_paths):
    """Validate a single operation. Returns list of errors (empty if valid)"""
    errors = []
    
    if not isinstance(operation, dict):
        errors.append("Operation must be a dict")
        return errors
    
    if "op" not in operation:
        errors.append("Missing 'op' field")
        return errors
    
    op = operation["op"]
    
    if op not in {"add", "remove", "replace"}:
        errors.append(f"Invalid operation '{op}'")
        return errors
    
    if "path" not in operation:
        errors.append("Missing 'path' field")
        return errors
    
    path = operation["path"]
    tokens = parse_pointer(path)
    
    if tokens is None:
        errors.append("Invalid path format")
        return errors
    
    if op in {"add", "replace"}:
        if "value" not in operation:
            errors.append(f"Missing 'value' field for '{op}'")
            return errors
    
    if is_protected(path, protected_paths):
        errors.append("Cannot modify protected path")
        return errors
    
    if op == "remove":
        if would_remove_protected(path, protected_paths):
            errors.append("Cannot remove path containing protected paths")
            return errors
    
    if op == "remove":
        if not tokens:
            errors.append("Cannot remove root")
        else:
            exists, _ = get_value(doc, tokens)
            if not exists:
                errors.append("Path does not exist")
    
    elif op == "replace":
        if tokens:
            exists, _ = get_value(doc, tokens)
            if not exists:
                errors.append("Path does not exist")
    
    elif op == "add":
        if tokens:
            exists, parent, last_token = get_parent(doc, tokens)
            if not exists:
                errors.append("Parent path does not exist")
            elif isinstance(parent, dict):
                pass
            elif isinstance(parent, list):
                try:
                    index = int(last_token)
                    if not (-len(parent) - 1 <= index <= len(parent)):
                        errors.append("Array index out of bounds")
                except ValueError:
                    if last_token != "-":
                        errors.append("Invalid array index")
            else:
                errors.append("Cannot add to non-dict/list")
    
    return errors


def apply_operation(doc, operation):
    """Apply an operation to a document. Returns new document."""
    working = copy.deepcopy(doc)
    op = operation["op"]
    path = operation["path"]
    tokens = parse_pointer(path)
    
    if not tokens:
        if op in {"replace", "add"}:
            return operation["value"]
        return working
    
    exists, parent, last_token = get_parent(working, tokens)
    if not exists:
        return working
    
    if op == "remove":
        if isinstance(parent, dict) and last_token in parent:
            del parent[last_token]
        elif isinstance(parent, list):
            try:
                index = int(last_token)
                if -len(parent) <= index < len(parent):
                    del parent[index]
            except ValueError:
                pass
    
    elif op == "replace":
        if isinstance(parent, dict):
            parent[last_token] = operation["value"]
        elif isinstance(parent, list):
            try:
                index = int(last_token)
                if -len(parent) <= index < len(parent):
                    parent[index] = operation["value"]
            except ValueError:
                pass
    
    elif op == "add":
        if isinstance(parent, dict):
            parent[last_token] = operation["value"]
        elif isinstance(parent, list):
            try:
                index = int(last_token)
                if index == len(parent) or last_token == "-":
                    parent.append(operation["value"])
                else:
                    parent.insert(index, operation["value"])
            except ValueError:
                pass
    
    return working
