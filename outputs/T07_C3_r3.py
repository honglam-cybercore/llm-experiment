def merge_config(defaults, file_config, env_config, cli_config, schema) -> dict:
    configs = []
    for config in [defaults, file_config, env_config, cli_config]:
        if config is not None:
            if not isinstance(config, dict):
                raise ValueError("All config sources must be dicts or None")
            configs.append(config)
    
    _validate_schema(schema)
    
    merged = {}
    for config in configs:
        _merge_into(merged, config)
    
    flat_merged = _flatten_dict(merged)
    
    for key in flat_merged:
        if key not in schema:
            raise ValueError(f"Unknown key: {key}")
    
    result_flat = {}
    for key, spec in schema.items():
        if key in flat_merged:
            value = flat_merged[key]
            result_flat[key] = _convert_and_validate(value, spec, key)
        elif spec["required"]:
            raise ValueError(f"Required key missing: {key}")
    
    return _unflatten_dict(result_flat)


def _validate_schema(schema):
    if not isinstance(schema, dict):
        raise ValueError("Schema must be a dict")
    
    for key, spec in schema.items():
        if not isinstance(spec, dict):
            raise ValueError(f"Schema spec for '{key}' must be a dict")
        
        if "type" not in spec:
            raise ValueError(f"Schema spec for '{key}' missing 'type'")
        
        type_val = spec["type"]
        if type_val not in ("int", "bool", "str"):
            raise ValueError(f"Invalid type for '{key}': {type_val}")
        
        if "required" not in spec:
            raise ValueError(f"Schema spec for '{key}' missing 'required'")
        
        if not isinstance(spec["required"], bool):
            raise ValueError(f"'required' for '{key}' must be bool")
        
        if "min" in spec and "max" in spec:
            try:
                if spec["min"] > spec["max"]:
                    raise ValueError(f"Schema constraint for '{key}': min > max")
            except TypeError:
                raise ValueError(f"Schema constraint for '{key}': min and max must be comparable")


def _merge_into(target, source):
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _merge_into(target[key], value)
        else:
            target[key] = value


def _flatten_dict(d, prefix=""):
    result = {}
    for key, value in d.items():
        new_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result.update(_flatten_dict(value, new_key))
        else:
            result[new_key] = value
    return result


def _unflatten_dict(d):
    result = {}
    for key, value in d.items():
        parts = key.split(".")
        current = result
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    return result


def _convert_and_validate(value, spec, key):
    type_name = spec["type"]
    
    if type_name == "int":
        if isinstance(value, bool):
            raise ValueError(f"Cannot convert bool to int for key '{key}'")
        elif isinstance(value, int):
            converted = value
        elif isinstance(value, str):
            try:
                converted = int(value)
            except ValueError:
                raise ValueError(f"Cannot convert '{value}' to int for key '{key}'")
        else:
            raise ValueError(f"Cannot convert {type(value).__name__} to int for key '{key}'")
    elif type_name == "bool":
        if isinstance(value, bool):
            converted = value
        elif isinstance(value, str):
            if value == "true":
                converted = True
            elif value == "false":
                converted = False
            else:
                raise ValueError(f"Cannot convert '{value}' to bool for key '{key}'")
        else:
            raise ValueError(f"Cannot convert {type(value).__name__} to bool for key '{key}'")
    elif type_name == "str":
        if isinstance(value, str):
            converted = value
        else:
            try:
                converted = str(value)
            except Exception:
                raise ValueError(f"Cannot convert {type(value).__name__} to str for key '{key}'")
    
    if "min" in spec and converted < spec["min"]:
        raise ValueError(f"Value for key '{key}' ({converted}) is less than minimum ({spec['min']})")
    
    if "max" in spec and converted > spec["max"]:
        raise ValueError(f"Value for key '{key}' ({converted}) is greater than maximum ({spec['max']})")
    
    return converted
