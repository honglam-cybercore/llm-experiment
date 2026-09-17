import copy


def merge_config(defaults, file_config, env_config, cli_config, schema) -> dict:
    allowed_types = {"int", "bool", "str"}

    if not isinstance(schema, dict):
        raise ValueError("schema must be a dictionary")

    schema_rules = {}
    schema_paths = set()

    for path, rule in schema.items():
        if not isinstance(path, str) or not path or any(
            not part for part in path.split(".")
        ):
            raise ValueError("invalid schema key")

        if not isinstance(rule, dict):
            raise ValueError("invalid schema rule")

        if set(rule) - {"type", "required", "min", "max"}:
            raise ValueError("invalid schema rule fields")

        value_type = rule.get("type")
        required = rule.get("required")

        if value_type not in allowed_types or type(required) is not bool:
            raise ValueError("invalid schema rule")

        if "min" in rule and "max" in rule:
            lower = rule["min"]
            upper = rule["max"]

            if value_type == "int":
                if (
                    type(lower) is not int
                    or type(upper) is not int
                    or lower > upper
                ):
                    raise ValueError("invalid schema constraints")
            elif value_type == "str":
                if (
                    type(lower) is not int
                    or type(upper) is not int
                    or lower < 0
                    or lower > upper
                ):
                    raise ValueError("invalid schema constraints")
            else:
                raise ValueError("invalid schema constraints")
        elif "min" in rule or "max" in rule:
            bound = rule.get("min", rule.get("max"))
            if value_type == "int" and type(bound) is not int:
                raise ValueError("invalid schema constraint")
            if value_type == "str" and (
                type(bound) is not int or bound < 0
            ):
                raise ValueError("invalid schema constraint")
            if value_type == "bool":
                raise ValueError("invalid schema constraint")

        schema_rules[path] = rule
        schema_paths.add(path)

    for path in schema_paths:
        parts = path.split(".")
        for index in range(1, len(parts)):
            if ".".join(parts[:index]) in schema_paths:
                raise ValueError("schema contains conflicting paths")

    def is_schema_prefix(path):
        prefix = path + "."
        return any(key.startswith(prefix) for key in schema_paths)

    def validate_source(value, path=""):
        if not isinstance(value, dict):
            raise ValueError("configuration source must be a dictionary")

        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("configuration keys must be strings")

            current_path = f"{path}.{key}" if path else key

            if current_path in schema_paths:
                continue

            if isinstance(item, dict) and is_schema_prefix(current_path):
                validate_source(item, current_path)
            else:
                raise ValueError(f"unknown configuration key: {current_path}")

    sources = (defaults, file_config, env_config, cli_config)
    for source in sources:
        validate_source(source)

    def deep_merge(base, override):
        result = copy.deepcopy(base)
        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = copy.deepcopy(value)
        return result

    merged = {}
    for source in sources:
        merged = deep_merge(merged, source)

    def get_path(mapping, path):
        current = mapping
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                return False, None
            current = current[part]
        return True, current

    def set_path(mapping, path, value):
        parts = path.split(".")
        current = mapping
        for part in parts[:-1]:
            current = current[part]
        current[parts[-1]] = value

    def convert(value, value_type):
        try:
            if value_type == "int":
                if isinstance(value, bool):
                    return int(value)
                return int(value)

            if value_type == "bool":
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    if value == "true":
                        return True
                    if value == "false":
                        return False
                raise ValueError

            if value_type == "str":
                return str(value)

        except (TypeError, ValueError, OverflowError):
            raise ValueError("value cannot be converted")

        raise ValueError("invalid schema type")

    result = copy.deepcopy(merged)

    for path, rule in schema_rules.items():
        present, raw_value = get_path(result, path)

        if not present:
            if rule["required"]:
                raise ValueError(f"required key is missing: {path}")
            continue

        converted = convert(raw_value, rule["type"])

        if rule["type"] == "int":
            if "min" in rule and converted < rule["min"]:
                raise ValueError(f"value below minimum: {path}")
            if "max" in rule and converted > rule["max"]:
                raise ValueError(f"value above maximum: {path}")
        elif rule["type"] == "str":
            if "min" in rule and len(converted) < rule["min"]:
                raise ValueError(f"value below minimum: {path}")
            if "max" in rule and len(converted) > rule["max"]:
                raise ValueError(f"value above maximum: {path}")

        set_path(result, path, converted)

    return result