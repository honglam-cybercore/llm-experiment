from copy import deepcopy


def merge_config(defaults, file_config, env_config, cli_config, schema) -> dict:
    def fail(message):
        raise ValueError(message)

    def validate_schema(schema_obj):
        if not isinstance(schema_obj, dict):
            fail("schema must be a dictionary")

        parsed = {}

        for key, spec in schema_obj.items():
            if not isinstance(key, str) or not key or any(part == "" for part in key.split(".")):
                fail("invalid schema key")

            if not isinstance(spec, dict):
                fail("invalid schema entry")

            if set(spec) - {"type", "required", "min", "max"}:
                fail("invalid schema entry")

            value_type = spec.get("type")
            if value_type not in {"int", "bool", "str"}:
                fail("invalid schema type")

            if not isinstance(spec.get("required"), bool):
                fail("invalid required flag")

            for bound_name in ("min", "max"):
                if bound_name in spec:
                    bound = spec[bound_name]
                    if isinstance(bound, bool) or not isinstance(bound, int):
                        fail("invalid schema constraint")
                    if value_type == "bool":
                        fail("constraints are not valid for booleans")

            if "min" in spec and "max" in spec and spec["min"] > spec["max"]:
                fail("invalid schema constraints")

            parts = tuple(key.split("."))
            parsed[parts] = dict(spec)

        paths = set(parsed)
        for path in paths:
            for index in range(1, len(path)):
                if path[:index] in paths:
                    fail("conflicting schema paths")

        return parsed

    def validate_source(source):
        if not isinstance(source, dict):
            fail("configuration sources must be dictionaries")

        for key, value in source.items():
            if not isinstance(key, str):
                fail("configuration keys must be strings")
            if isinstance(value, dict):
                validate_source(value)

    def merge(low, high):
        result = deepcopy(low)
        for key, value in high.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge(result[key], value)
            else:
                result[key] = deepcopy(value)
        return result

    parsed_schema = validate_schema(schema)
    validate_source(defaults)
    validate_source(file_config)
    validate_source(env_config)
    validate_source(cli_config)

    merged = merge(
        merge(
            merge(deepcopy(defaults), file_config),
            env_config,
        ),
        cli_config,
    )

    prefixes = set()
    for path in parsed_schema:
        for index in range(1, len(path)):
            prefixes.add(path[:index])

    def validate_keys(value, path=()):
        if isinstance(value, dict):
            if path and path in parsed_schema:
                fail("configuration value must not be a dictionary")

            if path and path not in prefixes and path not in parsed_schema:
                fail("unknown configuration key")

            for key, child in value.items():
                child_path = path + (key,)
                if isinstance(child, dict):
                    validate_keys(child, child_path)
                elif child_path not in parsed_schema:
                    fail("unknown configuration key")
        else:
            if path not in parsed_schema:
                fail("unknown configuration key")

    validate_keys(merged)

    missing = object()

    def get_path(value, path):
        current = value
        for key in path:
            if not isinstance(current, dict) or key not in current:
                return missing
            current = current[key]
        return current

    def convert(value, spec):
        value_type = spec["type"]

        if value_type == "int":
            if isinstance(value, bool):
                fail("invalid integer value")
            if isinstance(value, int):
                converted = value
            elif isinstance(value, str):
                try:
                    converted = int(value.strip(), 10)
                except (TypeError, ValueError, OverflowError):
                    fail("invalid integer value")
            else:
                fail("invalid integer value")

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
                    fail("invalid boolean value")
            else:
                fail("invalid boolean value")

        else:
            if isinstance(value, str):
                converted = value
            elif isinstance(value, (dict, list, tuple, set)) or value is None:
                fail("invalid string value")
            else:
                converted = str(value)

        if "min" in spec:
            bound = spec["min"]
            comparable = len(converted) if value_type == "str" else converted
            if comparable < bound:
                fail("value below minimum")

        if "max" in spec:
            bound = spec["max"]
            comparable = len(converted) if value_type == "str" else converted
            if comparable > bound:
                fail("value above maximum")

        return converted

    for path, spec in parsed_schema.items():
        value = get_path(merged, path)
        if value is missing:
            if spec["required"]:
                fail("required configuration key is missing")

    def convert_tree(value, path=()):
        if isinstance(value, dict):
            return {
                key: convert_tree(child, path + (key,))
                for key, child in value.items()
            }
        return convert(value, parsed_schema[path])

    return convert_tree(merged) if merged else {}