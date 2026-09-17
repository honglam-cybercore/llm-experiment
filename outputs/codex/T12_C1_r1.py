def evaluate_filter(expression, record) -> bool:
    if not isinstance(record, dict):
        raise ValueError("record must be a dictionary")

    def is_number(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def compatible(left, right):
        if left is None or right is None:
            return left is None and right is None
        if is_number(left) and is_number(right):
            return True
        if isinstance(left, bool) or isinstance(right, bool):
            return type(left) is type(right)
        return type(left) is type(right)

    def safe_equal(left, right):
        if not compatible(left, right):
            raise ValueError("incompatible comparison types")
        return left == right

    def compare(left, operator, right):
        if operator not in {"eq", "ne", "gt", "gte", "lt", "lte", "in", "contains"}:
            raise ValueError("unknown operator")

        if operator in {"eq", "ne"}:
            equal = safe_equal(left, right)
            return equal if operator == "eq" else not equal

        if operator in {"gt", "gte", "lt", "lte"}:
            if not compatible(left, right):
                raise ValueError("incompatible comparison types")
            if not (
                (is_number(left) and is_number(right))
                or isinstance(left, str) and isinstance(right, str)
            ):
                raise ValueError("incompatible comparison types")

            if operator == "gt":
                return left > right
            if operator == "gte":
                return left >= right
            if operator == "lt":
                return left < right
            return left <= right

        if operator == "in":
            if not isinstance(right, (list, tuple, set, frozenset, str, dict)):
                raise ValueError("in requires a container value")
            if isinstance(right, str) and not isinstance(left, str):
                raise ValueError("incompatible comparison types")

            for item in right:
                if compatible(left, item) and left == item:
                    return True
            return False

        if not isinstance(left, (list, tuple, set, frozenset, str, dict)):
            raise ValueError("contains requires a container field")
        if isinstance(left, str) and not isinstance(right, str):
            raise ValueError("incompatible comparison types")

        for item in left:
            if compatible(item, right) and item == right:
                return True
        return False

    def evaluate(node):
        if not isinstance(node, dict) or len(node) != 1:
            raise ValueError("malformed expression")

        key = next(iter(node))

        if key == "and":
            items = node[key]
            if not isinstance(items, list):
                raise ValueError("malformed expression")
            return all(evaluate(item) for item in items)

        if key == "or":
            items = node[key]
            if not isinstance(items, list):
                raise ValueError("malformed expression")
            return any(evaluate(item) for item in items)

        if key == "not":
            return not evaluate(node[key])

        if key not in {"field", "op", "value"}:
            raise ValueError("malformed expression")

        if set(node) != {"field", "op", "value"}:
            raise ValueError("malformed expression")

        field = node["field"]
        operator = node["op"]

        if not isinstance(field, str):
            raise ValueError("malformed expression")
        if field not in record:
            raise ValueError("unknown field")
        if not isinstance(operator, str):
            raise ValueError("unknown operator")

        return compare(record[field], operator, node["value"])

    return bool(evaluate(expression))