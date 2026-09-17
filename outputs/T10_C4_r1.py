import copy

def validate_patch(document, operations, protected_paths) -> dict:
    errors = []
    
    if not isinstance(operations, list):
        return {"valid": False, "errors": ["operations must be a list"]}
    
    if not isinstance(protected_paths, list):
        return {"valid": False, "errors": ["protected_paths must be a list"]}
    
    working_doc = copy.deepcopy(document)
    
    def parse_pointer(pointer):
        if not isinstance(pointer, str):
            return None
        
        if pointer == "":
            return []
        
        if not pointer.startswith("/"):
            return None
        
        parts = pointer[1:].split("/")
        result = []
        for part in parts:
            part = part.replace("~1", "/")
            part = part.replace("~0", "~")
            result.append(part)
        
        return result
    
    protected_paths_parts = []
    for p in protected_paths:
        parsed = parse_pointer(p)
        if parsed is not None:
            protected_paths_parts.append(parsed)
    
    def is_path_protected(path_parts):
        for protected in protected_paths_parts:
            if path_parts == protected:
                return True
            if len(path_parts) > len(protected) and path_parts[:len(protected)] == protected:
                return True
            if len(protected) > len(path_parts) and protected[:len(path_parts)] == path_parts:
                return True
        return False
    
    def get_value(doc, path_parts):
        current = doc
        for part in path_parts:
            if isinstance(current, dict):
                if part not in current:
                    return None, False
                current = current[part]
            elif isinstance(current, list):
                try:
                    index = int(part)
                    if index < 0 or index >= len(current):
                        return None, False
                    current = current[index]
                except ValueError:
                    return None, False
            else:
                return None, False
        return current, True
    
    def set_value(doc, path_parts, value):
        if not path_parts:
            return False
        
        current = doc
        for part in path_parts[:-1]:
            if isinstance(current, dict):
                if part not in current:
                    return False
                current = current[part]
            elif isinstance(current, list):
                try:
                    index = int(part)
                    if index < 0 or index >= len(current):
                        return False
                    current = current[index]
                except ValueError:
                    return False
            else:
                return False
        
        last_part = path_parts[-1]
        if isinstance(current, dict):
            current[last_part] = value
            return True
        elif isinstance(current, list):
            if last_part == "-":
                current.append(value)
                return True
            try:
                index = int(last_part)
                if index < 0:
                    return False
                if index == len(current):
                    current.append(value)
                    return True
                elif index < len(current):
                    current[index] = value
                    return True
                else:
                    return False
            except ValueError:
                return False
        else:
            return False
    
    def remove_value(doc, path_parts):
        if not path_parts:
            return False
        
        current = doc
        for part in path_parts[:-1]:
            if isinstance(current, dict):
                if part not in current:
                    return False
                current = current[part]
            elif isinstance(current, list):
                try:
                    index = int(part)
                    if index < 0 or index >= len(current):
                        return False
                    current = current[index]
                except ValueError:
                    return False
            else:
                return False
        
        last_part = path_parts[-1]
        if isinstance(current, dict):
            if last_part in current:
                del current[last_part]
                return True
            return False
        elif isinstance(current, list):
            try:
                index = int(last_part)
                if 0 <= index < len(current):
                    del current[index]
                    return True
            except ValueError:
                pass
        
        return False
    
    for i, op in enumerate(operations):
        try:
            if not isinstance(op, dict):
                errors.append(f"Operation {i}: must be a dict")
                return {"valid": False, "errors": errors}
            
            if "op" not in op:
                errors.append(f"Operation {i}: missing 'op' field")
                return {"valid": False, "errors": errors}
            
            op_type = op["op"]
            if op_type not in ["add", "remove", "replace"]:
                errors.append(f"Operation {i}: unsupported operation '{op_type}'")
                return {"valid": False, "errors": errors}
            
            if "path" not in op:
                errors.append(f"Operation {i}: missing 'path' field")
                return {"valid": False, "errors": errors}
            
            path_str = op["path"]
            path_parts = parse_pointer(path_str)
            
            if path_parts is None:
                errors.append(f"Operation {i}: invalid path format")
                return {"valid": False, "errors": errors}
            
            if is_path_protected(path_parts):
                errors.append(f"Operation {i}: path is protected")
                return {"valid": False, "errors": errors}
            
            if op_type == "add":
                if "value" not in op:
                    errors.append(f"Operation {i}: 'add' operation missing 'value' field")
                    return {"valid": False, "errors": errors}
                
                if path_parts:
                    parent_path = path_parts[:-1]
                    parent_val, exists = get_value(working_doc, parent_path)
                    
                    if not exists:
                        errors.append(f"Operation {i}: parent path does not exist")
                        return {"valid": False, "errors": errors}
                    
                    if not isinstance(parent_val, (dict, list)):
                        errors.append(f"Operation {i}: parent is not a dict or list")
                        return {"valid": False, "errors": errors}
                    
                    if isinstance(parent_val, list):
                        last_part = path_parts[-1]
                        if last_part != "-":
                            try:
                                index = int(last_part)
                                if index < 0 or index > len(parent_val):
                                    errors.append(f"Operation {i}: invalid array index")
                                    return {"valid": False, "errors": errors}
                            except ValueError:
                                errors.append(f"Operation {i}: invalid array index")
                                return {"valid": False, "errors": errors}
                else:
                    errors.append(f"Operation {i}: cannot add at root")
                    return {"valid": False, "errors": errors}
                
                value = copy.deepcopy(op["value"])
                if not set_value(working_doc, path_parts, value):
                    errors.append(f"Operation {i}: failed to set value")
                    return {"valid": False, "errors": errors}
            
            elif op_type == "remove":
                _, exists = get_value(working_doc, path_parts)
                if not exists:
                    errors.append(f"Operation {i}: path does not exist")
                    return {"valid": False, "errors": errors}
                
                if not remove_value(working_doc, path_parts):
                    errors.append(f"Operation {i}: failed to remove value")
                    return {"valid": False, "errors": errors}
            
            elif op_type == "replace":
                if "value" not in op:
                    errors.append(f"Operation {i}: 'replace' operation missing 'value' field")
                    return {"valid": False, "errors": errors}
                
                _, exists = get_value(working_doc, path_parts)
                if not exists:
                    errors.append(f"Operation {i}: path does not exist")
                    return {"valid": False, "errors": errors}
                
                new_value = copy.deepcopy(op["value"])
                if not set_value(working_doc, path_parts, new_value):
                    errors.append(f"Operation {i}: failed to replace value")
                    return {"valid": False, "errors": errors}
        
        except Exception:
            errors.append(f"Operation {i}: validation failed")
            return {"valid": False, "errors": errors}
    
    return {"valid": True, "errors": []}
