def validate_patch(document, operations, protected_paths) -> dict:
    import copy
    
    def unescape_json_pointer(s):
        result = []
        i = 0
        while i < len(s):
            if s[i] == '~' and i + 1 < len(s):
                if s[i + 1] == '0':
                    result.append('~')
                    i += 2
                elif s[i + 1] == '1':
                    result.append('/')
                    i += 2
                else:
                    result.append(s[i])
                    i += 1
            else:
                result.append(s[i])
                i += 1
        return ''.join(result)
    
    def escape_json_pointer(s):
        return s.replace("~", "~0").replace("/", "~1")
    
    def parse_pointer(path):
        if not isinstance(path, str):
            return None
        if path == "":
            return []
        if not path.startswith("/"):
            return None
        
        parts = path[1:].split("/")
        result = []
        for part in parts:
            result.append(unescape_json_pointer(part))
        return result
    
    def get_value(doc, path_parts):
        current = doc
        for part in path_parts:
            if isinstance(current, dict):
                if part not in current:
                    return None, False
                current = current[part]
            elif isinstance(current, list):
                try:
                    idx = int(part)
                    if idx < 0 or idx >= len(current):
                        return None, False
                    current = current[idx]
                except (ValueError, TypeError):
                    return None, False
            else:
                return None, False
        return current, True
    
    def set_value(doc, path_parts, value):
        if not path_parts:
            return value
        
        doc = copy.deepcopy(doc)
        current = doc
        
        for part in path_parts[:-1]:
            if isinstance(current, dict):
                if part not in current:
                    return None
                current = current[part]
            elif isinstance(current, list):
                try:
                    idx = int(part)
                    if idx < 0 or idx >= len(current):
                        return None
                    current = current[idx]
                except (ValueError, TypeError):
                    return None
            else:
                return None
        
        last_part = path_parts[-1]
        if isinstance(current, dict):
            current[last_part] = value
        elif isinstance(current, list):
            try:
                idx = int(last_part)
                if idx < 0 or idx > len(current):
                    return None
                if idx == len(current):
                    current.append(value)
                else:
                    current[idx] = value
            except (ValueError, TypeError):
                return None
        else:
            return None
        return doc
    
    def remove_value(doc, path_parts):
        if not path_parts:
            return None
        
        doc = copy.deepcopy(doc)
        current = doc
        
        for part in path_parts[:-1]:
            if isinstance(current, dict):
                if part not in current:
                    return None
                current = current[part]
            elif isinstance(current, list):
                try:
                    idx = int(part)
                    if idx < 0 or idx >= len(current):
                        return None
                    current = current[idx]
                except (ValueError, TypeError):
                    return None
            else:
                return None
        
        last_part = path_parts[-1]
        if isinstance(current, dict):
            if last_part not in current:
                return None
            del current[last_part]
        elif isinstance(current, list):
            try:
                idx = int(last_part)
                if idx < 0 or idx >= len(current):
                    return None
                current.pop(idx)
            except (ValueError, TypeError):
                return None
        else:
            return None
        return doc
    
    def get_path_str(path_parts):
        if path_parts:
            escaped = [escape_json_pointer(p) for p in path_parts]
            return "/" + "/".join(escaped)
        return ""
    
    def is_protected(path_parts):
        path_str = get_path_str(path_parts)
        
        for protected in protected_paths:
            if not isinstance(protected, str):
                continue
            
            if path_str == protected:
                return True
            if protected and path_str.startswith(protected + "/"):
                return True
            if protected.startswith(path_str + "/"):
                return True
        
        return False
    
    if not isinstance(operations, list):
        return {"valid": False, "errors": ["operations must be a list"]}
    
    if not isinstance(protected_paths, list):
        return {"valid": False, "errors": ["protected_paths must be a list"]}
    
    current_doc = document
    
    for i, op in enumerate(operations):
        if not isinstance(op, dict):
            return {"valid": False, "errors": [f"Operation {i}: invalid format"]}
        
        if "op" not in op or "path" not in op:
            return {"valid": False, "errors": [f"Operation {i}: missing required fields"]}
        
        operation = op.get("op")
        path = op.get("path")
        
        if operation not in ["add", "remove", "replace"]:
            return {"valid": False, "errors": [f"Operation {i}: invalid operation"]}
        
        if not isinstance(path, str):
            return {"valid": False, "errors": [f"Operation {i}: invalid path format"]}
        
        path_parts = parse_pointer(path)
        if path_parts is None:
            return {"valid": False, "errors": [f"Operation {i}: invalid JSON Pointer"]}
        
        if is_protected(path_parts):
            return {"valid": False, "errors": [f"Operation {i}: path is protected"]}
        
        if operation == "add":
            if "value" not in op:
                return {"valid": False, "errors": [f"Operation {i}: missing value"]}
            if not path_parts:
                return {"valid": False, "errors": [f"Operation {i}: cannot add at root"]}
            
            parent_parts = path_parts[:-1]
            parent, exists = get_value(current_doc, parent_parts)
            if not exists:
                return {"valid": False, "errors": [f"Operation {i}: parent path not found"]}
            
            if isinstance(parent, list):
                try:
                    idx = int(path_parts[-1])
                    if idx < 0 or idx > len(parent):
                        return {"valid": False, "errors": [f"Operation {i}: invalid array index"]}
                except (ValueError, TypeError):
                    return {"valid": False, "errors": [f"Operation {i}: invalid array index"]}
            elif not isinstance(parent, dict):
                return {"valid": False, "errors": [f"Operation {i}: cannot add to non-container"]}
            
            new_doc = set_value(current_doc, path_parts, op.get("value"))
            if new_doc is None:
                return {"valid": False, "errors": [f"Operation {i}: add operation failed"]}
            current_doc = new_doc
        
        elif operation == "remove":
            if not path_parts:
                return {"valid": False, "errors": [f"Operation {i}: cannot remove root"]}
            
            _, exists = get_value(current_doc, path_parts)
            if not exists:
                return {"valid": False, "errors": [f"Operation {i}: path not found"]}
            
            new_doc = remove_value(current_doc, path_parts)
            if new_doc is None:
                return {"valid": False, "errors": [f"Operation {i}: remove operation failed"]}
            current_doc = new_doc
        
        elif operation == "replace":
            if "value" not in op:
                return {"valid": False, "errors": [f"Operation {i}: missing value"]}
            
            _, exists = get_value(current_doc, path_parts)
            if not exists:
                return {"valid": False, "errors": [f"Operation {i}: path not found"]}
            
            new_doc = set_value(current_doc, path_parts, op.get("value"))
            if new_doc is None:
                return {"valid": False, "errors": [f"Operation {i}: replace operation failed"]}
            current_doc = new_doc
    
    return {"valid": True, "errors": []}
