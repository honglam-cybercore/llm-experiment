from collections.abc import Mapping, Sequence, Set

ALLOWED_FIELDS = None
MAX_NESTING_DEPTH = 32


def evaluate_filter(expression, record) -> bool:
    if not isinstance(record, dict):
        raise ValueError("record must be a dictionary")

    def validate_value(value):
        if isinstance(value, Mapping):
            raise ValueError("nested mappings are not valid values")
        if isinstance(value, (list, tuple, set, frozenset)):
            for item in value:
                validate_value(item)

    def compatible_types(left, right):
        if isinstance(left, bool) or isinstance(right, bool):
            return type(left) is type(right)
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return True
        return type(left) is type(right)

    def compare(node, depth):
        if depth > MAX_NESTING_DEPTH:
            raise ValueError("expression nesting is excessive")

        if not isinstance(node, dict):
            raise ValueError("expression must be a dictionary")

        if "field" in node or "op" in node or "value" in node:
            if set(node) != {"field", "op", "value"}:
                raise ValueError("malformed comparison")
            field = node["field"]
            op = node["op"]
            value = node["value"]

            if not isinstance(field, str) or not field:
                raise ValueError("invalid field")
            if ALLOWED_FIELDS is not None and field not in ALLOWED_FIELDS:
                raise ValueError("unknown field")
            if field not in record:
                raise ValueError("unknown field")

            allowed_ops = {"eq", "ne", "gt", "gte", "lt", "lte", "in", "contains"}
            if op not in allowed_ops:
                raise ValueError("unknown operator")

            actual = record[field]
            validate_value(actual)
            validate_value(value)

            if op in {"eq", "ne", "gt", "gte", "lt", "lte"}:
                if not compatible_types(actual, value):
                    raise ValueError("incompatible comparison types")
                try:
                    if op == "eq":
                        return actual == value
                    if op == "ne":
                        return actual != value
                    if op == "gt":
                        return actual > value
                    if op == "gte":
                        return actual >= value
                    if op == "lt":
                        return actual < value
                    return actual <= value
                except (TypeError, ValueError):
                    raise ValueError("incompatible comparison types")

            if op == "in":
                if not isinstance(value, (list, tuple, set, frozenset)):
                    raise ValueError("invalid operand for in")
                if any(not compatible_types(actual, item) for item in value):
                    raise ValueError("incompatible comparison types")
                return actual in value

            if isinstance(actual, str):
                if not isinstance(value, str):
                    raise ValueError("incompatible comparison types")
                return value in actual

            if isinstance(actual, (list, tuple, set, frozenset)):
                if isinstance(value, (list, tuple, set, frozenset, Mapping)):
                    raise ValueError("invalid operand for contains")
                if not any(compatible_types(value, item) for item in actual):
                    raise ValueError("incompatible comparison types")
                return value in actual

            raise ValueError("invalid operand for contains")

        if len(node) != 1:
            raise ValueError("malformed logical expression")

        operator, operand = next(iter(node.items()))

        if operator in {"and", "or"}:
            if not isinstance(operand, list) or not operand:
                raise ValueError("logical operand must be a non-empty list")
            results = [evaluate_node(item, depth + 1) for item in operand]
            return all(results) if operator == "and" else any(results)

        if operator == "not":
            return not evaluate_node(operand, depth + 1)

        raise ValueError("unknown operator")

    def evaluate_node(node, depth):
        return compare(node, depth)

    return bool(evaluate_node(expression, 0))