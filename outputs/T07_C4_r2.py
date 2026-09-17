def merge_config(defaults, file_config, env_config, cli_config, schema) -> dict:
    if not isinstance(schema, dict):
        raise ValueError("Schema must be a dictionary")
    
    for key, schema_spec in schema.items():
        if not isinstance(schema_spec, dict):
            raise ValueError(f"Schema spec for '{key}' must be a dictionary")
        if "type" not in schema_spec:
            raise ValueError(f"Schema spec for '{key}' must have 'type'")
        if schema_spec["type"] not in ("int", "bool", "str"):
            raise ValueError(f"Invalid type '{schema_spec['type']}' in schema for '{key}'")
        if "required" not in schema_spec:
            raise ValueError(f"Schema spec for '{key}' must have 'required'")
        if not isinstance(schema_spec["required"], bool):
            raise ValueError(f"'required' must be bool in schema for '{key}'")
        if "min" in schema_spec and "max" in schema_spec:
            if schema_spec["min"] > schema_spec["max"]:
                raise ValueError(f"Schema spec for '{key}' has min > max")
    
    merged = {}
    for config in [defaults, file_config, env_config, cli_config]:
        if config:
            merged = _deep_merge(merged, config)
    
    merged_flat = _flatten_dict(merged)
    
    for key in merged_flat:
        if key not in schema:
            raise ValueError(f"Unknown key '{key}' in configuration")
    
    result = {}
    for schema_key, schema_spec in schema.items():
        value = merged_flat.get(schema_key)
        
        if value is None:
            if schema_spec["required"]:
                raise ValueError(f"Required key '{schema_key}' is missing")
        else:
            converted = _convert_value(value, schema_spec["type"], schema_key)
            
            if "min" in schema_spec:
                if converted < schema_spec["min"]:
                    raise ValueError(f"Value for '{schema_key}' ({converted}) is less than minimum ({schema_spec['min']})")
            
            if "max" in schema_spec:
                if converted > schema_spec["max"]:
                    raise ValueError(f"Value for '{schema_key}' ({converted}) is greater than maximum ({schema_spec['max']})")
            
            _set_nested_value(result, schema_key, converted)
    
    return result


def _deep_merge(base, override):
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _flatten_dict(d, prefix=""):
    flat = {}
    for key, value in d.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(_flatten_dict(value, full_key))
        else:
            flat[full_key] = value
    return flat


def _set_nested_value(d, key, value):
    parts = key.split(".")
    current = d
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


def _convert_value(value, expected_type, key):
    if expected_type == "int":
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                raise ValueError(f"Cannot convert '{value}' to int for key '{key}'")
        raise ValueError(f"Cannot convert {type(value).__name__} to int for key '{key}'")
    
    elif expected_type == "bool":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lower_val = value.lower()
            if lower_val == "true":
                return True
            elif lower_val == "false":
                return False
            else:
                raise ValueError(f"Cannot convert '{value}' to bool for key '{key}'")
        raise ValueError(f"Cannot convert {type(value).__name__} to bool for key '{key}'")
    
    elif expected_type == "str":
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return str(value)
        raise ValueError(f"Cannot convert {type(value).__name__} to str for key '{key}'")
    
    else:
        raise ValueError(f"Unknown type '{expected_type}' in schema for key '{key}'")
