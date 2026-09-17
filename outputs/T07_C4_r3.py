def merge_config(defaults, file_config, env_config, cli_config, schema) -> dict:
    """
    Merge configuration from multiple sources with validation against a schema.
    
    Precedence (lowest to highest): defaults, file_config, env_config, cli_config
    """
    
    def validate_schema(schema_dict):
        """Validate that the schema itself is valid."""
        if not isinstance(schema_dict, dict):
            raise ValueError("Schema must be a dict")
        
        for key, schema_def in schema_dict.items():
            if not isinstance(key, str):
                raise ValueError(f"Schema key must be a string")
            
            if not isinstance(schema_def, dict):
                raise ValueError(f"Schema definition for '{key}' must be a dict")
            
            if 'type' not in schema_def:
                raise ValueError(f"Schema definition for '{key}' missing 'type'")
            
            schema_type = schema_def['type']
            if schema_type not in ('int', 'bool', 'str'):
                raise ValueError(f"Invalid schema type for '{key}': {schema_type}")
            
            if 'required' not in schema_def:
                raise ValueError(f"Schema definition for '{key}' missing 'required'")
            
            if not isinstance(schema_def['required'], bool):
                raise ValueError(f"Schema 'required' for '{key}' must be a bool")
            
            # Check min/max constraints
            if 'min' in schema_def:
                if schema_type != 'int':
                    raise ValueError(f"'min' constraint only valid for 'int' type")
                if not isinstance(schema_def['min'], int) or isinstance(schema_def['min'], bool):
                    raise ValueError(f"'min' must be an int")
            
            if 'max' in schema_def:
                if schema_type != 'int':
                    raise ValueError(f"'max' constraint only valid for 'int' type")
                if not isinstance(schema_def['max'], int) or isinstance(schema_def['max'], bool):
                    raise ValueError(f"'max' must be an int")
    
    def flatten_dict(d, parent_key=''):
        """Flatten nested dict to dotted keys."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def unflatten_dict(d):
        """Convert dotted keys back to nested dict."""
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
    
    def deep_merge(d1, d2):
        """Recursively merge d2 into d1, with d2 taking precedence."""
        result = d1.copy()
        for key, value in d2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def convert_value(value, schema_def):
        """Convert value to schema type with validation."""
        schema_type = schema_def['type']
        
        if schema_type == 'bool':
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                if value.lower() == 'true':
                    return True
                elif value.lower() == 'false':
                    return False
            raise ValueError(f"Cannot convert to bool")
        
        elif schema_type == 'int':
            try:
                if isinstance(value, int) and not isinstance(value, bool):
                    converted = value
                elif isinstance(value, str):
                    converted = int(value)
                else:
                    raise ValueError()
            except (ValueError, TypeError):
                raise ValueError(f"Cannot convert to int")
            
            # Check min/max constraints
            if 'min' in schema_def and converted < schema_def['min']:
                raise ValueError(f"Value is less than minimum")
            if 'max' in schema_def and converted > schema_def['max']:
                raise ValueError(f"Value is greater than maximum")
            
            return converted
        
        elif schema_type == 'str':
            if isinstance(value, str):
                return value
            else:
                return str(value)
    
    # Validate schema
    validate_schema(schema)
    
    # Merge configurations from lowest to highest precedence
    merged = {}
    for config in [defaults, file_config, env_config, cli_config]:
        if config:
            merged = deep_merge(merged, config)
    
    # Flatten for validation
    flattened_merged = flatten_dict(merged)
    
    # Validate and convert values
    result_flat = {}
    
    for schema_key, schema_def in schema.items():
        if schema_key in flattened_merged:
            value = flattened_merged[schema_key]
            try:
                converted = convert_value(value, schema_def)
                result_flat[schema_key] = converted
            except ValueError as e:
                raise ValueError(f"Cannot convert key '{schema_key}': {str(e)}")
        elif schema_def.get('required', False):
            raise ValueError(f"Required key '{schema_key}' is missing")
    
    # Check for unknown keys
    for key in flattened_merged:
        if key not in schema:
            raise ValueError(f"Unknown key '{key}'")
    
    # Unflatten result
    return unflatten_dict(result_flat)
