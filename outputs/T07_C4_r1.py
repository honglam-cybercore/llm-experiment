def merge_config(defaults, file_config, env_config, cli_config, schema) -> dict:
    _validate_schema(schema)
    
    defaults = defaults or {}
    file_config = file_config or {}
    env_config = env_config or {}
    cli_config = cli_config or {}
    
    merged = {}
    for config in [defaults, file_config, env_config, cli_config]:
        merged = _deep_merge(merged, config)
    
    flat_merged = _flatten_dict(merged)
    
    known_keys = set(schema.keys())
    present_keys = set(flat_merged.keys())
    unknown_keys = present_keys - known_keys
    
    if unknown_keys:
        raise ValueError(f"Unknown configuration keys: {', '.join(sorted(unknown_keys))}")
    
    result_flat = {}
    for key in present_keys:
        value = flat_merged[key]
        schema_def = schema[key]
        try:
            result_flat[key] = _convert_value(value, schema_def)
        except ValueError as e:
            raise ValueError(f"Configuration key '{key}': {str(e)}")
    
    for key, schema_def in schema.items():
        if schema_def.get('required', False) and key not in result_flat:
            raise ValueError(f"Required configuration key missing: {key}")
    
    result = _unflatten_dict(result_flat)
    return result


def _deep_merge(base, override):
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _flatten_dict(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def _unflatten_dict(d, sep='.'):
    result = {}
    for key, value in d.items():
        parts = key.split(sep)
        current = result
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    return result


def _validate_schema(schema):
    if not isinstance(schema, dict):
        raise ValueError("Schema must be a dictionary")
    
    valid_types = {'int', 'bool', 'str'}
    
    for key, schema_def in schema.items():
        if not isinstance(key, str):
            raise ValueError("Schema keys must be strings")
        
        if not isinstance(schema_def, dict):
            raise ValueError(f"Schema definition must be a dictionary for key '{key}'")
        
        if 'type' not in schema_def:
            raise ValueError(f"Schema definition must have 'type' for key '{key}'")
        
        if 'required' not in schema_def:
            raise ValueError(f"Schema definition must have 'required' for key '{key}'")
        
        schema_type = schema_def['type']
        if schema_type not in valid_types:
            raise ValueError(f"Invalid type '{schema_type}' for key '{key}'")
        
        if 'min' in schema_def or 'max' in schema_def:
            if schema_type != 'int':
                raise ValueError(f"Constraints are only valid for 'int' type for key '{key}'")


def _convert_value(value, schema_def):
    target_type = schema_def['type']
    
    if target_type == 'int':
        if isinstance(value, bool):
            raise ValueError("Cannot convert boolean to int")
        if isinstance(value, int):
            result = value
        elif isinstance(value, str):
            try:
                result = int(value)
            except ValueError:
                raise ValueError("Cannot convert string to int")
        else:
            raise ValueError(f"Cannot convert {type(value).__name__} to int")
    
    elif target_type == 'bool':
        if isinstance(value, bool):
            result = value
        elif isinstance(value, str):
            lower_val = value.lower()
            if lower_val == 'true':
                result = True
            elif lower_val == 'false':
                result = False
            else:
                raise ValueError("Cannot convert string to bool")
        else:
            raise ValueError(f"Cannot convert {type(value).__name__} to bool")
    
    elif target_type == 'str':
        if isinstance(value, str):
            result = value
        elif isinstance(value, bool):
            raise ValueError("Cannot convert boolean to str")
        else:
            result = str(value)
    
    else:
        raise ValueError(f"Unknown type: {target_type}")
    
    if 'min' in schema_def:
        if result < schema_def['min']:
            raise ValueError(f"Value is less than minimum {schema_def['min']}")
    
    if 'max' in schema_def:
        if result > schema_def['max']:
            raise ValueError(f"Value is greater than maximum {schema_def['max']}")
    
    return result
