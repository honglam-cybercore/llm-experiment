def merge_config(defaults, file_config, env_config, cli_config, schema) -> dict:
    import re

    if not isinstance(schema, dict):
        raise ValueError("schema must be a dictionary")

    schema_types = {}
    schema_prefixes = set()

    for path, rules in schema.items():
        if not isinstance(path, str) or not path or any(
            not part for part in path.split(".")
        ):
            raise ValueError("invalid schema key")

        if not isinstance(rules, dict):
            raise ValueError("schema rules must be dictionaries")

        value_type = rules.get("type")
        if value_type not in ("int", "bool", "str"):
            raise ValueError("invalid schema type")

        if not isinstance(rules.get("required"), bool):
            raise ValueError("schema required must be a boolean")

        if "min" in rules and "max" in rules:
            if value_type == "int":
                if (
                    isinstance(rules["min"], bool)
                    or isinstance(rules["max"], bool)
                    or not isinstance(rules["min"], int)
                    or not isinstance(rules["max"], int)
                    or rules["min"] > rules["max"]
                ):
                    raise ValueError("invalid schema constraints")
            elif rules["min"] > rules["max"]:
                raise ValueError("invalid schema constraints")

        if value_type != "int" and ("min" in rules or "max" in rules):
            raise ValueError("min and max are only valid for int values")

        schema_types[path] = rules
        parts = path.split(".")
        for index in range(1, len(parts)):
            schema_prefixes.add(".".join(parts[:index]))

    if set(schema_types) & schema_prefixes:
        raise ValueError("schema contains conflicting paths")

    def validate_source(value, prefix=""):
        if not isinstance(value, dict):
            raise ValueError("configuration sources must be dictionaries")

        for key, item in value.items():
            if not isinstance(key, str) or not key:
                raise ValueError("invalid configuration key")

            path = f"{prefix}.{key}" if prefix else key

            if path in schema_types:
                if isinstance(item, dict):
                    raise ValueError("configuration value must not be a dictionary")
            elif path in schema_prefixes:
                validate_source(item, path)
            else:
                raise ValueError(f"unknown configuration key: {path}")

    sources = (defaults, file_config, env_config, cli_config)
    for source in sources:
        validate_source(source)

    def deep_merge(base, overlay):
        result = dict(base)
        for key, value in overlay.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    merged = {}
    for source in sources:
        merged = deep_merge(merged, source)

    missing = object()

    def get_value(mapping, path):
        current = mapping
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                return missing
            current = current[part]
        return current

    def convert(value, rules):
        if value is None:
            raise ValueError("configuration value cannot be None")

        value_type = rules["type"]

        try:
            if value_type == "int":
                if isinstance(value, bool):
                    raise ValueError
                if isinstance(value, int):
                    converted = value
                elif isinstance(value, str) and re.fullmatch(r"[+-]?\d+", value.strip()):
                    converted = int(value.strip())
                else:
                    raise ValueError

            elif value_type == "bool":
                if isinstance(value, bool):
                    converted = value
                elif isinstance(value, str):
                    normalized = value.strip().lower()
                    if normalized == "true":
                        converted = True
                    elif normalized == "false":
                        converted = False
                    else:
                        raise ValueError
                else:
                    raise ValueError

            else:
                converted = value if isinstance(value, str) else str(value)
        except Exception as exc:
            raise ValueError("invalid configuration value") from exc

        if value_type == "int":
            if "min" in rules and converted < rules["min"]:
                raise ValueError("configuration value is below minimum")
            if "max" in rules and converted > rules["max"]:
                raise ValueError("configuration value exceeds maximum")

        return converted

    result = {}
    for path, rules in schema_types.items():
        value = get_value(merged, path)

        if value is missing:
            if rules["required"]:
                raise ValueError(f"required configuration key is missing: {path}")
            continue

        converted = convert(value, rules)
        current = result
        parts = path.split(".")

        for part in parts[:-1]:
            current = current.setdefault(part, {})

        current[parts[-1]] = converted

    return result