from copy import deepcopy

def merge_config(defaults, file_config, env_config, cli_config, schema) -> dict:
    def merge_dicts(base, updates):
        result = deepcopy(base)
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_dicts(result[key], value)
            else:
                result[key] = value
        return result
    
    merged = defaults
    merged = merge_dicts(merged, file_config)
    merged = merge_dicts(merged, env_config)
    merged = merge_dicts(merged, cli_config)
    
    if not isinstance(schema, dict):
        raise ValueError("Schema must be a dict")
    
    for key, rule in schema.items():
        if not isinstance(rule, dict):
            raise ValueError(f"Schema rule for '{key}' must be a dict")
        if "type" not in rule:
            raise ValueError(f"Schema rule for '{key}' missing 'type'")
        if rule["type"] not in ("int", "bool", "str"):
            raise ValueError(f"Invalid type '{rule['type']}' for '{key}'")
        if "required" not in rule:
            raise ValueError(f"Schema rule for '{key}' missing 'required'")
        if not isinstance(rule["required"], bool):
            raise ValueError(f"'required' must be bool for '{key}'")
        if "min" in rule and "max" in rule:
            if rule["min"] > rule["max"]:
                raise ValueError(f"Invalid constraints for '{key}': min > max")
    
    def flatten(d, parent_key=""):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    flattened = flatten(merged)
    
    for key in flattened:
        if key not in schema:
            raise ValueError(f"Unknown key '{key}'")
    
    result_flat = {}
    for key, rule in schema.items():
        if key in flattened:
            value = flattened[key]
            try:
                if rule["type"] == "int":
                    converted = int(value)
                elif rule["type"] == "bool":
                    if isinstance(value, bool):
                        converted = value
                    elif isinstance(value, str):
                        if value == "true":
                            converted = True
                        elif value == "false":
                            converted = False
                        else:
                            raise ValueError()
                    else:
                        raise ValueError()
                elif rule["type"] == "str":
                    converted = str(value)
            except (ValueError, TypeError):
                raise ValueError(f"Cannot convert '{key}' to {rule['type']}")
            
            if "min" in rule and converted < rule["min"]:
                raise ValueError(f"Value for '{key}' is less than minimum {rule['min']}")
            if "max" in rule and converted > rule["max"]:
                raise ValueError(f"Value for '{key}' is greater than maximum {rule['max']}")
            
            result_flat[key] = converted
        elif rule["required"]:
            raise ValueError(f"Required key '{key}' is missing")
    
    def unflatten(flat):
        result = {}
        for key, value in flat.items():
            parts = key.split(".")
            current = result
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
        return result
    
    return unflatten(result_flat)
