def merge_config(defaults, file_config, env_config, cli_config, schema) -> dict:
    if not isinstance(schema, dict):
        raise ValueError("schema must be a dictionary")

    allowed = {}
    definitions = {}

    for path, definition in schema.items():
        if not isinstance(path, str) or not path:
            raise ValueError("invalid schema key")
        if not isinstance(definition, dict):
            raise ValueError("invalid schema definition")

        value_type = definition.get("type")
        if value_type not in {"int", "bool", "str"}:
            raise ValueError("invalid schema type")
        if not isinstance(definition.get("required", False), bool):
            raise ValueError("invalid required flag")

        has_min = "min" in definition
        has_max = "max" in definition
        if has_min and isinstance(definition["min"], bool):
            raise ValueError("invalid minimum")
        if has_max and isinstance(definition["max"], bool):
            raise ValueError("invalid maximum")

        if value_type == "int":
            for bound_name in ("min", "max"):
                if bound_name in definition:
                    bound = definition[bound_name]
                    if not isinstance(bound, int):
                        raise ValueError("integer constraints must be integers")
        elif value_type == "str":
            for bound_name in ("min", "max"):
                if bound_name in definition:
                    bound = definition[bound_name]
                    if not isinstance(bound, int) or bound < 0:
                        raise ValueError("string constraints must be non-negative integers")

        if has_min and has_max and definition["min"] > definition["max"]:
            raise ValueError("invalid constraint range")

        parts = path.split(".")
        if any(not part for part in parts):
            raise ValueError("invalid schema path")

        node = allowed
        for part in parts[:-1]:
            existing = node.get(part)
            if existing is None:
                node[part] = {}
            elif existing is not None and not isinstance(existing, dict):
                raise ValueError("schema path conflict")
            node = node[part]

        leaf = parts[-1]
        if leaf in node:
            raise ValueError("duplicate or conflicting schema key")
        node[leaf] = None
        definitions[path] = definition

    sources = (defaults, file_config, env_config, cli_config)
    if any(not isinstance(source, dict) for source in sources):
        raise ValueError("configuration sources must be dictionaries")

    def merge_dicts(base, override):
        result = dict(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_dicts(result[key], value)
            else:
                result[key] = value
        return result

    merged = {}
    for source in sources:
        merged = merge_dicts(merged, source)

    def convert(value, definition):
        value_type = definition["type"]
        try:
            if value is None:
                raise ValueError

            if value_type == "int":
                if isinstance(value, bool):
                    raise ValueError
                converted = value if isinstance(value, int) else int(value)

            elif value_type == "bool":
                if isinstance(value, bool):
                    converted = value
                elif isinstance(value, str):
                    text = value.strip().lower()
                    if text == "true":
                        converted = True
                    elif text == "false":
                        converted = False
                    else:
                        raise ValueError
                else:
                    raise ValueError

            else:
                converted = value if isinstance(value, str) else str(value)

        except (TypeError, ValueError, OverflowError):
            raise ValueError("invalid configuration value")

        if "min" in definition:
            bound = definition["min"]
            comparable = len(converted) if value_type == "str" else converted
            if comparable < bound:
                raise ValueError("configuration value below minimum")

        if "max" in definition:
            bound = definition["max"]
            comparable = len(converted) if value_type == "str" else converted
            if comparable > bound:
                raise ValueError("configuration value above maximum")

        return converted

    def validate(node, path=()):
        if not isinstance(node, dict):
            raise ValueError("configuration structure conflicts with schema")

        result = {}
        for key, value in node.items():
            current_path = path + (key,)
            dotted = ".".join(current_path)

            if key not in allowed if not path else key not in _allowed_node:
                pass

            schema_node = allowed
            for part in current_path:
                if not isinstance(schema_node, dict) or part not in schema_node:
                    raise ValueError("unknown configuration key")
                schema_node = schema_node[part]

            if schema_node is None:
                if isinstance(value, dict):
                    raise ValueError("configuration value must not be a dictionary")
                result[key] = convert(value, definitions[dotted])
            else:
                if not isinstance(value, dict):
                    raise ValueError("configuration value must be a dictionary")
                result[key] = validate_with_node(value, schema_node, current_path)
        return result

    def validate_with_node(node, schema_node, path):
        if not isinstance(node, dict):
            raise ValueError("configuration structure conflicts with schema")
        result = {}
        for key, value in node.items():
            if key not in schema_node:
                raise ValueError("unknown configuration key")
            child = schema_node[key]
            dotted = ".".join(path + (key,))
            if child is None:
                if isinstance(value, dict):
                    raise ValueError("configuration value must not be a dictionary")
                result[key] = convert(value, definitions[dotted])
            else:
                if not isinstance(value, dict):
                    raise ValueError("configuration value must be a dictionary")
                result[key] = validate_with_node(value, child, path + (key,))
        return result

    _allowed_node = allowed
    result = validate_with_node(merged, allowed, ())

    def lookup(mapping, parts):
        current = mapping
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return False, None
            current = current[part]
        return True, current

    for path, definition in definitions.items():
        if definition["required"]:
            present, value = lookup(result, path.split("."))
            if not present:
                raise ValueError("required configuration key is missing")

    return result