def evaluate_filter(expression, record) -> bool:
    if not isinstance(record, dict):
        raise ValueError("record must be a dictionary")

    def type_compatible(left, right):
        if isinstance(left, bool) or isinstance(right, bool):
            return isinstance(left, bool) and isinstance(right, bool)
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return True
        if left is None or right is None:
            return left is None and right is None
        if isinstance(left, str) or isinstance(right, str):
            return isinstance(left, str) and isinstance(right, str)
        if isinstance(left, (list, tuple, set)) or isinstance(right, (list, tuple, set)):
            return type(left) is type(right)
        return type(left) is type(right)

    def compare(node):
        if not isinstance(node, dict):
            raise ValueError("malformed expression")

        if "and" in node or "or" in node or "not" in node:
            if len(node) != 1:
                raise ValueError("malformed expression")

            if "and" in node:
                expressions = node["and"]
                if not isinstance(expressions, list):
                    raise ValueError("malformed expression")
                return all(compare(item) for item in expressions)

            if "or" in node:
                expressions = node["or"]
                if not isinstance(expressions, list):
                    raise ValueError("malformed expression")
                return any(compare(item) for item in expressions)

            return not compare(node["not"])

        if set(node) != {"field", "op", "value"}:
            raise ValueError("malformed expression")

        field = node["field"]
        operator = node["op"]
        expected = node["value"]

        if not isinstance(field, str) or field not in record:
            raise ValueError("unknown field")
        if operator not in {"eq", "ne", "gt", "gte", "lt", "lte", "in", "contains"}:
            raise ValueError("unknown operator")

        actual = record[field]

        if operator in {"eq", "ne", "gt", "gte", "lt", "lte"}:
            if not type_compatible(actual, expected):
                raise ValueError("incompatible types")

            try:
                if operator == "eq":
                    return actual == expected
                if operator == "ne":
                    return actual != expected
                if operator == "gt":
                    return actual > expected
                if operator == "gte":
                    return actual >= expected
                if operator == "lt":
                    return actual < expected
                return actual <= expected
            except (TypeError, ValueError):
                raise ValueError("incompatible types")

        if operator == "in":
            if not isinstance(expected, (list, tuple, set, frozenset, str)):
                raise ValueError("incompatible types")
            if isinstance(expected, str):
                if not isinstance(actual, str):
                    raise ValueError("incompatible types")
            elif not all(type_compatible(actual, item) for item in expected):
                raise ValueError("incompatible types")
            return actual in expected

        if isinstance(actual, str):
            if not isinstance(expected, str):
                raise ValueError("incompatible types")
            return expected in actual

        if not isinstance(actual, (list, tuple, set, frozenset)):
            raise ValueError("incompatible types")
        if not any(type_compatible(item, expected) for item in actual):
            raise ValueError("incompatible types")
        return expected in actual

    return bool(compare(expression))