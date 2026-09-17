import copy

def validate_patch(document, operations, protected_paths) -> dict:
    try:
        if not isinstance(operations, list):
            return {"valid": False, "errors": ["Operations must be a list"]}
        
        if not isinstance(protected_paths, list):
            return {"valid": False, "errors": ["Protected paths must be a list"]}
        
        current_doc = copy.deepcopy(document)
        
        def unescape_pointer(token):
            return token.replace("~1", "/").replace("~0", "~")
        
        def parse_pointer(path):
            if not isinstance(path, str):
                return None
            if path == "":
                return []
            if not path.startswith("/"):
                return None
            tokens = path[1:].split("/")
            return [unescape_pointer(token) for token in tokens]
        
        def get_value(doc, tokens):
            current = doc
            for token in tokens:
                if isinstance(current, dict):
                    if token not in current:
                        return None, False
                    current = current[token]
                elif isinstance(current, list):
                    try:
                        index = int(token)
                        if index < 0 or index >= len(current):
                            return None, False
                        current = current[index]
                    except (ValueError, TypeError):
                        return None, False
                else:
                    return None, False
            return current, True
        
        def can_add_to_path(doc, tokens):
            if not tokens:
                return True
            
            parent_tokens = tokens[:-1]
            parent_val, parent_exists = get_value(doc, parent_tokens)
            if not parent_exists:
                return False
            
            if not isinstance(parent_val, (dict, list)):
                return False
            
            last_token = tokens[-1]
            if isinstance(parent_val, list):
                if last_token == "-":
                    return True
                try:
                    index = int(last_token)
                    return 0 <= index <= len(parent_val)
                except (ValueError, TypeError):
                    return False
            
            return isinstance(last_token, str)
        
        def apply_add(doc, tokens, value):
            if not tokens:
                return value
            
            new_doc = copy.deepcopy(doc)
            current = new_doc
            
            for token in tokens[:-1]:
                if isinstance(current, dict):
                    if token not in current:
                        return None
                    current = current[token]
                elif isinstance(current, list):
                    try:
                        index = int(token)
                        if index < 0 or index >= len(current):
                            return None
                        current = current[index]
                    except (ValueError, TypeError):
                        return None
                else:
                    return None
            
            last_token = tokens[-1]
            if isinstance(current, dict):
                current[last_token] = value
            elif isinstance(current, list):
                if last_token == "-":
                    current.append(value)
                else:
                    try:
                        index = int(last_token)
                        if index < 0 or index > len(current):
                            return None
                        current.insert(index, value)
                    except (ValueError, TypeError):
                        return None
            else:
                return None
            
            return new_doc
        
        def apply_remove(doc, tokens):
            if not tokens:
                return None
            
            new_doc = copy.deepcopy(doc)
            current = new_doc
            
            for token in tokens[:-1]:
                if isinstance(current, dict):
                    if token not in current:
                        return None
                    current = current[token]
                elif isinstance(current, list):
                    try:
                        index = int(token)
                        if index < 0 or index >= len(current):
                            return None
                        current = current[index]
                    except (ValueError, TypeError):
                        return None
                else:
                    return None
            
            last_token = tokens[-1]
            if isinstance(current, dict):
                if last_token not in current:
                    return None
                del current[last_token]
            elif isinstance(current, list):
                try:
                    index = int(last_token)
                    if index < 0 or index >= len(current):
                        return None
                    current.pop(index)
                except (ValueError, TypeError):
                    return None
            else:
                return None
            
            return new_doc
        
        def is_protected(path_tokens, protected_tokens_list):
            for protected_tokens in protected_tokens_list:
                if len(path_tokens) >= len(protected_tokens):
                    if path_tokens[:len(protected_tokens)] == protected_tokens:
                        return True
                if len(protected_tokens) > len(path_tokens):
                    if protected_tokens[:len(path_tokens)] == path_tokens:
                        return True
            return False
        
        protected_tokens_list = []
        for ppath in protected_paths:
            tokens = parse_pointer(ppath)
            if tokens is None:
                return {"valid": False, "errors": [f"Invalid protected path: {ppath}"]}
            protected_tokens_list.append(tokens)
        
        for i, op in enumerate(operations):
            if not isinstance(op, dict):
                return {"valid": False, "errors": [f"Operation {i} is not a dict"]}
            
            if "op" not in op:
                return {"valid": False, "errors": [f"Operation {i} missing 'op' field"]}
            
            if "path" not in op:
                return {"valid": False, "errors": [f"Operation {i} missing 'path' field"]}
            
            op_type = op["op"]
            op_path = op["path"]
            
            if op_type not in ("add", "remove", "replace"):
                return {"valid": False, "errors": [f"Operation {i} has invalid op: {op_type}"]}
            
            tokens = parse_pointer(op_path)
            if tokens is None:
                return {"valid": False, "errors": [f"Operation {i} has invalid path: {op_path}"]}
            
            if is_protected(tokens, protected_tokens_list):
                return {"valid": False, "errors": [f"Operation {i} targets protected path: {op_path}"]}
            
            if op_type == "add":
                if "value" not in op:
                    return {"valid": False, "errors": [f"Operation {i} (add) missing 'value' field"]}
                
                if not can_add_to_path(current_doc, tokens):
                    return {"valid": False, "errors": [f"Operation {i} (add) cannot be applied to path: {op_path}"]}
                
                new_doc = apply_add(current_doc, tokens, op["value"])
                if new_doc is None:
                    return {"valid": False, "errors": [f"Operation {i} (add) failed to apply to path: {op_path}"]}
                current_doc = new_doc
            
            elif op_type == "remove":
                val, exists = get_value(current_doc, tokens)
                if not exists:
                    return {"valid": False, "errors": [f"Operation {i} (remove) path does not exist: {op_path}"]}
                
                new_doc = apply_remove(current_doc, tokens)
                if new_doc is None:
                    return {"valid": False, "errors": [f"Operation {i} (remove) failed to apply to path: {op_path}"]}
                current_doc = new_doc
            
            elif op_type == "replace":
                if "value" not in op:
                    return {"valid": False, "errors": [f"Operation {i} (replace) missing 'value' field"]}
                
                val, exists = get_value(current_doc, tokens)
                if not exists:
                    return {"valid": False, "errors": [f"Operation {i} (replace) path does not exist: {op_path}"]}
                
                new_doc = apply_add(current_doc, tokens, op["value"])
                if new_doc is None:
                    return {"valid": False, "errors": [f"Operation {i} (replace) failed to apply to path: {op_path}"]}
                current_doc = new_doc
        
        return {"valid": True, "errors": []}
    
    except Exception:
        return {"valid": False, "errors": ["Validation failed"]}
