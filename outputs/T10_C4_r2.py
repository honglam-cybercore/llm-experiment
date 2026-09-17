def validate_patch(document, operations, protected_paths) -> dict:
    """
    Validate JSON patch operations against allowed operations, valid paths,
    document structure, and protected paths.
    """
    try:
        if not isinstance(operations, list):
            return {"valid": False, "errors": ["Operations must be a list"]}
        if not isinstance(protected_paths, list):
            return {"valid": False, "errors": ["Protected paths must be a list"]}
        
        import copy
        current_doc = copy.deepcopy(document)
        
        for op in operations:
            error = _validate_operation(op, current_doc, protected_paths)
            if error:
                return {"valid": False, "errors": [error]}
            
            try:
                current_doc = _apply_operation(current_doc, op)
            except Exception:
                return {"valid": False, "errors": ["Failed to apply operation"]}
        
        return {"valid": True, "errors": []}
    except Exception:
        return {"valid": False, "errors": ["Validation failed"]}


def _validate_operation(op, document, protected_paths):
    if not isinstance(op, dict):
        return "Operation must be a dictionary"
    
    if "op" not in op or "path" not in op:
        return "Missing required fields"
    
    op_type = op["op"]
    path = op["path"]
    
    if not isinstance(path, str):
        return "Path must be a string"
    
    if op_type not in ("add", "remove", "replace"):
        return "Unsupported operation"
    
    if path and not path.startswith("/"):
        return "Path must be empty or start with '/'"
    
    if _has_invalid_escapes(path):
        return "Invalid escape sequence in path"
    
    for protected in protected_paths:
        if path == protected:
            return "Cannot modify protected path"
        if path.startswith(protected + "/"):
            return "Cannot modify content under protected path"
        if op_type == "remove" and protected.startswith(path + "/"):
            return "Cannot remove path containing protected path"
    
    if op_type in ("add", "replace") and "value" not in op:
        return f"Missing 'value' field"
    
    if op_type == "replace" and not _path_exists(document, path):
        return "Replace: path does not exist"
    
    if op_type == "remove" and not _path_exists(document, path):
        return "Remove: path does not exist"
    
    if op_type == "add":
        if path:
            parent = _get_parent_path(path)
            if parent is None or not _path_exists(document, parent):
                return "Add: parent path does not exist"
            
            parent_value = _get_value_at_path(document, parent)
            if isinstance(parent_value, list):
                last_token = path.split("/")[-1]
                try:
                    index = int(last_token)
                    if not (0 <= index <= len(parent_value)):
                        return "Add: invalid array index"
                except ValueError:
                    return "Add: invalid array index"
    
    return None


def _has_invalid_escapes(path):
    i = 0
    while i < len(path):
        if path[i] == "~":
            if i + 1 >= len(path) or path[i + 1] not in ("0", "1"):
                return True
            i += 2
        else:
            i += 1
    return False


def _parse_pointer(path):
    if not path:
        return []
    parts = path[1:].split("/")
    tokens = []
    for part in parts:
        unescaped = part.replace("~1", "/").replace("~0", "~")
        tokens.append(unescaped)
    return tokens


def _get_value_at_path(document, path):
    if not path:
        return document
    
    tokens = _parse_pointer(path)
    current = document
    
    for token in tokens:
        if isinstance(current, dict):
            current = current[token]
        elif isinstance(current, list):
            try:
                index = int(token)
                current = current[index]
            except (ValueError, IndexError):
                raise KeyError(token)
        else:
            raise TypeError("Cannot traverse")
    
    return current


def _path_exists(document, path):
    try:
        _get_value_at_path(document, path)
        return True
    except Exception:
        return False


def _get_parent_path(path):
    if not path:
        return None
    
    last_slash = -1
    i = 0
    while i < len(path):
        if path[i] == "/":
            tilde_count = 0
            j = i - 1
            while j >= 0 and path[j] == "~":
                tilde_count += 1
                j -= 1
            if tilde_count % 2 == 0:
                last_slash = i
        i += 1
    
    if last_slash <= 0:
        return None
    return path[:last_slash]


def _apply_operation(document, op):
    import copy
    doc = copy.deepcopy(document)
    
    op_type = op["op"]
    path = op["path"]
    
    if not path:
        if op_type == "add" or op_type == "replace":
            return copy.deepcopy(op["value"])
        elif op_type == "remove":
            return None
    
    tokens = _parse_pointer(path)
    current = doc
    for token in tokens[:-1]:
        if isinstance(current, dict):
            current = current[token]
        elif isinstance(current, list):
            current = current[int(token)]
    
    last_token = tokens[-1]
    
    if op_type == "add":
        if isinstance(current, dict):
            current[last_token] = copy.deepcopy(op["value"])
        elif isinstance(current, list):
            current.insert(int(last_token), copy.deepcopy(op["value"]))
    elif op_type == "remove":
        if isinstance(current, dict):
            del current[last_token]
        elif isinstance(current, list):
            del current[int(last_token)]
    elif op_type == "replace":
        if isinstance(current, dict):
            current[last_token] = copy.deepcopy(op["value"])
        elif isinstance(current, list):
            current[int(last_token)] = copy.deepcopy(op["value"])
    
    return doc
