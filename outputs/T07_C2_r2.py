def merge_config(defaults, file_config, env_config, cli_config, schema) -> dict:
    _validate_schema(schema)
    
    merged = {}
    for config in [defaults, file_config, env_config, cli_config]:
        if config:
            merged = _deep_merge(merged, config)
    
    flat_merged = _flatten(merged)
    
    for key in flat_merged.keys():
        if key not in schema:
            raise ValueError(f"Unknown configuration key: {key}")
    
    result_flat = {}
    for key_path, schema_def in schema.items():
        if key_path in flat_merged:
            value = flat_merged[key_path]
            result_flat[key_path] = _convert_value(value, schema_def, key_path)
        elif schema_def.get("required", False):
            raise ValueError(f"Required configuration key missing: {key_path}")
    
    result = _unflatten(result_flat)
    return result


def _validate_schema(schema):
    if not isinstance(schema, dict):
        raise ValueError("Schema must be a dict")
    
    for key, spec in schema.items():
        if not isinstance(spec, dict):
            raise ValueError(f"Schema spec for '{key}' must be a dict")
        if "type" not in spec:
            raise ValueError(f"Schema spec for '{key}' missing 'type'")
        if spec["type"] not in ("int", "bool", "str"):
            raise ValueError(f"Invalid type '{spec['type']}' for '{key}'")
        if "required" not in spec:
            raise ValueError(f"Schema spec for '{key}' missing 'required'")
        if not isinstance(spec["required"], bool):
            raise ValueError(f"'required' for '{key}' must be a bool")
        if "min" in spec and not isinstance(spec["min"], (int, float)):
            raise ValueError(f"'min' for '{key}' must be numeric")
        if "max" in spec and not isinstance(spec["max"], (int, float)):
            raise ValueError(f"'max' for '{key}' must be numeric")


def _deep_merge(base, update):
    if not isinstance(update, dict):
        return update
    if not isinstance(base, dict):
        return update
    
    result = base.copy()
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _flatten(nested, parent_key=''):
    flat = {}
    for key, value in nested.items():
        if value is None:
            continue
        new_key = f"{parent_key}.{key}" if parent_key else key
        if isinstance(value, dict):
            flat.update(_flatten(value, new_key))
        else:
            flat[new_key] = value
    return flat


def _unflatten(flat):
    result = {}
    for key_path, value in flat.items():
        parts = key_path.split('.')
        current = result
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    return result


def _convert_value(value, spec, key_path):
    type_name = spec["type"]
    
    if type_name == "bool":
        if isinstance(value, bool):
            converted = value
        elif isinstance(value, str):
            if value.lower() == "true":
                converted = True
            elif value.lower() == "false":
                converted = False
            else:
                raise ValueError(f"Cannot convert '{value}' to bool")
        else:
            raise ValueError(f"Cannot convert {type(value).__name__} to bool")
    
    elif type_name == "int":
        if isinstance(value, int) and not isinstance(value, bool):
            converted = value
        elif isinstance(value, str):
            try:
                converted = int(value)
            except ValueError:
                raise ValueError(f"Cannot convert '{value}' to int")
        else:
            raise ValueError(f"Cannot convert {type(value).__name__} to int")
        
        if "min" in spec and converted < spec["min"]:
            raise ValueError(f"Value {converted} for '{key_path}' below minimum {spec['min']}")
        if "max" in spec and converted > spec["max"]:
            raise ValueError(f"Value {converted} for '{key_path}' above maximum {spec['max']}")
    
    elif type_name == "str":
        if isinstance(value, str):
            converted = value
        elif isinstance(value, bool):
            converted = str(value)
        elif isinstance(value, int):
            converted = str(value)
        else:
            raise ValueError(f"Cannot convert {type(value).__name__} to str")
    
    else:
        raise ValueError(f"Unknown type: {type_name}")
    
    return converted
