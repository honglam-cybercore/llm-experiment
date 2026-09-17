def merge_config(defaults, file_config, env_config, cli_config, schema) -> dict:
    def fail(message):
        raise ValueError(message)

    sources = (defaults, file_config, env_config, cli_config)

    if not isinstance(schema, dict):
        fail("schema must be a dictionary")

    leaf_specs = {}
    prefixes = set()

    for path, spec in schema.items():
        if not isinstance(path, str) or not path or any(
            part == "" for part in path.split(".")
        ):
            fail("invalid schema key")

        parts = path.split(".")
        for index in range(1, len(parts)):
            prefixes.add(".".join(parts[:index]))

        if not isinstance(spec, dict):
            fail("invalid schema specification")

        value_type = spec.get("type")
        if value_type not in ("int", "bool", "str"):
            fail("invalid schema type")

        if not isinstance(spec.get("required"), bool):
            fail("invalid required flag")

        has_min = "min" in spec
        has_max = "max" in spec

        if value_type == "bool" and (has_min or has_max):
            fail("constraints are invalid for boolean values")

        if value_type in ("int", "str"):
            for bound_name in ("min", "max"):
                if bound_name in spec:
                    bound = spec[bound_name]
                    if not isinstance(bound, int) or isinstance(bound, bool):
                        fail("invalid schema constraint")

            if has_min and has_max and spec["min"] > spec["max"]:
                fail("invalid schema constraint")

        leaf_specs[path] = spec

    if set(leaf_specs) & prefixes:
        fail("schema contains conflicting paths")

    def validate_source(value, path=""):
        if not isinstance(value, dict):
            fail("configuration source must be a dictionary")

        for key, item in value.items():
            if not isinstance(key, str) or not key or "." in key:
                fail("invalid configuration key")

            full_path = f"{path}.{key}" if path else key

            if full_path in leaf_specs:
                continue

            if full_path in prefixes:
                if not isinstance(item, dict):
                    fail("nested configuration value must be a dictionary")
                validate_source(item, full_path)
                continue

            fail("unknown configuration key")

    for source in sources:
        validate_source(source)

    def clone(value):
        if isinstance(value, dict):
            return {key: clone(item) for key, item in value.items()}
        if isinstance(value, list):
            return [clone(item) for item in value]
        if isinstance(value, tuple):
            return tuple(clone(item) for item in value)
        return value

    def merge(base, overlay):
        if not isinstance(base, dict) or not isinstance(overlay, dict):
            return clone(overlay)

        result = clone(base)
        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge(result[key], value)
            else:
                result[key] = clone(value)
        return result

    merged = {}
    for source in sources:
        merged = merge(merged, source)

    def get_path(mapping, parts):
        current = mapping
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return False, None
            current = current[part]
        return True, current

    def set_path(mapping, parts, value):
        current = mapping
        for part in parts[:-1]:
            current = current[part]
        current[parts[-1]] = value

    def convert(value, spec):
        value_type = spec["type"]

        if value is None or isinstance(value, (dict, list, tuple, set)):
            fail("invalid configuration value")

        if value_type == "int":
            if isinstance(value, bool):
                fail("invalid integer value")
            if isinstance(value, int):
                converted = value
            elif isinstance(value, str):
                try:
                    text = value.strip()
                    if not text:
                        fail("invalid integer value")
                    converted = int(text, 10)
                except (TypeError, ValueError):
                    fail("invalid integer value")
            else:
                fail("invalid integer value")

            if "min" in spec and converted < spec["min"]:
                fail("configuration value below minimum")
            if "max" in spec and converted > spec["max"]:
                fail("configuration value above maximum")
            return converted

        if value_type == "bool":
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                normalized = value.strip().lower()
                if normalized == "true":
                    return True
                if normalized == "false":
                    return False
            fail("invalid boolean value")

        if not isinstance(value, str):
            value = str(value)

        if "min" in spec and len(value) < spec["min"]:
            fail("configuration value below minimum length")
        if "max" in spec and len(value) > spec["max"]:
            fail("configuration value above maximum length")
        return value

    for path, spec in leaf_specs.items():
        parts = path.split(".")
        present, value = get_path(merged, parts)

        if not present:
            if spec["required"]:
                fail("required configuration key is missing")
            continue

        set_path(merged, parts, convert(value, spec))

    return merged
