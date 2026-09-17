def merge_config(defaults, file_config, env_config, cli_config, schema) -> dict:
    _validate_schema(schema)
    
    merged = {}
    for config in [defaults, file_config, env_config, cli_config]:
        if config:
            _merge_dicts(merged, config)
    
    flat_merged = _flatten_dict(merged)
    
    for key in flat_merged.keys():
        if key not in schema:
            raise ValueError(f"Unknown key in config: {key}")
    
    result = {}
    for key, spec in schema.items():
        if key in flat_merged:
            result[key] = _convert_value(flat_merged[key], spec)
        elif spec.get("required", False):
            raise ValueError(f"Missing required key: {key}")
    
    return _unflatten_dict(result)


def _validate_schema(schema):
    if not isinstance(schema, dict):
        raise ValueError("Schema must be a dict")
    
    for key, spec in schema.items():
        if not isinstance(spec, dict):
            raise ValueError(f"Schema entry for '{key}' must be a dict")
        
        if "type" not in spec:
            raise ValueError(f"Schema entry for '{key}' missing 'type'")
        if "required" not in spec:
            raise ValueError(f"Schema entry for '{key}' missing 'required'")
        
        if spec["type"] not in ("int", "bool", "str"):
            raise ValueError(f"Schema entry for '{key}' has invalid type")
        
        if not isinstance(spec["required"], bool):
            raise ValueError(f"Schema entry for '{key}' has non-bool 'required'")
        
        allowed_keys = {"type", "required", "min", "max"}
        for field_key in spec.keys():
            if field_key not in allowed_keys:
                raise ValueError(f"Schema entry for '{key}' has unknown field")
        
        if spec["type"] != "int" and ("min" in spec or "max" in spec):
            raise ValueError(f"Schema entry for '{key}' has min/max with non-int type")


def _merge_dicts(target, source):
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _merge_dicts(target[key], value)
        else:
            target[key] = value


def _flatten_dict(d, parent_key=""):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}.{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key).items())
        else:
            items.append((new_key, v))
    return dict(items)


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


def _convert_value(value, spec):
    target_type = spec["type"]
    
    if target_type == "str":
        if isinstance(value, str):
            result = value
        else:
            result = str(value)
    
    elif target_type == "bool":
        if isinstance(value, bool):
            result = value
        elif isinstance(value, str):
            lower_val = value.lower()
            if lower_val == "true":
                result = True
            elif lower_val == "false":
                result = False
            else:
                raise ValueError(f"Cannot convert to bool")
        else:
            raise ValueError(f"Cannot convert to bool")
    
    elif target_type == "int":
        if isinstance(value, bool):
            raise ValueError(f"Cannot convert bool to int")
        elif isinstance(value, int):
            result = value
        elif isinstance(value, str):
            try:
                result = int(value)
            except ValueError:
                raise ValueError(f"Cannot convert to int")
        else:
            raise ValueError(f"Cannot convert to int")
    
    else:
        raise ValueError(f"Invalid type in schema")
    
    if target_type == "int":
        if "min" in spec and result < spec["min"]:
            raise ValueError(f"Value below minimum")
        if "max" in spec and result > spec["max"]:
            raise ValueError(f"Value above maximum")
    
    return result
