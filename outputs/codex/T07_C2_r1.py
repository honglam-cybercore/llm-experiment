from copy import deepcopy


def merge_config(defaults, file_config, env_config, cli_config, schema) -> dict:
    def fail(message):
        raise ValueError(message)

    if not isinstance(schema, dict):
        fail("schema must be a dictionary")

    schema_map = {}
    for path, rules in schema.items():
        if not isinstance(path, str) or not path or any(part == "" for part in path.split(".")):
            fail("invalid schema key")
        if not isinstance(rules, dict):
            fail(f"invalid schema entry for {path}")

        value_type = rules.get("type")
        if value_type not in {"int", "bool", "str"}:
            fail(f"invalid type for {path}")

        required = rules.get("required")
        if not isinstance(required, bool):
            fail(f"invalid required flag for {path}")

        if "min" in rules or "max" in rules:
            if value_type == "bool":
                fail(f"constraints are invalid for {path}")

            for bound_name in ("min", "max"):
                if bound_name in rules:
                    bound = rules[bound_name]
                    if value_type == "int":
                        if isinstance(bound, bool) or not isinstance(bound, int):
                            fail(f"invalid {bound_name} for {path}")
                    elif not isinstance(bound, str):
                        fail(f"invalid {bound_name} for {path}")

            if "min" in rules and "max" in rules and rules["min"] > rules["max"]:
                fail(f"invalid constraint range for {path}")

        schema_map[path] = rules

    paths = list(schema_map)
    for path in paths:
        parts = path.split(".")
        for index in range(1, len(parts)):
            prefix = ".".join(parts[:index])
            if prefix in schema_map:
                fail("schema contains conflicting paths")

    def expand(source):
        if not isinstance(source, dict):
            fail("configuration source must be a dictionary")

        result = {}

        def insert(target, key, value):
            if not isinstance(key, str) or not key:
                fail("configuration contains an invalid key")

            parts = key.split(".")
            current = target
            for part in parts[:-1]:
                if not part:
                    fail("configuration contains an invalid key")
                existing = current.get(part)
                if existing is None:
                    existing = {}
                    current[part] = existing
                elif not isinstance(existing, dict):
                    fail("configuration contains conflicting keys")
                current = existing

            final = parts[-1]
            if not final:
                fail("configuration contains an invalid key")

            if final in current and isinstance(current[final], dict) and isinstance(value, dict):
                current[final] = merge_dicts(current[final], expand(value))
            else:
                current[final] = expand(value) if isinstance(value, dict) else value

        for key, value in source.items():
            insert(result, key, value)

        return result

    def merge_dicts(low, high):
        result = deepcopy(low)
        for key, value in high.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_dicts(result[key], value)
            else:
                result[key] = deepcopy(value)
        return result

    sources = [defaults, file_config, env_config, cli_config]
    merged = {}
    for source in sources:
        merged = merge_dicts(merged, expand(source))

    def is_known(path):
        return path in schema_map or any(
            schema_path.startswith(path + ".") for schema_path in schema_map
        )

    def convert(value, rules, path):
        value_type = rules["type"]

        try:
            if value_type == "int":
                if isinstance(value, bool):
                    raise ValueError
                if isinstance(value, int):
                    converted = value
                elif isinstance(value, str):
                    text = value.strip()
                    if not text:
                        raise ValueError
                    converted = int(text, 10)
                else:
                    raise ValueError

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
                if isinstance(value, str):
                    converted = value
                elif isinstance(value, (dict, list, tuple, set)):
                    raise ValueError
                else:
                    converted = str(value)

        except (TypeError, ValueError, OverflowError):
            fail(f"invalid value for {path}")

        for bound_name in ("min", "max"):
            if bound_name in rules:
                bound = rules[bound_name]
                if value_type == "int" and not (
                    rules.get("min") is not None and isinstance(bound, int)
                ):
                    fail(f"invalid constraint for {path}")
                try:
                    if bound_name == "min" and converted < bound:
                        fail(f"value below minimum for {path}")
                    if bound_name == "max" and converted > bound:
                        fail(f"value above maximum for {path}")
                except TypeError:
                    fail(f"invalid constraint for {path}")

        return converted

    def validate(node, prefix=""):
        if not isinstance(node, dict):
            fail("configuration structure is invalid")

        output = {}
        for key, value in node.items():
            path = f"{prefix}.{key}" if prefix else key

            if not is_known(path):
                fail(f"unknown configuration key: {path}")

            if path in schema_map:
                if isinstance(value, dict):
                    fail(f"invalid value for {path}")
                output[key] = convert(value, schema_map[path], path)
            else:
                if not isinstance(value, dict):
                    fail(f"invalid configuration structure at {path}")
                output[key] = validate(value, path)

        return output

    result = validate(merged)

    for path, rules in schema_map.items():
        if rules["required"]:
            current = result
            found = True
            for part in path.split("."):
                if not isinstance(current, dict) or part not in current:
                    found = False
                    break
                current = current[part]
            if not found:
                fail(f"required configuration key is missing: {path}")

    return result