def validate_patch(document, operations, protected_paths) -> dict:
    import copy
    
    errors = []
    
    working_doc = copy.deepcopy(document)
    
    def unescape_pointer(token):
        result = []
        i = 0
        while i < len(token):
            if token[i] == '~':
                if i + 1 < len(token):
                    if token[i + 1] == '0':
                        result.append('~')
                        i += 2
                    elif token[i + 1] == '1':
                        result.append('/')
                        i += 2
                    else:
                        return None
                else:
                    return None
            else:
                result.append(token[i])
                i += 1
        return ''.join(result)
    
    def parse_pointer(path):
        if not isinstance(path, str):
            return None
        
        if path == '':
            return []
        
        if not path.startswith('/'):
            return None
        
        parts = path[1:].split('/')
        unescaped_parts = []
        for part in parts:
            unescaped = unescape_pointer(part)
            if unescaped is None:
                return None
            unescaped_parts.append(unescaped)
        
        return unescaped_parts
    
    def get_value(doc, pointer_parts):
        current = doc
        for part in pointer_parts:
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
    
    def path_is_protected(path, protected_paths):
        if not protected_paths:
            return False
        
        for protected in protected_paths:
            if path == protected:
                return True
            if path.startswith(protected + '/'):
                return True
            if protected.startswith(path + '/'):
                return True
        
        return False
    
    def can_parent_exist(doc, pointer_parts):
        if len(pointer_parts) == 0:
            return False
        
        parent_parts = pointer_parts[:-1]
        parent, exists = get_value(doc, parent_parts)
        
        if not exists:
            return False
        
        return isinstance(parent, (dict, list))
    
    def set_value(doc, pointer_parts, value):
        doc = copy.deepcopy(doc)
        
        if len(pointer_parts) == 0:
            return value
        
        current = doc
        for part in pointer_parts[:-1]:
            if isinstance(current, dict):
                if part not in current:
                    return None
                current = current[part]
            elif isinstance(current, list):
                try:
                    index = int(part)
                    if index < 0 or index >= len(current):
                        return None
                    current = current[index]
                except ValueError:
                    return None
            else:
                return None
        
        last_part = pointer_parts[-1]
        if isinstance(current, dict):
            current[last_part] = value
        elif isinstance(current, list):
            try:
                index = int(last_part)
                if index < 0 or index > len(current):
                    return None
                if index == len(current):
                    current.append(value)
                else:
                    current[index] = value
            except ValueError:
                return None
        else:
            return None
        
        return doc
    
    def remove_value(doc, pointer_parts):
        doc = copy.deepcopy(doc)
        
        if len(pointer_parts) == 0:
            return None
        
        current = doc
        for part in pointer_parts[:-1]:
            if isinstance(current, dict):
                if part not in current:
                    return None
                current = current[part]
            elif isinstance(current, list):
                try:
                    index = int(part)
                    if index < 0 or index >= len(current):
                        return None
                    current = current[index]
                except ValueError:
                    return None
            else:
                return None
        
        last_part = pointer_parts[-1]
        if isinstance(current, dict):
            if last_part not in current:
                return None
            del current[last_part]
        elif isinstance(current, list):
            try:
                index = int(last_part)
                if index < 0 or index >= len(current):
                    return None
                current.pop(index)
            except ValueError:
                return None
        else:
            return None
        
        return doc
    
    for i, op in enumerate(operations):
        if not isinstance(op, dict):
            errors.append(f"Operation {i}: not a dict")
            continue
        
        op_type = op.get('op')
        path = op.get('path')
        
        if op_type not in ('add', 'remove', 'replace'):
            errors.append(f"Operation {i}: unsupported operation '{op_type}'")
            continue
        
        if not isinstance(path, str):
            errors.append(f"Operation {i}: path must be a string")
            continue
        
        pointer_parts = parse_pointer(path)
        if pointer_parts is None:
            errors.append(f"Operation {i}: invalid JSON Pointer '{path}'")
            continue
        
        if path_is_protected(path, protected_paths):
            errors.append(f"Operation {i}: path '{path}' is protected")
            continue
        
        if op_type == 'add':
            if 'value' not in op:
                errors.append(f"Operation {i}: add operation missing 'value'")
                continue
            
            if not can_parent_exist(working_doc, pointer_parts):
                errors.append(f"Operation {i}: invalid parent path for add operation")
                continue
            
            new_doc = set_value(working_doc, pointer_parts, op['value'])
            if new_doc is None:
                errors.append(f"Operation {i}: failed to add value")
                continue
            
            working_doc = new_doc
        
        elif op_type == 'remove':
            _, exists = get_value(working_doc, pointer_parts)
            if not exists:
                errors.append(f"Operation {i}: path does not exist for remove operation")
                continue
            
            new_doc = remove_value(working_doc, pointer_parts)
            if new_doc is None:
                errors.append(f"Operation {i}: failed to remove value")
                continue
            
            working_doc = new_doc
        
        elif op_type == 'replace':
            if 'value' not in op:
                errors.append(f"Operation {i}: replace operation missing 'value'")
                continue
            
            _, exists = get_value(working_doc, pointer_parts)
            if not exists:
                errors.append(f"Operation {i}: path does not exist for replace operation")
                continue
            
            new_doc = set_value(working_doc, pointer_parts, op['value'])
            if new_doc is None:
                errors.append(f"Operation {i}: failed to replace value")
                continue
            
            working_doc = new_doc
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }
