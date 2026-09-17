def merge_config(defaults, file_config, env_config, cli_config, schema) -> dict:
    # Validate schema
    for schema_key, schema_spec in schema.items():
        if not isinstance(schema_spec, dict):
            raise ValueError(f"Invalid schema")
        
        if "type" not in schema_spec:
            raise ValueError(f"Invalid schema")
        if schema_spec["type"] not in ["int", "bool", "str"]:
            raise ValueError(f"Invalid schema")
        
        if "required" not in schema_spec:
            raise ValueError(f"Invalid schema")
        if not isinstance(schema_spec["required"], bool):
            raise ValueError(f"Invalid schema")
    
    # Merge configs with proper precedence
    def merge_dicts(base, override):
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_dicts(result[key], value)
            else:
                result[key] = value
        return result
    
    # Merge in order of precedence: defaults -> file -> env -> cli
    merged = {}
    merged = merge_dicts(merged, defaults)
    merged = merge_dicts(merged, file_config)
    merged = merge_dicts(merged, env_config)
    merged = merge_dicts(merged, cli_config)
    
    # Flatten the merged config to check against schema
    def flatten(d, prefix=""):
        result = {}
        for key, value in d.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                result.update(flatten(value, full_key))
            else:
                result[full_key] = value
        return result
    
    flat_merged = flatten(merged)
    
    # Check for unknown keys
    for key in flat_merged:
        if key not in schema:
            raise ValueError(f"Unknown key")
    
    # Check for required keys
    for schema_key, schema_spec in schema.items():
        if schema_spec["required"] and schema_key not in flat_merged:
            raise ValueError(f"Required key missing")
    
    # Convert and validate values
    converted = {}
    for key, value in flat_merged.items():
        schema_spec = schema[key]
        schema_type = schema_spec["type"]
        
        # Convert value
        if schema_type == "bool":
            if isinstance(value, bool):
                converted[key] = value
            elif isinstance(value, str):
                if value.lower() == "true":
                    converted[key] = True
                elif value.lower() == "false":
                    converted[key] = False
                else:
                    raise ValueError(f"Cannot convert to bool")
            else:
                raise ValueError(f"Cannot convert to bool")
        elif schema_type == "int":
            if isinstance(value, int) and not isinstance(value, bool):
                converted[key] = value
            elif isinstance(value, str):
                try:
                    converted[key] = int(value)
                except ValueError:
                    raise ValueError(f"Cannot convert to int")
            else:
                raise ValueError(f"Cannot convert to int")
            
            # Check constraints
            if "min" in schema_spec and converted[key] < schema_spec["min"]:
                raise ValueError(f"Value out of range")
            if "max" in schema_spec and converted[key] > schema_spec["max"]:
                raise ValueError(f"Value out of range")
        elif schema_type == "str":
            converted[key] = str(value)
            
            # Check constraints (min/max for strings are length)
            if "min" in schema_spec and len(converted[key]) < schema_spec["min"]:
                raise ValueError(f"Value out of range")
            if "max" in schema_spec and len(converted[key]) > schema_spec["max"]:
                raise ValueError(f"Value out of range")
    
    # Reconstruct nested dict from flattened
    def unflatten(flat_dict):
        result = {}
        for key, value in flat_dict.items():
            parts = key.split(".")
            current = result
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
        return result
    
    return unflatten(converted)
