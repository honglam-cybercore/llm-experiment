def validate_patch(document, operations, protected_paths) -> dict:
    try:
        def parse_pointer(pointer):
            if pointer == "":
                return []
            if not pointer.startswith("/"):
                return None
            
            for i, char in enumerate(pointer):
                if char == "~" and (i + 1 >= len(pointer) or pointer[i + 1] not in "01"):
                    return None
            
            tokens = pointer[1:].split("/")
            unescaped = []
            for token in tokens:
                token = token.replace("~1", "/").replace("~0", "~")
                unescaped.append(token)
            return unescaped
        
        def deep_copy(obj):
            if isinstance(obj, dict):
                return {k: deep_copy(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [deep_copy(v) for v in obj]
            else:
                return obj
        
        def get_value(doc, tokens):
            current = doc
            for token in tokens:
                if isinstance(current, dict):
                    if token in current:
                        current = current[token]
                    else:
                        return (False, None)
                elif isinstance(current, list):
                    try:
                        index = int(token)
                        if 0 <= index < len(current):
                            current = current[index]
                        else:
                            return (False, None)
                    except ValueError:
                        return (False, None)
                else:
                    return (False, None)
            return (True, current)
        
        def get_parent(doc, tokens):
            if not tokens:
                return None
            current = doc
            for token in tokens[:-1]:
                if isinstance(current, dict):
                    if token in current:
                        current = current[token]
                    else:
                        return None
                elif isinstance(current, list):
                    try:
                        index = int(token)
                        if 0 <= index < len(current):
                            current = current[index]
                        else:
                            return None
                    except ValueError:
                        return None
                else:
                    return None
            if not isinstance(current, (dict, list)):
                return None
            return (current, tokens[-1])
        
        def is_path_protected(path, protected_paths):
            path_tokens = parse_pointer(path)
            if path_tokens is None:
                return True
            
            for protected in protected_paths:
                protected_tokens = parse_pointer(protected)
                if protected_tokens is None:
                    continue
                
                if len(protected_tokens) >= len(path_tokens):
                    if protected_tokens[:len(path_tokens)] == path_tokens:
                        return True
                else:
                    if path_tokens[:len(protected_tokens)] == protected_tokens:
                        return True
            
            return False
        
        if not isinstance(operations, list):
            return {"valid": False, "errors": ["Operations must be a list"]}
        
        if not isinstance(protected_paths, list):
            return {"valid": False, "errors": ["Protected paths must be a list"]}
        
        current_doc = deep_copy(document)
        
        for i, op in enumerate(operations):
            if not isinstance(op, dict):
                return {"valid": False, "errors": [f"Operation {i} is not a dict"]}
            
            if "op" not in op:
                return {"valid": False, "errors": [f"Operation {i} missing 'op' field"]}
            
            op_type = op.get("op")
            if op_type not in ["add", "remove", "replace"]:
                return {"valid": False, "errors": [f"Operation {i} has unsupported op '{op_type}'"]}
            
            if "path" not in op:
                return {"valid": False, "errors": [f"Operation {i} missing 'path' field"]}
            
            path = op.get("path")
            if not isinstance(path, str):
                return {"valid": False, "errors": [f"Operation {i} path is not a string"]}
            
            tokens = parse_pointer(path)
            if tokens is None:
                return {"valid": False, "errors": [f"Operation {i} has invalid path format"]}
            
            if is_path_protected(path, protected_paths):
                return {"valid": False, "errors": [f"Operation {i} targets protected path '{path}'"]}
            
            if op_type == "add":
                if "value" not in op:
                    return {"valid": False, "errors": [f"Operation {i} (add) missing 'value' field"]}
                
                value = op.get("value")
                
                if not tokens:
                    current_doc = deep_copy(value)
                else:
                    parent_info = get_parent(current_doc, tokens)
                    if parent_info is None:
                        return {"valid": False, "errors": [f"Operation {i} (add) parent does not exist"]}
                    
                    parent, key = parent_info
                    
                    if isinstance(parent, dict):
                        parent[key] = deep_copy(value)
                    elif isinstance(parent, list):
                        if key == "-":
                            parent.append(deep_copy(value))
                        else:
                            try:
                                index = int(key)
                                if index < 0 or index > len(parent):
                                    return {"valid": False, "errors": [f"Operation {i} (add) array index out of bounds"]}
                                parent.insert(index, deep_copy(value))
                            except ValueError:
                                return {"valid": False, "errors": [f"Operation {i} (add) invalid array index"]}
            
            elif op_type == "remove":
                exists, _ = get_value(current_doc, tokens)
                if not exists:
                    return {"valid": False, "errors": [f"Operation {i} (remove) path does not exist"]}
                
                if not tokens:
                    return {"valid": False, "errors": [f"Operation {i} (remove) cannot remove root"]}
                
                parent_info = get_parent(current_doc, tokens)
                parent, key = parent_info
                
                if isinstance(parent, dict):
                    del parent[key]
                elif isinstance(parent, list):
                    try:
                        index = int(key)
                        del parent[index]
                    except ValueError:
                        return {"valid": False, "errors": [f"Operation {i} (remove) invalid array index"]}
            
            elif op_type == "replace":
                if "value" not in op:
                    return {"valid": False, "errors": [f"Operation {i} (replace) missing 'value' field"]}
                
                exists, _ = get_value(current_doc, tokens)
                if not exists:
                    return {"valid": False, "errors": [f"Operation {i} (replace) path does not exist"]}
                
                value = op.get("value")
                
                if not tokens:
                    current_doc = deep_copy(value)
                else:
                    parent_info = get_parent(current_doc, tokens)
                    parent, key = parent_info
                    
                    if isinstance(parent, dict):
                        parent[key] = deep_copy(value)
                    elif isinstance(parent, list):
                        try:
                            index = int(key)
                            parent[index] = deep_copy(value)
                        except ValueError:
                            return {"valid": False, "errors": [f"Operation {i} (replace) invalid array index"]}
        
        return {"valid": True, "errors": []}
    
    except Exception:
        return {"valid": False, "errors": ["An unexpected error occurred"]}
