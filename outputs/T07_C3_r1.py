def merge_config(defaults, file_config, env_config, cli_config, schema) -> dict:
    # Validate schema
    if not isinstance(schema, dict):
        raise ValueError("Schema must be a dict")
    
    for key, config in schema.items():
        if not isinstance(config, dict):
            raise ValueError(f"Schema entry for '{key}' must be a dict")
        if 'type' not in config:
            raise ValueError(f"Schema entry for '{key}' missing 'type'")
        if config['type'] not in ('int', 'bool', 'str'):
            raise ValueError(f"Schema entry for '{key}' has invalid type '{config['type']}'")
        if 'required' not in config:
            raise ValueError(f"Schema entry for '{key}' missing 'required'")
        if not isinstance(config['required'], bool):
            raise ValueError(f"Schema entry for '{key}' 'required' must be bool")
        if 'min' in config and 'max' in config:
            if config['min'] > config['max']:
                raise ValueError(f"Schema entry for '{key}' has min > max")
    
    # Normalize inputs to dicts
    defaults = defaults if isinstance(defaults, dict) else {}
    file_config = file_config if isinstance(file_config, dict) else {}
    env_config = env_config if isinstance(env_config, dict) else {}
    cli_config = cli_config if isinstance(cli_config, dict) else {}
    
    # Merge configs with precedence: defaults < file < env < cli
    def merge_dicts(base, override):
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_dicts(result[key], value)
            else:
                result[key] = value
        return result
    
    merged = merge_dicts(defaults, file_config)
    merged = merge_dicts(merged, env_config)
    merged = merge_dicts(merged, cli_config)
    
    # Flatten to dotted paths
    def flatten(d, parent_key=''):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    flattened = flatten(merged)
    
    # Check for unknown keys
    schema_keys = set(schema.keys())
    for key in flattened.keys():
        if key not in schema_keys:
            raise ValueError(f"Unknown key '{key}'")
    
    # Check for required keys
    for key, config in schema.items():
        if config['required'] and key not in flattened:
            raise ValueError(f"Required key '{key}' is missing")
    
    # Convert values and validate constraints
    converted = {}
    for key, schema_config in schema.items():
        if key not in flattened:
            continue
        
        value = flattened[key]
        target_type = schema_config['type']
        
        # Type conversion
        try:
            if target_type == 'bool':
                if isinstance(value, bool):
                    converted_value = value
                elif isinstance(value, str):
                    if value.lower() == 'true':
                        converted_value = True
                    elif value.lower() == 'false':
                        converted_value = False
                    else:
                        raise ValueError()
                else:
                    raise ValueError()
            elif target_type == 'int':
                converted_value = int(value)
            elif target_type == 'str':
                converted_value = str(value)
        except (ValueError, TypeError):
            raise ValueError(f"Cannot convert '{key}' to {target_type}")
        
        # Constraint validation
        if 'min' in schema_config:
            if converted_value < schema_config['min']:
                raise ValueError(f"Value for '{key}' below minimum")
        if 'max' in schema_config:
            if converted_value > schema_config['max']:
                raise ValueError(f"Value for '{key}' exceeds maximum")
        
        converted[key] = converted_value
    
    # Unflatten back to nested dict structure
    def unflatten(d):
        result = {}
        for key, value in d.items():
            parts = key.split('.')
            current = result
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
        return result
    
    return unflatten(converted)
