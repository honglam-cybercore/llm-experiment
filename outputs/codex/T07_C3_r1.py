def merge_config(defaults, file_config, env_config, cli_config, schema) -> dict:
    def fail(message):
        raise ValueError(message)

    def validate_schema(value):
        if not isinstance(value, dict):
            fail("schema must be a dictionary")

        leaves = {}
        for path, rule in value.items():
            if not isinstance(path, str) or not path or any(
                part == "" for part in path.split(".")
            ):
                fail("invalid schema key")
            if not isinstance(rule, dict):
                fail("invalid schema rule")
            if rule.get("type") not in {"int", "bool", "str"}:
                fail("invalid schema type")
            if not isinstance(rule.get("required"), bool):
                fail("invalid required flag")

            kind = rule["type"]
            for bound in ("min", "max"):
                if bound in rule:
                    bound_value = rule[bound]
                    if kind == "int":
                        if isinstance(bound_value, bool) or not isinstance(bound_value, int):
                            fail("invalid integer constraint")
                    elif kind == "str":
                        if not isinstance(bound_value, str):
                            fail("invalid string constraint")
                    else:
                        fail("boolean constraints are not supported")

            if "min" in rule and "max" in rule and rule["min"] > rule["max"]:
                fail("invalid constraint range")

            leaves[path] = rule

        paths = set(leaves)
        for path in paths:
            parts = path.split(".")
            for index in range(1, len(parts)):
                if ".".join(parts[:index]) in paths:
                    fail("schema contains conflicting paths")

        return leaves

    def validate_source(source):
        if not isinstance(source, dict):
            fail("configuration source must be a dictionary")

        def walk(value, prefix=""):
            if not isinstance(value, dict):
                return
            for key, child in value.items():
                if not isinstance(key, str) or not key:
                    fail("configuration keys must be non-empty strings")
                current = f"{prefix}.{key}" if prefix else key
                if current not in rules and not any(
                    path.startswith(current + ".") for path in rules
                ):
                    fail(f"unknown configuration key: {current}")
                if isinstance(child, dict):
                    walk(child, current)

        walk(source)

    def merge(left, right):
        result = dict(left)
        for key, value in right.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = merge(result[key], value)
            else:
                result[key] = value
        return result

    def convert(value, rule):
        kind = rule["type"]

        try:
            if kind == "int":
                if isinstance(value, bool):
                    fail("invalid integer value")
                converted = value if isinstance(value, int) else int(str(value).strip())
            elif kind == "bool":
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
                converted = value if isinstance(value, str) else str(value)
        except (TypeError, ValueError, OverflowError):
            fail("invalid configuration value")

        for bound in ("min", "max"):
            if bound in rule:
                limit = rule[bound]
                if bound == "min" and converted < limit:
                    fail("configuration value below minimum")
                if bound == "max" and converted > limit:
                    fail("configuration value above maximum")

        return converted

    def convert_tree(value, prefix=""):
        if not isinstance(value, dict):
            fail("expected nested configuration object")

        result = {}
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else key
            if path in rules:
                if isinstance(child, dict):
                    fail("nested object used for scalar configuration value")
                result[key] = convert(child, rules[path])
            else:
                result[key] = convert_tree(child, path)
        return result

    rules = validate_schema(schema)
    for source in (defaults, file_config, env_config, cli_config):
        validate_source(source)

    merged = {}
    for source in (defaults, file_config, env_config, cli_config):
        merged = merge(merged, source)

    result = convert_tree(merged)

    for path, rule in rules.items():
        if rule["required"]:
            current = result
            for part in path.split("."):
                if not isinstance(current, dict) or part not in current:
                    fail(f"required configuration key missing: {path}")
                current = current[part]

    return result