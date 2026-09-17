def merge_config(defaults, file_config, env_config, cli_config, schema) -> dict:
    def fail():
        raise ValueError("invalid configuration")

    if not isinstance(schema, dict):
        fail()

    schema_map = {}

    for path, spec in schema.items():
        if not isinstance(path, str) or not path or any(
            not part for part in path.split(".")
        ):
            fail()
        if not isinstance(spec, dict):
            fail()

        value_type = spec.get("type")
        if value_type not in ("int", "bool", "str"):
            fail()
        if not isinstance(spec.get("required"), bool):
            fail()

        has_min = "min" in spec
        has_max = "max" in spec

        if value_type == "int":
            for bound_name, present in (("min", has_min), ("max", has_max)):
                if present and (
                    isinstance(spec[bound_name], bool)
                    or not isinstance(spec[bound_name], int)
                ):
                    fail()
        elif has_min or has_max:
            fail()

        if has_min and has_max and spec["min"] > spec["max"]:
            fail()

        schema_map[path] = spec

    paths = list(schema_map)
    for path in paths:
        parts = path.split(".")
        for index in range(1, len(parts)):
            if ".".join(parts[:index]) in schema_map:
                fail()

    sources = (defaults, file_config, env_config, cli_config)
    if any(not isinstance(source, dict) for source in sources):
        fail()

    def merge_into(target, source):
        for key, value in source.items():
            if not isinstance(key, str) or not key:
                fail()
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                merge_into(target[key], value)
            elif isinstance(value, dict):
                nested = {}
                merge_into(nested, value)
                target[key] = nested
            else:
                target[key] = value

    merged = {}
    for source in sources:
        merge_into(merged, source)

    flattened = {}

    def flatten(value, prefix=""):
        if not isinstance(value, dict):
            if not prefix:
                fail()
            flattened[prefix] = value
            return

        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(child, dict):
                flatten(child, path)
            else:
                flattened[path] = child

    flatten(merged)

    for path in flattened:
        if path not in schema_map:
            fail()

    for path, spec in schema_map.items():
        if path not in flattened:
            if spec["required"]:
                fail()
            continue

        raw = flattened[path]
        value_type = spec["type"]

        try:
            if raw is None:
                fail()

            if value_type == "int":
                if isinstance(raw, bool):
                    fail()
                converted = raw if isinstance(raw, int) else int(raw)

            elif value_type == "bool":
                if isinstance(raw, bool):
                    converted = raw
                elif isinstance(raw, str) and raw.lower() in ("true", "false"):
                    converted = raw.lower() == "true"
                else:
                    fail()

            else:
                converted = raw if isinstance(raw, str) else str(raw)
        except (TypeError, ValueError, OverflowError):
            fail()

        if "min" in spec and converted < spec["min"]:
            fail()
        if "max" in spec and converted > spec["max"]:
            fail()

        flattened[path] = converted

    result = {}

    for path, value in flattened.items():
        parts = path.split(".")
        current = result
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = value

    return result