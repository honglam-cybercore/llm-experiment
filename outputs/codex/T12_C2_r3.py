ALLOWED_FIELDS = None
MAX_NESTING = 100


def evaluate_filter(expression, record) -> bool:
    if not isinstance(record, dict):
        raise ValueError("record must be a dictionary")

    def compatible(a, b):
        if isinstance(a, bool) or isinstance(b, bool):
            return type(a) is type(b)
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return True
        return type(a) is type(b)

    def validate_value(value):
        if value is None or isinstance(value, (str, int, float, bool)):
            return
        if isinstance(value, (list, tuple, set)):
            for item in value:
                validate_value(item)
            return
        if isinstance(value, dict):
            for key, item in value.items():
                if not isinstance(key, str):
                    raise ValueError("invalid value type")
                validate_value(item)
            return
        raise ValueError("invalid value type")

    def evaluate(node, depth):
        if depth > MAX_NESTING or not isinstance(node, dict):
            raise ValueError("malformed expression")

        keys = set(node)

        if "and" in node:
            if keys != {"and"} or not isinstance(node["and"], list) or not node["and"]:
                raise ValueError("malformed expression")
            return all(evaluate(item, depth + 1) for item in node["and"])

        if "or" in node:
            if keys != {"or"} or not isinstance(node["or"], list) or not node["or"]:
                raise ValueError("malformed expression")
            return any(evaluate(item, depth + 1) for item in node["or"])

        if "not" in node:
            if keys != {"not"}:
                raise ValueError("malformed expression")
            return not evaluate(node["not"], depth + 1)

        if keys != {"field", "op", "value"}:
            raise ValueError("malformed expression")

        field = node["field"]
        op = node["op"]
        value = node["value"]

        if not isinstance(field, str):
            raise ValueError("malformed expression")
        if ALLOWED_FIELDS is not None and field not in ALLOWED_FIELDS:
            raise ValueError("unknown field")
        if field not in record:
            raise ValueError("unknown field")

        if op not in {"eq", "ne", "gt", "gte", "lt", "lte", "in", "contains"}:
            raise ValueError("unknown operator")

        actual = record[field]
        validate_value(actual)
        validate_value(value)

        if op in {"eq", "ne"}:
            if not compatible(actual, value):
                raise ValueError("incompatible types")
            return actual == value if op == "eq" else actual != value

        if op in {"gt", "gte", "lt", "lte"}:
            if not compatible(actual, value):
                raise ValueError("incompatible types")
            if isinstance(actual, (dict, list, tuple, set)) or actual is None:
                raise ValueError("incompatible types")
            try:
                if op == "gt":
                    return actual > value
                if op == "gte":
                    return actual >= value
                if op == "lt":
                    return actual < value
                return actual <= value
            except (TypeError, ValueError):
                raise ValueError("incompatible types")

        if op == "in":
            if not isinstance(value, (list, tuple, set, dict, str)):
                raise ValueError("invalid operand type")
            if isinstance(value, dict):
                return actual in value
            if isinstance(value, str):
                if not isinstance(actual, str):
                    raise ValueError("incompatible types")
                return actual in value
            for item in value:
                if not compatible(actual, item):
                    raise ValueError("incompatible types")
            return actual in value

        if not isinstance(actual, (list, tuple, set, dict, str)):
            raise ValueError("invalid operand type")
        if isinstance(actual, str):
            if not isinstance(value, str):
                raise ValueError("incompatible types")
            return value in actual
        if isinstance(actual, dict):
            if not isinstance(value, str):
                raise ValueError("incompatible types")
            return value in actual
        for item in actual:
            if not compatible(item, value):
                raise ValueError("incompatible types")
        return value in actual

    return bool(evaluate(expression, 0))