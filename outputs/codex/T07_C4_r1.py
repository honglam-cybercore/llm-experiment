def merge_config(defaults, file_config, env_config, cli_config, schema) -> dict:
    allowed_types = {"int", "bool", "str"}

    if not isinstance(schema, dict):
        raise ValueError("schema must be a dictionary")

    class Node:
        __slots__ = ("children", "definition")

        def __init__(self):
            self.children = {}
            self.definition = None

    root = Node()

    for path, definition in schema.items():
        if not isinstance(path, str) or not path or any(
            not part for part in path.split(".")
        ):
            raise ValueError("invalid schema key")

        if not isinstance(definition, dict):
            raise ValueError("invalid schema definition")

        value_type = definition.get("type")
        required = definition.get("required")

        if value_type not in allowed_types or type(required) is not bool:
            raise ValueError("invalid schema definition")

        permitted = {"type", "required", "min", "max"}
        if any(key not in permitted for key in definition):
            raise ValueError("invalid schema definition")

        if "min" in definition and type(definition["min"]) is not int:
            raise ValueError("invalid schema constraint")
        if "max" in definition and type(definition["max"]) is not int:
            raise ValueError("invalid schema constraint")
        if (
            "min" in definition
            and "max" in definition
            and definition["min"] > definition["max"]
        ):
            raise ValueError("invalid schema constraint")

        if value_type == "bool" and ("min" in definition or "max" in definition):
            raise ValueError("invalid schema constraint")

        node = root
        parts = path.split(".")
        for part in parts:
            if node.definition is not None:
                raise ValueError("invalid schema structure")
            node = node.children.setdefault(part, Node())

        if node.definition is not None or node.children:
            raise ValueError("invalid schema structure")

        node.definition = dict(definition)

    sources = (defaults, file_config, env_config, cli_config)
    for source in sources:
        if not isinstance(source, dict):
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

    def validate_and_convert(value, node, path):
        if node.definition is not None:
            if node.children or isinstance(value, dict):
                raise ValueError("invalid configuration structure")

            definition = node.definition
            value_type = definition["type"]

            if value_type == "int":
                if isinstance(value, bool):
                    raise ValueError("invalid integer value")
                if isinstance(value, int):
                    converted = value
                elif isinstance(value, str):
                    try:
                        converted = int(value.strip(), 10)
                    except (TypeError, ValueError):
                        raise ValueError("invalid integer value") from None
                else:
                    raise ValueError("invalid integer value")

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
                        raise ValueError("invalid boolean value")
                else:
                    raise ValueError("invalid boolean value")

            else:
                if value is None or isinstance(value, (dict, list, tuple, set)):
                    raise ValueError("invalid string value")
                if isinstance(value, str):
                    converted = value
                elif isinstance(value, (int, float, bool)):
                    converted = str(value)
                else:
                    raise ValueError("invalid string value")

            if "min" in definition:
                minimum = definition["min"]
                comparable = len(converted) if value_type == "str" else converted
                if comparable < minimum:
                    raise ValueError("value below minimum")

            if "max" in definition:
                maximum = definition["max"]
                comparable = len(converted) if value_type == "str" else converted
                if comparable > maximum:
                    raise ValueError("value above maximum")

            return converted

        if not isinstance(value, dict):
            raise ValueError("invalid configuration structure")

        result = {}
        for key, child_value in value.items():
            if not isinstance(key, str) or key not in node.children:
                raise ValueError("unknown configuration key")
            result[key] = validate_and_convert(
                child_value,
                node.children[key],
                f"{path}.{key}" if path else key,
            )
        return result

    converted = validate_and_convert(merged, root, "")

    def check_required(node, value):
        if node.definition is not None:
            if node.definition["required"] and value is _MISSING:
                raise ValueError("required configuration is missing")
            return

        current = value if isinstance(value, dict) else {}
        for key, child in node.children.items():
            child_value = current[key] if key in current else _MISSING
            check_required(child, child_value)

    _MISSING = object()

    def check_required_raw(node, value):
        if node.definition is not None:
            if node.definition["required"] and value is _MISSING:
                raise ValueError("required configuration is missing")
            return

        current = value if isinstance(value, dict) else {}
        for key, child in node.children.items():
            check_required_raw(
                child,
                current[key] if key in current else _MISSING,
            )

    check_required_raw(root, merged)
    return converted