import copy

def validate_patch(document, operations, protected_paths) -> dict:
    errors = []
    
    def parse_pointer(pointer):
        """Parse a JSON Pointer (RFC 6901) into path components."""
        if pointer == "":
            return []
        if not isinstance(pointer, str) or not pointer.startswith("/"):
            return None
        
        parts = pointer[1:].split("/")
        decoded_parts = []
        for part in parts:
            unescaped = []
            i = 0
            while i < len(part):
                if part[i] == "~":
                    if i + 1 >= len(part):
                        return None
                    if part[i + 1] == "0":
                        unescaped.append("~")
                        i += 2
                    elif part[i + 1] == "1":
                        unescaped.append("/")
                        i += 2
                    else:
                        return None
                else:
                    unescaped.append(part[i])
                    i += 1
            
            decoded_parts.append("".join(unescaped))
        
        return decoded_parts
    
    def get_value(doc, path):
        """Get value at path, returns (exists, value)"""
        current = doc
        for key in path:
            if isinstance(current, dict):
                if key not in current:
                    return False, None
                current = current[key]
            elif isinstance(current, list):
                try:
                    idx = int(key)
                    if idx < 0 or idx >= len(current):
                        return False, None
                    current = current[idx]
                except (ValueError, IndexError):
                    return False, None
            else:
                return False, None
        return True, current
    
    def path_exists(doc, path):
        """Check if path exists"""
        exists, _ = get_value(doc, path)
        return exists
    
    def is_protected(path, protected_paths):
        """Check if path is protected or contains protected paths"""
        path_str = "/" + "/".join(path) if path else ""
        
        for protected in protected_paths:
            if path_str == protected:
                return True
            if path_str.startswith(protected + "/"):
                return True
            if protected.startswith(path_str + "/"):
                return True
        
        return False
    
    def apply_operation(doc, op):
        """Apply a single operation and return new document"""
        doc = copy.deepcopy(doc)
        
        op_type = op["op"]
        path_str = op["path"]
        
        path = parse_pointer(path_str)
        if path is None:
            return None
        
        if op_type == "add":
            value = op.get("value")
            if not path:
                doc = value
            else:
                parent_path = path[:-1]
                key = path[-1]
                _, parent = get_value(doc, parent_path)
                if parent is None:
                    return None
                
                if isinstance(parent, dict):
                    parent[key] = value
                elif isinstance(parent, list):
                    if key == "-":
                        parent.append(value)
                    else:
                        try:
                            idx = int(key)
                            if idx < 0 or idx > len(parent):
                                return None
                            parent.insert(idx, value)
                        except ValueError:
                            return None
                else:
                    return None
        
        elif op_type == "remove":
            if not path:
                return None
            
            parent_path = path[:-1]
            key = path[-1]
            _, parent = get_value(doc, parent_path)
            if parent is None:
                return None
            
            if isinstance(parent, dict):
                if key not in parent:
                    return None
                del parent[key]
            elif isinstance(parent, list):
                try:
                    idx = int(key)
                    if idx < 0 or idx >= len(parent):
                        return None
                    del parent[idx]
                except ValueError:
                    return None
            else:
                return None
        
        elif op_type == "replace":
            value = op.get("value")
            if not path:
                doc = value
            else:
                parent_path = path[:-1]
                key = path[-1]
                _, parent = get_value(doc, parent_path)
                if parent is None:
                    return None
                
                if isinstance(parent, dict):
                    if key not in parent:
                        return None
                    parent[key] = value
                elif isinstance(parent, list):
                    try:
                        idx = int(key)
                        if idx < 0 or idx >= len(parent):
                            return None
                        parent[idx] = value
                    except ValueError:
                        return None
                else:
                    return None
        
        return doc
    
    try:
        current_doc = copy.deepcopy(document)
        
        for i, op in enumerate(operations):
            if not isinstance(op, dict):
                return {"valid": False, "errors": [f"Operation {i}: not a dict"]}
            
            if "op" not in op:
                return {"valid": False, "errors": [f"Operation {i}: missing 'op' field"]}
            
            if "path" not in op:
                return {"valid": False, "errors": [f"Operation {i}: missing 'path' field"]}
            
            op_type = op["op"]
            path_str = op["path"]
            
            if op_type not in ["add", "remove", "replace"]:
                return {"valid": False, "errors": [f"Operation {i}: unsupported operation '{op_type}'"]}
            
            if not isinstance(path_str, str):
                return {"valid": False, "errors": [f"Operation {i}: path must be a string"]}
            
            path = parse_pointer(path_str)
            if path is None:
                return {"valid": False, "errors": [f"Operation {i}: invalid path"]}
            
            if is_protected(path, protected_paths):
                return {"valid": False, "errors": [f"Operation {i}: path is protected"]}
            
            if op_type == "add":
                if "value" not in op:
                    return {"valid": False, "errors": [f"Operation {i}: missing 'value' field"]}
                
                if not path:
                    return {"valid": False, "errors": [f"Operation {i}: cannot add to root"]}
                
                parent_path = path[:-1]
                if not path_exists(current_doc, parent_path):
                    return {"valid": False, "errors": [f"Operation {i}: parent path does not exist"]}
                
                _, parent = get_value(current_doc, parent_path)
                if isinstance(parent, list):
                    key = path[-1]
                    if key != "-":
                        try:
                            idx = int(key)
                            if idx < 0 or idx > len(parent):
                                return {"valid": False, "errors": [f"Operation {i}: array index out of bounds"]}
                        except ValueError:
                            return {"valid": False, "errors": [f"Operation {i}: invalid array index"]}
            
            elif op_type == "remove":
                if not path_exists(current_doc, path):
                    return {"valid": False, "errors": [f"Operation {i}: path does not exist"]}
            
            elif op_type == "replace":
                if "value" not in op:
                    return {"valid": False, "errors": [f"Operation {i}: missing 'value' field"]}
                
                if not path_exists(current_doc, path):
                    return {"valid": False, "errors": [f"Operation {i}: path does not exist"]}
            
            new_doc = apply_operation(current_doc, op)
            if new_doc is None:
                return {"valid": False, "errors": [f"Operation {i}: failed to apply operation"]}
            
            current_doc = new_doc
        
        return {"valid": True, "errors": []}
    
    except Exception as e:
        return {"valid": False, "errors": [str(e)]}
