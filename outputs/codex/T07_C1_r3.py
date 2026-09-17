import copy


def merge_config(defaults, file_config, env_config, cli_config, schema) -> dict:
    def invalid(message):
        raise ValueError(message)

    if not isinstance(schema, dict):
        invalid("schema must be a dict")

    validated_schema = {}

    for path, rule in schema.items():
        if not isinstance(path, str) or not path or any(
            not part for part in path.split(".")
        ):
            invalid("invalid schema key")

        if not isinstance(rule, dict):
            invalid("invalid schema entry")

        value_type = rule.get("type")
        if value_type not in {"int", "bool", "str"}:
            invalid("invalid schema type")

        required = rule.get("required")
        if not isinstance(required, bool):
            invalid("invalid required flag")

        allowed = {"type", "required", "min", "max"}
        if any(key not in allowed for key in rule):
            invalid("invalid schema entry")

        if "min" in rule:
            minimum = rule["min"]
            if value_type == "int" and (not isinstance(minimum, int) or isinstance(minimum, bool)):
                invalid("invalid minimum")
            if value_type == "bool" and not isinstance(minimum, bool):
                invalid("invalid minimum")
            if value_type == "str" and not isinstance(minimum, str):
                invalid("invalid minimum")

        if "max" in rule:
            maximum = rule["max"]
            if value_type == "int" and (not isinstance(maximum, int) or isinstance(maximum, bool)):
                invalid("invalid maximum")
            if value_type == "bool" and not isinstance(maximum, bool):
                invalid("invalid maximum")
            if value_type == "str" and not isinstance(maximum, str):
                invalid("invalid maximum")

        if "min" in rule and "max" in rule and rule["min"] > rule["max"]:
            invalid("minimum exceeds maximum")

        validated_schema[path] = dict(rule)

    paths = set(validated_schema)
    prefixes = set()
    for path in paths:
        parts = path.split(".")
        prefixes.update(".".join(parts[:i]) for i in range(1, len(parts)))

    sources = (defaults, file_config, env_config, cli_config)
    for source in sources:
        if not isinstance(source, dict):
            invalid("configuration source must be a dict")

    def merge(left, right):
        result = copy.deepcopy(left)
        for key, value in right.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge(result[key], value)
            else:
                result[key] = copy.deepcopy(value)
        return result

    merged = {}
    for source in sources:
        merged = merge(merged, source)

    values = {}

    def collect(value, path=""):
        if isinstance(value, dict):
            if path and path not in prefixes and path not in paths:
                invalid("unknown configuration key: " + path)
            for key, child in value.items():
                if not isinstance(key, str) or not key:
                    invalid("invalid configuration key")
                child_path = key if not path else path + "." + key
                collect(child, child_path)
        else:
            if path not in paths:
                invalid("unknown configuration key: " + path)
            values[path] = value

    collect(merged)

    converted = {}
    for path, rule in validated_schema.items():
        if path not in values:
            if rule["required"]:
                invalid("required configuration key is missing: " + path)
            continue

        value = values[path]
        value_type = rule["type"]

        try:
            if value_type == "int":
                if isinstance(value, bool):
                    raise ValueError
                converted_value = int(value)
            elif value_type == "bool":
                if isinstance(value, bool):
                    converted_value = value
                elif isinstance(value, str) and value.strip().lower() in {"true", "false"}:
                    converted_value = value.strip().lower() == "true"
                else:
                    raise ValueError
            else:
                converted_value = value if isinstance(value, str) else str(value)
        except (TypeError, ValueError, OverflowError):
            invalid("invalid value for configuration key: " + path)

        if "min" in rule and converted_value < rule["min"]:
            invalid("value below minimum for configuration key: " + path)
        if "max" in rule and converted_value > rule["max"]:
            invalid("value above maximum for configuration key: " + path)

        converted[path] = converted_value

    result = {}
    for path, value in converted.items():
        target = result
        parts = path.split(".")
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value

    return result
