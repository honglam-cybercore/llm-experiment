import copy

def validate_patch(document, operations, protected_paths) -> dict:
    if not isinstance(operations, list):
        return {"valid": False, "errors": ["operations must be a list"]}
    if not isinstance(protected_paths, list):
        return {"valid": False, "errors": ["protected_paths must be a list"]}
    
    def unescape_token(token):
        return token.replace("~1", "/").replace("~0", "~")
    
    def parse_path(path):
        if path == "":
            return []
        if not isinstance(path, str) or not path.startswith("/"):
            return None
        parts = path[1:].split("/")
        return [unescape_token(part) for part in parts]
    
    def is_protected(path_str, protected_paths):
        for protected in protected_paths:
            if path_str == protected or path_str.startswith(protected + "/") or protected.startswith(path_str + "/"):
                return True
        return False
    
    def get_parent_for_modification(doc, path_parts):
        if not path_parts:
            return doc, None
        current = doc
        for part in path_parts[:-1]:
            if isinstance(current, dict):
                if part not in current:
                    return None, None
                current = current[part]
            elif isinstance(current, list):
                if part == "-":
                    return None, None
                try:
                    index = int(part)
                    if index < 0 or index >= len(current):
                        return None, None
                    current = current[index]
                except (ValueError, TypeError):
                    return None, None
            else:
                return None, None
        return current, path_parts[-1]
    
    current_doc = copy.deepcopy(document)
    
    for i, op in enumerate(operations):
        try:
            if not isinstance(op, dict):
                return {"valid": False, "errors": [f"Operation {i} is not a dict"]}
            
            op_type = op.get("op")
            path_str = op.get("path")
            
            if op_type not in ["add", "remove", "replace"]:
                return {"valid": False, "errors": [f"Operation {i}: invalid op '{op_type}'"]}
            
            if not isinstance(path_str, str):
                return {"valid": False, "errors": [f"Operation {i}: path is not a string"]}
            
            path_parts = parse_path(path_str)
            if path_parts is None:
                return {"valid": False, "errors": [f"Operation {i}: invalid path format"]}
            
            if is_protected(path_str, protected_paths):
                return {"valid": False, "errors": [f"Operation {i}: path is protected"]}
            
            if op_type == "add":
                if "value" not in op:
                    return {"valid": False, "errors": [f"Operation {i}: 'add' requires 'value'"]}
                
                if not path_parts:
                    current_doc = copy.deepcopy(op["value"])
                else:
                    parent, key = get_parent_for_modification(current_doc, path_parts)
                    if parent is None:
                        return {"valid": False, "errors": [f"Operation {i}: parent path does not exist"]}
                    
                    if isinstance(parent, dict):
                        parent[key] = copy.deepcopy(op["value"])
                    elif isinstance(parent, list):
                        try:
                            if key == "-":
                                parent.append(copy.deepcopy(op["value"]))
                            else:
                                index = int(key)
                                if index < 0 or index > len(parent):
                                    return {"valid": False, "errors": [f"Operation {i}: array index out of bounds"]}
                                parent.insert(index, copy.deepcopy(op["value"]))
                        except (ValueError, TypeError):
                            return {"valid": False, "errors": [f"Operation {i}: invalid array index"]}
                    else:
                        return {"valid": False, "errors": [f"Operation {i}: parent is not a container"]}
            
            elif op_type == "remove":
                if not path_parts:
                    return {"valid": False, "errors": [f"Operation {i}: cannot remove root"]}
                
                parent, key = get_parent_for_modification(current_doc, path_parts)
                if parent is None:
                    return {"valid": False, "errors": [f"Operation {i}: parent path does not exist"]}
                
                if isinstance(parent, dict):
                    if key not in parent:
                        return {"valid": False, "errors": [f"Operation {i}: path does not exist"]}
                    del parent[key]
                elif isinstance(parent, list):
                    try:
                        if key == "-":
                            return {"valid": False, "errors": [f"Operation {i}: invalid array index"]}
                        index = int(key)
                        if index < 0 or index >= len(parent):
                            return {"valid": False, "errors": [f"Operation {i}: array index out of bounds"]}
                        del parent[index]
                    except (ValueError, TypeError):
                        return {"valid": False, "errors": [f"Operation {i}: invalid array index"]}
                else:
                    return {"valid": False, "errors": [f"Operation {i}: parent is not a container"]}
            
            elif op_type == "replace":
                if "value" not in op:
                    return {"valid": False, "errors": [f"Operation {i}: 'replace' requires 'value'"]}
                
                if not path_parts:
                    current_doc = copy.deepcopy(op["value"])
                else:
                    parent, key = get_parent_for_modification(current_doc, path_parts)
                    if parent is None:
                        return {"valid": False, "errors": [f"Operation {i}: parent path does not exist"]}
                    
                    if isinstance(parent, dict):
                        if key not in parent:
                            return {"valid": False, "errors": [f"Operation {i}: path does not exist"]}
                        parent[key] = copy.deepcopy(op["value"])
                    elif isinstance(parent, list):
                        try:
                            if key == "-":
                                return {"valid": False, "errors": [f"Operation {i}: invalid array index"]}
                            index = int(key)
                            if index < 0 or index >= len(parent):
                                return {"valid": False, "errors": [f"Operation {i}: array index out of bounds"]}
                            parent[index] = copy.deepcopy(op["value"])
                        except (ValueError, TypeError):
                            return {"valid": False, "errors": [f"Operation {i}: invalid array index"]}
                    else:
                        return {"valid": False, "errors": [f"Operation {i}: parent is not a container"]}
        
        except Exception:
            return {"valid": False, "errors": [f"Operation {i}: unexpected error"]}
    
    return {"valid": True, "errors": []}
