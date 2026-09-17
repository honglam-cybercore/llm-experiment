def merge_config(defaults, file_config, env_config, cli_config, schema) -> dict:
    # Validate schema
    if not isinstance(schema, dict):
        raise ValueError("Schema must be a dict")
    
    for key, key_schema in schema.items():
        if not isinstance(key_schema, dict):
            raise ValueError(f"Schema value for key '{key}' must be a dict")
        if "type" not in key_schema:
            raise ValueError(f"Schema for key '{key}' is missing 'type'")
        if key_schema["type"] not in ["int", "bool", "str"]:
            raise ValueError(f"Schema for key '{key}' has invalid type")
        if "required" not in key_schema:
            raise ValueError(f"Schema for key '{key}' is missing 'required'")
        if not isinstance(key_schema["required"], bool):
            raise ValueError(f"Schema for key '{key}' has invalid 'required'")
    
    # Merge configurations with precedence
    merged = {}
    for config in [defaults, file_config, env_config, cli_config]:
        if config is not None:
            merged = _deep_merge(merged, config)
    
    # Flatten merged config to handle dotted keys
    flat_merged = _flatten_dict(merged)
    
    # Check for unknown keys
    for key in flat_merged:
        if key not in schema:
            raise ValueError(f"Unknown key: {key}")
    
    # Process and convert values
    result = {}
    for key, key_schema in schema.items():
        if key in flat_merged:
            value = flat_merged[key]
            converted = _convert_value(value, key_schema["type"])
            _check_constraints(converted, key_schema, key)
            _set_nested_value(result, key, converted)
        else:
            if key_schema.get("required", False):
                raise ValueError(f"Missing required key: {key}")
    
    return result

def _deep_merge(base, override):
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def _flatten_dict(d, parent_key=''):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}.{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key).items())
        else:
            items.append((new_key, v))
    return dict(items)

def _convert_value(value, target_type):
    if target_type == "int":
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                raise ValueError(f"Cannot convert '{value}' to int")
        raise ValueError(f"Cannot convert {type(value).__name__} to int")
    elif target_type == "bool":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            if value == "true":
                return True
            elif value == "false":
                return False
            else:
                raise ValueError(f"Cannot convert '{value}' to bool")
        raise ValueError(f"Cannot convert {type(value).__name__} to bool")
    elif target_type == "str":
        if isinstance(value, str):
            return value
        return str(value)
    else:
        raise ValueError(f"Unknown type: {target_type}")

def _check_constraints(value, key_schema, key):
    if "min" in key_schema:
        if value < key_schema["min"]:
            raise ValueError(f"Value for key '{key}' below minimum")
    if "max" in key_schema:
        if value > key_schema["max"]:
            raise ValueError(f"Value for key '{key}' exceeds maximum")

def _set_nested_value(d, path, value):
    keys = path.split('.')
    current = d
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value
