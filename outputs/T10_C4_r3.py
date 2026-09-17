def validate_patch(document, operations, protected_paths) -> dict:
    import copy
    
    def unescape_pointer(token):
        """Unescape a JSON Pointer token."""
        return token.replace('~1', '/').replace('~0', '~')
    
    def parse_pointer(path):
        """Parse a JSON Pointer into tokens."""
        try:
            if not isinstance(path, str):
                return None
            if path == '':
                return []
            if not path.startswith('/'):
                return None
            tokens = path[1:].split('/')
            return [unescape_pointer(t) for t in tokens]
        except:
            return None
    
    def get_value(doc, tokens):
        """Get value at path. Returns (exists, value)."""
        try:
            current = doc
            for token in tokens:
                if isinstance(current, dict):
                    if token not in current:
                        return False, None
                    current = current[token]
                elif isinstance(current, list):
                    idx = int(token)
                    if idx < 0 or idx >= len(current):
                        return False, None
                    current = current[idx]
                else:
                    return False, None
            return True, current
        except:
            return False, None
    
    def apply_add(doc, tokens, value):
        """Apply add operation. Returns new doc or None."""
        try:
            result = copy.deepcopy(doc)
            
            if not tokens:
                return value
            
            current = result
            for token in tokens[:-1]:
                if isinstance(current, dict):
                    if token not in current:
                        return None
                    current = current[token]
                elif isinstance(current, list):
                    idx = int(token)
                    if idx < 0 or idx >= len(current):
                        return None
                    current = current[idx]
                else:
                    return None
            
            last_token = tokens[-1]
            if isinstance(current, dict):
                current[last_token] = value
            elif isinstance(current, list):
                idx = int(last_token)
                if idx < 0 or idx > len(current):
                    return None
                if idx == len(current):
                    current.append(value)
                else:
                    current[idx] = value
            else:
                return None
            
            return result
        except:
            return None
    
    def apply_remove(doc, tokens):
        """Apply remove operation. Returns new doc or None."""
        try:
            result = copy.deepcopy(doc)
            
            if not tokens:
                return None
            
            current = result
            for token in tokens[:-1]:
                if isinstance(current, dict):
                    if token not in current:
                        return None
                    current = current[token]
                elif isinstance(current, list):
                    idx = int(token)
                    if idx < 0 or idx >= len(current):
                        return None
                    current = current[idx]
                else:
                    return None
            
            last_token = tokens[-1]
            if isinstance(current, dict):
                if last_token not in current:
                    return None
                del current[last_token]
            elif isinstance(current, list):
                idx = int(last_token)
                if idx < 0 or idx >= len(current):
                    return None
                current.pop(idx)
            else:
                return None
            
            return result
        except:
            return None
    
    def apply_replace(doc, tokens, value):
        """Apply replace operation. Returns new doc or None."""
        try:
            result = copy.deepcopy(doc)
            
            if not tokens:
                return value
            
            current = result
            for token in tokens[:-1]:
                if isinstance(current, dict):
                    if token not in current:
                        return None
                    current = current[token]
                elif isinstance(current, list):
                    idx = int(token)
                    if idx < 0 or idx >= len(current):
                        return None
                    current = current[idx]
                else:
                    return None
            
            last_token = tokens[-1]
            if isinstance(current, dict):
                if last_token not in current:
                    return None
                current[last_token] = value
            elif isinstance(current, list):
                idx = int(last_token)
                if idx < 0 or idx >= len(current):
                    return None
                current[idx] = value
            else:
                return None
            
            return result
        except:
            return None
    
    def is_path_protected(path_tokens, protected_paths_tokens):
        """Check if modifying this path would violate protection."""
        for prot_tokens in protected_paths_tokens:
            if len(path_tokens) >= len(prot_tokens):
                if path_tokens[:len(prot_tokens)] == prot_tokens:
                    return True
            elif len(prot_tokens) > len(path_tokens):
                if prot_tokens[:len(path_tokens)] == path_tokens:
                    return True
        return False
    
    errors = []
    
    try:
        if not isinstance(operations, list):
            return {"valid": False, "errors": ["Operations must be a list"]}
        if not isinstance(protected_paths, list):
            return {"valid": False, "errors": ["Protected paths must be a list"]}
        
        protected_paths_tokens = []
        for pp in protected_paths:
            tokens = parse_pointer(pp)
            if tokens is None:
                return {"valid": False, "errors": ["Invalid protected path"]}
            protected_paths_tokens.append(tokens)
        
        current_doc = document
        
        for i, op in enumerate(operations):
            if not isinstance(op, dict):
                errors.append(f"Operation {i}: invalid format")
                continue
            
            op_type = op.get('op')
            path = op.get('path')
            
            if op_type not in ('add', 'remove', 'replace'):
                errors.append(f"Operation {i}: unsupported operation")
                continue
            
            path_tokens = parse_pointer(path)
            if path_tokens is None:
                errors.append(f"Operation {i}: invalid path")
                continue
            
            if is_path_protected(path_tokens, protected_paths_tokens):
                errors.append(f"Operation {i}: protected path")
                continue
            
            if op_type == 'add':
                if 'value' not in op:
                    errors.append(f"Operation {i}: missing value")
                    continue
                
                new_doc = apply_add(current_doc, path_tokens, op['value'])
                if new_doc is None:
                    errors.append(f"Operation {i}: invalid add")
                    continue
                
                current_doc = new_doc
            
            elif op_type == 'remove':
                new_doc = apply_remove(current_doc, path_tokens)
                if new_doc is None:
                    errors.append(f"Operation {i}: invalid remove")
                    continue
                
                current_doc = new_doc
            
            elif op_type == 'replace':
                if 'value' not in op:
                    errors.append(f"Operation {i}: missing value")
                    continue
                
                new_doc = apply_replace(current_doc, path_tokens, op['value'])
                if new_doc is None:
                    errors.append(f"Operation {i}: invalid replace")
                    continue
                
                current_doc = new_doc
        
        if errors:
            return {"valid": False, "errors": errors}
        else:
            return {"valid": True, "errors": []}
    
    except:
        return {"valid": False, "errors": ["Validation error"]}
