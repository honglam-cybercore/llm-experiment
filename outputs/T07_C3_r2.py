def merge_config(defaults, file_config, env_config, cli_config, schema) -> dict:
    validate_schema(schema)
    
    merged_flat = {}
    for config in [defaults, file_config, env_config, cli_config]:
        flat = flatten_dict(config)
        merged_flat.update(flat)
    
    for key in merged_flat:
        if key not in schema:
            raise ValueError(f"Unknown key: {key}")
    
    result = {}
    for key, rules in schema.items():
        if key in merged_flat:
            value = merged_flat[key]
            result[key] = convert_value(value, rules)
        elif rules.get('required', False):
            raise ValueError(f"Required key missing: {key}")
    
    return unflatten_dict(result)

def flatten_dict(d):
    if not isinstance(d, dict):
        return {}
    
    result = {}
    
    def _flatten(obj, prefix=''):
        for key, value in obj.items():
            new_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                _flatten(value, new_key)
            else:
                result[new_key] = value
    
    _flatten(d)
    return result

def unflatten_dict(d):
    result = {}
    
    for key, value in d.items():
        parts = key.split('.')
        current = result
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            elif not isinstance(current[part], dict):
                raise ValueError("Schema conflict")
            current = current[part]
        
        if parts[-1] in current and isinstance(current[parts[-1]], dict):
            raise ValueError("Schema conflict")
        
        current[parts[-1]] = value
    
    return result

def validate_schema(schema):
    if not isinstance(schema, dict):
        raise ValueError("Schema must be a dict")
    
    for key, rules in schema.items():
        if not isinstance(rules, dict):
            raise ValueError("Schema rule must be a dict")
        
        if 'type' not in rules:
            raise ValueError("Schema rule must have 'type'")
        
        if rules['type'] not in ('int', 'bool', 'str'):
            raise ValueError("Invalid type")
        
        if 'required' not in rules:
            raise ValueError("Schema rule must have 'required'")
        
        if not isinstance(rules['required'], bool):
            raise ValueError("'required' must be bool")
        
        if 'min' in rules and 'max' in rules:
            try:
                if rules['min'] > rules['max']:
                    raise ValueError("min > max")
            except TypeError:
                raise ValueError("Invalid min/max")
    
    keys = list(schema.keys())
    for i, key in enumerate(keys):
        for other_key in keys[i+1:]:
            if other_key.startswith(key + '.') or key.startswith(other_key + '.'):
                raise ValueError("Schema keys conflict")

def convert_value(value, rules):
    target_type = rules['type']
    
    if target_type == 'bool':
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            if value.lower() == 'true':
                return True
            if value.lower() == 'false':
                return False
        raise ValueError("Cannot convert to bool")
    
    elif target_type == 'int':
        if isinstance(value, int) and not isinstance(value, bool):
            int_value = value
        else:
            try:
                int_value = int(value)
            except (ValueError, TypeError):
                raise ValueError("Cannot convert to int")
        
        if 'min' in rules and int_value < rules['min']:
            raise ValueError("Value less than min")
        if 'max' in rules and int_value > rules['max']:
            raise ValueError("Value greater than max")
        
        return int_value
    
    elif target_type == 'str':
        return str(value)
