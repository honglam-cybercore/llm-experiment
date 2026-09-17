from __future__ import annotations

from typing import Any


_ALLOWED_TYPES = {"int", "bool", "str"}
_SCHEMA_FIELDS = {"type", "required", "min", "max"}


def merge_config(defaults, file_config, env_config, cli_config, schema) -> dict:
    _validate_schema(schema)

    merged = {}
    for source in (defaults, file_config, env_config, cli_config):
        if not isinstance(source, dict):
            raise ValueError("configuration sources must be dictionaries")
        _validate_config_tree(source)
        merged = _merge_dicts(merged, source)

    for path in _flatten_paths(merged):
        if path not in schema:
            raise ValueError(f"unknown configuration key: {path}")

    result = {}
    for path, rules in schema.items():
        present, raw_value = _get_path(merged, path)
        if not present:
            if rules["required"]:
                raise ValueError(f"required configuration key is missing: {path}")
            continue

        value = _convert_value(raw_value, rules["type"], path)
        if "min" in rules and value < rules["min"]:
            raise ValueError(f"configuration value below minimum: {path}")
        if "max" in rules and value > rules["max"]:
            raise ValueError(f"configuration value above maximum: {path}")

        _set_path(result, path, value)

    return result


def _validate_schema(schema: Any) -> None:
    if not isinstance(schema, dict):
        raise ValueError("schema must be a dictionary")

    paths = set()
    for path, rules in schema.items():
        if not isinstance(path, str) or not path or any(
            not part for part in path.split(".")
        ):
            raise ValueError("schema contains an invalid key")

        if path in paths:
            raise ValueError("schema contains duplicate keys")
        paths.add(path)

        if not isinstance(rules, dict):
            raise ValueError(f"invalid schema entry: {path}")
        if any(key not in _SCHEMA_FIELDS for key in rules):
            raise ValueError(f"invalid schema field: {path}")
        if rules.get("type") not in _ALLOWED_TYPES:
            raise ValueError(f"invalid schema type: {path}")
        if not isinstance(rules.get("required"), bool):
            raise ValueError(f"invalid required flag: {path}")

        value_type = rules["type"]
        for bound_name in ("min", "max"):
            if bound_name not in rules:
                continue
            bound = rules[bound_name]
            if value_type == "int":
                valid_bound = isinstance(bound, int) and not isinstance(bound, bool)
            elif value_type == "str":
                valid_bound = isinstance(bound, str)
            else:
                valid_bound = False
            if not valid_bound:
                raise ValueError(f"invalid {bound_name} constraint: {path}")

        if "min" in rules and "max" in rules and rules["min"] > rules["max"]:
            raise ValueError(f"invalid constraint range: {path}")

    for path in paths:
        parts = path.split(".")
        for index in range(1, len(parts)):
            if ".".join(parts[:index]) in paths:
                raise ValueError("schema contains conflicting nested keys")


def _validate_config_tree(value: Any, seen=None) -> None:
    if seen is None:
        seen = set()

    if not isinstance(value, dict):
        return

    identity = id(value)
    if identity in seen:
        raise ValueError("configuration contains a cyclic dictionary")
    seen.add(identity)

    for key, child in value.items():
        if not isinstance(key, str) or not key:
            raise ValueError("configuration keys must be non-empty strings")
        _validate_config_tree(child, seen)

    seen.remove(identity)


def _merge_dicts(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge_dicts(result[key], value)
        elif isinstance(value, dict):
            result[key] = _merge_dicts({}, value)
        else:
            result[key] = value
    return result


def _flatten_paths(value: dict, prefix: str = ""):
    paths = []
    for key, child in value.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(child, dict):
            paths.extend(_flatten_paths(child, path))
        else:
            paths.append(path)
    return paths


def _get_path(value: dict, path: str):
    current = value
    parts = path.split(".")
    for index, part in enumerate(parts):
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
        if index < len(parts) - 1 and not isinstance(current, dict):
            return False, None
    return True, current


def _set_path(target: dict, path: str, value: Any) -> None:
    current = target
    parts = path.split(".")
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = value


def _convert_value(value: Any, value_type: str, path: str) -> Any:
    try:
        if value_type == "int":
            if isinstance(value, bool):
                raise ValueError
            if isinstance(value, int):
                return value
            if isinstance(value, str):
                return int(value.strip(), 10)
            raise ValueError

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
            if isinstance(value, (dict, list, tuple, set)):
                raise ValueError
            return str(value)
    except (TypeError, ValueError, OverflowError):
        raise ValueError(f"invalid value for configuration key: {path}") from None

    raise ValueError(f"invalid schema type: {path}")