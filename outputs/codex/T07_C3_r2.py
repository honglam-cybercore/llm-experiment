def merge_config(defaults, file_config, env_config, cli_config, schema) -> dict:
    def fail(message):
        raise ValueError(message)

    def validate_schema(value):
        if not isinstance(value, dict):
            fail("schema must be a dict")

        rules = {}
        prefixes = set()

        for path, rule in value.items():
            if not isinstance(path, str) or not path or any(
                not part for part in path.split(".")
            ):
                fail("invalid schema key")
            if not isinstance(rule, dict):
                fail("invalid schema rule")

            allowed = {"type", "required", "min", "max"}
            if any(key not in allowed for key in rule):
                fail("invalid schema rule")

            value_type = rule.get("type")
            if value_type not in {"int", "bool", "str"}:
                fail("invalid schema type")

            required = rule.get("required")
            if not isinstance(required, bool):
                fail("invalid required flag")

            if "min" in rule and "max" in rule:
                if type(rule["min"]) is not type(rule["max"]):
                    fail("incompatible constraints")

            if value_type == "bool" and ("min" in rule or "max" in rule):
                fail("boolean constraints are invalid")

            if value_type == "int":
                for bound_name in ("min", "max"):
                    if bound_name in rule and (
                        isinstance(rule[bound_name], bool)
                        or not isinstance(rule[bound_name], int)
                    ):
                        fail("invalid integer constraint")

            if value_type == "str":
                for bound_name in ("min", "max"):
                    if bound_name in rule and (
                        isinstance(rule[bound_name], bool)
                        or not isinstance(rule[bound_name], int)
                        or rule[bound_name] < 0
                    ):
                        fail("invalid string constraint")

            parts = path.split(".")
            for index in range(1, len(parts)):
                prefixes.add(".".join(parts[:index]))

            rules[path] = dict(rule)

        if set(rules) & prefixes:
            fail("schema contains conflicting paths")

        return rules, prefixes

    rules, prefixes = validate_schema(schema)

    def validate_source(source):
        if not isinstance(source, dict):
            fail("configuration source must be a dict")

        def walk(value, path=""):
            if not isinstance(value, dict):
                return

            for key, child in value.items():
                if not isinstance(key, str) or not key:
                    fail("invalid configuration key")

                current = f"{path}.{key}" if path else key
                if current not in rules and current not in prefixes:
                    fail("unknown configuration key")

                if isinstance(child, dict):
                    walk(child, current)
                elif current in prefixes:
                    fail("invalid configuration structure")

        walk(source)

    for source in (defaults, file_config, env_config, cli_config):
        validate_source(source)

    def merge(left, right):
        result = {}
        for key, value in left.items():
            result[key] = dict(value) if isinstance(value, dict) else value

        for key, value in right.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = merge(result[key], value)
            else:
                result[key] = dict(value) if isinstance(value, dict) else value
        return result

    merged = {}
    for source in (defaults, file_config, env_config, cli_config):
        merged = merge(merged, source)

    def flatten(value, path="", output=None):
        if output is None:
            output = {}

        if not isinstance(value, dict):
            output[path] = value
            return output

        for key, child in value.items():
            current = f"{path}.{key}" if path else key
            if isinstance(child, dict):
                flatten(child, current, output)
            else:
                output[current] = child

        return output

    flat = flatten(merged)
    converted = {}

    def convert(value, rule):
        value_type = rule["type"]

        try:
            if value_type == "int":
                if isinstance(value, bool):
                    raise ValueError
                result = int(value)
            elif value_type == "bool":
                if isinstance(value, bool):
                    result = value
                elif isinstance(value, str) and value in {"true", "false"}:
                    result = value == "true"
                else:
                    raise ValueError
            else:
                if isinstance(value, (dict, list, tuple, set)):
                    raise ValueError
                result = value if isinstance(value, str) else str(value)
        except (TypeError, ValueError, OverflowError):
            raise ValueError("configuration value cannot be converted")

        if value_type == "int":
            if "min" in rule and result < rule["min"]:
                fail("configuration value is below minimum")
            if "max" in rule and result > rule["max"]:
                fail("configuration value is above maximum")
        elif value_type == "str":
            length = len(result)
            if "min" in rule and length < rule["min"]:
                fail("configuration value is below minimum")
            if "max" in rule and length > rule["max"]:
                fail("configuration value is above maximum")

        return result

    for path, rule in rules.items():
        if path not in flat:
            if rule["required"]:
                fail("required configuration key is missing")
            continue
        converted[path] = convert(flat[path], rule)

    result = {}
    for path, value in converted.items():
        parts = path.split(".")
        current = result
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = value

    return result