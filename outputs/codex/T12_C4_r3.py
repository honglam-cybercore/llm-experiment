_MAX_DEPTH = 100
_LOGICAL_OPERATORS = {"and", "or", "not"}
_COMPARISON_OPERATORS = {"eq", "ne", "gt", "gte", "lt", "lte", "in", "contains"}


def evaluate_filter(expression, record) -> bool:
    if not isinstance(record, dict):
        raise ValueError("record must be a dictionary")
    return _evaluate(expression, record, 0)


def _evaluate(expression, record, depth):
    if depth > _MAX_DEPTH:
        raise ValueError("expression nesting is excessive")

    if not isinstance(expression, dict):
        raise ValueError("expression must be a dictionary")

    keys = set(expression)

    if keys == {"field", "op", "value"}:
        field = expression["field"]
        operator = expression["op"]
        operand = expression["value"]

        if not isinstance(field, str) or not field:
            raise ValueError("invalid field")
        if field not in record:
            raise ValueError("unknown field")
        if not isinstance(operator, str) or operator not in _COMPARISON_OPERATORS:
            raise ValueError("unknown operator")

        actual = record[field]
        _validate_value(actual)
        _validate_value(operand)
        return _compare(actual, operator, operand)

    if len(keys) != 1:
        raise ValueError("malformed expression")

    operator = next(iter(keys))

    if operator == "not":
        return not _evaluate(expression[operator], record, depth + 1)

    if operator in {"and", "or"}:
        operands = expression[operator]
        if not isinstance(operands, list) or not operands:
            raise ValueError("logical operands must be a non-empty list")

        results = [
            _evaluate(item, record, depth + 1)
            for item in operands
        ]
        return all(results) if operator == "and" else any(results)

    if operator in _LOGICAL_OPERATORS or operator in _COMPARISON_OPERATORS:
        raise ValueError("malformed expression")

    raise ValueError("unknown operator")


def _validate_value(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        if isinstance(value, float):
            if value != value or value in (float("inf"), float("-inf")):
                raise ValueError("invalid value")
        return

    if isinstance(value, list):
        for item in value:
            _validate_value(item)
        return

    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("invalid value")
            _validate_value(item)
        return

    raise ValueError("invalid value")


def _same_scalar_type(left, right):
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool)
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return True
    return type(left) is type(right)


def _compare(actual, operator, expected):
    if operator in {"eq", "ne"}:
        if not _compatible_for_equality(actual, expected):
            raise ValueError("incompatible comparison types")
        result = _secure_equal(actual, expected)
        return result if operator == "eq" else not result

    if operator in {"gt", "gte", "lt", "lte"}:
        if not _same_scalar_type(actual, expected):
            raise ValueError("incompatible comparison types")
        try:
            if operator == "gt":
                return actual > expected
            if operator == "gte":
                return actual >= expected
            if operator == "lt":
                return actual < expected
            return actual <= expected
        except (TypeError, ValueError):
            raise ValueError("incompatible comparison types")

    if operator == "in":
        if not isinstance(expected, list):
            raise ValueError("in requires a list operand")
        for item in expected:
            if not _compatible_for_equality(actual, item):
                raise ValueError("incompatible comparison types")
        return any(_secure_equal(actual, item) for item in expected)

    if operator == "contains":
        if isinstance(actual, str):
            if not isinstance(expected, str):
                raise ValueError("incompatible comparison types")
            return expected in actual

        if isinstance(actual, list):
            for item in actual:
                if not _compatible_for_equality(item, expected):
                    raise ValueError("incompatible comparison types")
            return any(_secure_equal(item, expected) for item in actual)

        raise ValueError("contains requires a string or list field")

    raise ValueError("unknown operator")


def _compatible_for_equality(left, right):
    if isinstance(left, list) and isinstance(right, list):
        return all(
            _compatible_for_equality(a, b)
            for a, b in zip(left, right)
        ) and len(left) == len(right)

    if isinstance(left, dict) and isinstance(right, dict):
        if set(left) != set(right):
            return False
        return all(_compatible_for_equality(left[key], right[key]) for key in left)

    if isinstance(left, (list, dict)) or isinstance(right, (list, dict)):
        return False

    if left is None or right is None:
        return left is None and right is None

    return _same_scalar_type(left, right)


def _secure_equal(left, right):
    if isinstance(left, dict):
        return (
            isinstance(right, dict)
            and list(left.keys()) == list(right.keys())
            and all(_secure_equal(left[key], right[key]) for key in left)
        )

    if isinstance(left, list):
        return (
            isinstance(right, list)
            and len(left) == len(right)
            and all(_secure_equal(a, b) for a, b in zip(left, right))
        )

    if isinstance(left, str) and isinstance(right, str):
        return left == right

    return left == right