def validate_patch(document, operations, protected_paths) -> dict:
    import copy
    
    if not isinstance(operations, list):
        return {"valid": False, "errors": ["operations must be a list"]}
    
    if not isinstance(protected_paths, list):
        return {"valid": False, "errors": ["protected_paths must be a list"]}
    
    def parse_json_pointer(path):
        if not isinstance(path, str):
            raise ValueError("path must be a string")
        if path == "":
            return []
        if not path.startswith("/"):
            raise ValueError("JSON Pointer must start with /")
        parts = path[1:].split("/")
        return [part.replace("~1", "/").replace("~0", "~") for part in parts]
    
    def path_is_protected(parts):
        for protected_path in protected_paths:
            try:
                protected_parts = parse_json_pointer(protected_path)
                if len(parts) >= len(protected_parts) and parts[:len(protected_parts)] == protected_parts:
                    return True
            except:
                pass
        return False
    
    def removal_affects_protected(parts):
        for protected_path in protected_paths:
            try:
                protected_parts = parse_json_pointer(protected_path)
                if len(protected_parts) > len(parts) and protected_parts[:len(parts)] == parts:
                    return True
            except:
                pass
        return False
    
    def add_value(doc, parts, value):
        doc = copy.deepcopy(doc)
        if not parts:
            return {"success": True, "doc": value}
        
        parent = doc
        for part in parts[:-1]:
            if isinstance(parent, dict):
                if part not in parent:
                    return {"success": False, "error": "Parent path does not exist"}
                parent = parent[part]
            elif isinstance(parent, list):
                try:
                    index = int(part)
                    if index < 0 or index >= len(parent):
                        return {"success": False, "error": "Array index out of bounds"}
                    parent = parent[index]
                except ValueError:
                    return {"success": False, "error": "Invalid array index"}
            else:
                return {"success": False, "error": "Parent is not a dict or list"}
        
        last_part = parts[-1]
        if isinstance(parent, dict):
            parent[last_part] = value
            return {"success": True, "doc": doc}
        elif isinstance(parent, list):
            try:
                index = int(last_part)
                if index < 0 or index > len(parent):
                    return {"success": False, "error": "Array index out of bounds"}
                parent.insert(index, value)
                return {"success": True, "doc": doc}
            except ValueError:
                return {"success": False, "error": "Invalid array index"}
        else:
            return {"success": False, "error": "Parent is not a dict or list"}
    
    def remove_value(doc, parts):
        doc = copy.deepcopy(doc)
        if not parts:
            return {"success": False, "error": "Cannot remove root document"}
        
        parent = doc
        for part in parts[:-1]:
            if isinstance(parent, dict):
                if part not in parent:
                    return {"success": False, "error": "Parent path does not exist"}
                parent = parent[part]
            elif isinstance(parent, list):
                try:
                    index = int(part)
                    if index < 0 or index >= len(parent):
                        return {"success": False, "error": "Array index out of bounds"}
                    parent = parent[index]
                except ValueError:
                    return {"success": False, "error": "Invalid array index"}
            else:
                return {"success": False, "error": "Parent is not a dict or list"}
        
        last_part = parts[-1]
        if isinstance(parent, dict):
            if last_part not in parent:
                return {"success": False, "error": "Path does not exist"}
            del parent[last_part]
            return {"success": True, "doc": doc}
        elif isinstance(parent, list):
            try:
                index = int(last_part)
                if index < 0 or index >= len(parent):
                    return {"success": False, "error": "Array index out of bounds"}
                parent.pop(index)
                return {"success": True, "doc": doc}
            except ValueError:
                return {"success": False, "error": "Invalid array index"}
        else:
            return {"success": False, "error": "Parent is not a dict or list"}
    
    def replace_value(doc, parts, value):
        doc = copy.deepcopy(doc)
        if not parts:
            return {"success": True, "doc": value}
        
        parent = doc
        for part in parts[:-1]:
            if isinstance(parent, dict):
                if part not in parent:
                    return {"success": False, "error": "Parent path does not exist"}
                parent = parent[part]
            elif isinstance(parent, list):
                try:
                    index = int(part)
                    if index < 0 or index >= len(parent):
                        return {"success": False, "error": "Array index out of bounds"}
                    parent = parent[index]
                except ValueError:
                    return {"success": False, "error": "Invalid array index"}
            else:
                return {"success": False, "error": "Parent is not a dict or list"}
        
        last_part = parts[-1]
        if isinstance(parent, dict):
            if last_part not in parent:
                return {"success": False, "error": "Path does not exist"}
            parent[last_part] = value
            return {"success": True, "doc": doc}
        elif isinstance(parent, list):
            try:
                index = int(last_part)
                if index < 0 or index >= len(parent):
                    return {"success": False, "error": "Array index out of bounds"}
                parent[index] = value
                return {"success": True, "doc": doc}
            except ValueError:
                return {"success": False, "error": "Invalid array index"}
        else:
            return {"success": False, "error": "Parent is not a dict or list"}
    
    current_doc = copy.deepcopy(document)
    errors = []
    
    for i, op in enumerate(operations):
        try:
            if not isinstance(op, dict):
                errors.append(f"Operation {i} is not a dict")
                continue
            
            if "op" not in op:
                errors.append(f"Operation {i} missing 'op' field")
                continue
            
            operation = op["op"]
            if operation not in ("add", "remove", "replace"):
                errors.append(f"Operation {i} has invalid op '{operation}'")
                continue
            
            if "path" not in op:
                errors.append(f"Operation {i} missing 'path' field")
                continue
            
            path = op["path"]
            
            try:
                parts = parse_json_pointer(path)
            except Exception as e:
                errors.append(f"Operation {i} has invalid path: {str(e)}")
                continue
            
            if path_is_protected(parts):
                errors.append(f"Operation {i} targets protected path")
                continue
            
            if operation == "remove" and removal_affects_protected(parts):
                errors.append(f"Operation {i} would remove a protected path")
                continue
            
            if operation in ("add", "replace"):
                if "value" not in op:
                    errors.append(f"Operation {i} missing 'value' field")
                    continue
                value = op["value"]
            
            if operation == "add":
                result = add_value(current_doc, parts, value)
                if result["success"]:
                    current_doc = result["doc"]
                else:
                    errors.append(f"Operation {i}: {result['error']}")
            elif operation == "remove":
                result = remove_value(current_doc, parts)
                if result["success"]:
                    current_doc = result["doc"]
                else:
                    errors.append(f"Operation {i}: {result['error']}")
            elif operation == "replace":
                result = replace_value(current_doc, parts, value)
                if result["success"]:
                    current_doc = result["doc"]
                else:
                    errors.append(f"Operation {i}: {result['error']}")
        except Exception:
            errors.append(f"Operation {i}: unexpected error")
            continue
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
