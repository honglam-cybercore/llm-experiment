import math

ALLOWED_FIELDS = None
MAX_NESTING = 100


def evaluate_filter(expression, record) -> bool:
    if not isinstance(record, dict):
        raise ValueError("record must be a dictionary")

    for key, value in record.items():
        if not isinstance(key, str) or not _valid_value(value):
            raise ValueError("invalid record")

    return _evaluate(expression, record, 0, set())


def _evaluate(expression, record, depth, active):
    if depth > MAX_NESTING or not isinstance(expression, dict):
        raise ValueError("malformed expression")

    identity = id(expression)
    if identity in active:
        raise ValueError("malformed expression")

    active.add(identity)
    try:
        keys = set(expression)
        if keys == {"field", "op", "value"}:
            return _evaluate_comparison(expression, record)
        if keys == {"and"}:
            operands = expression["and"]
            if not isinstance(operands, list) or not operands:
                raise ValueError("malformed expression")
            results = [
                _evaluate(item, record, depth + 1, active)
                for item in operands
            ]
            return all(results)
        if keys == {"or"}:
            operands = expression["or"]
            if not isinstance(operands, list) or not operands:
                raise ValueError("malformed expression")
            results = [
                _evaluate(item, record, depth + 1, active)
                for item in operands
            ]
            return any(results)
        if keys == {"not"}:
            return not _evaluate(expression["not"], record, depth + 1, active)
        raise ValueError("malformed expression")
    finally:
        active.remove(identity)


def _evaluate_comparison(expression, record):
    field = expression["field"]
    operator = expression["op"]
    operand = expression["value"]

    if not isinstance(field, str):
        raise ValueError("invalid field")
    if operator not in {"eq", "ne", "gt", "gte", "lt", "lte", "in", "contains"}:
        raise ValueError("unknown operator")
    if not _valid_value(operand):
        raise ValueError("invalid operand")

    allowed = ALLOWED_FIELDS
    if allowed is not None:
        try:
            permitted = field in allowed
        except TypeError:
            raise ValueError("invalid field configuration")
    else:
        permitted = field in record

    if not permitted or field not in record:
        raise ValueError("unknown field")

    value = record[field]

    if operator in {"eq", "ne"}:
        if not _compatible(value, operand):
            raise ValueError("incompatible types")
        result = _equal(value, operand)
        return result if operator == "eq" else not result

    if operator in {"gt", "gte", "lt", "lte"}:
        if not _orderable(value) or not _orderable(operand):
            raise ValueError("incompatible types")
        if _type_group(value) != _type_group(operand):
            raise ValueError("incompatible types")
        if operator == "gt":
            return value > operand
        if operator == "gte":
            return value >= operand
        if operator == "lt":
            return value < operand
        return value <= operand

    if operator == "in":
        if not isinstance(operand, list):
            raise ValueError("invalid operand")
        for item in operand:
            if not _compatible(value, item):
                raise ValueError("incompatible types")
        return any(_equal(value, item) for item in operand)

    if operator == "contains":
        if isinstance(value, str) and isinstance(operand, str):
            return operand in value
        if isinstance(value, list):
            if not any(_compatible(item, operand) for item in value):
                raise ValueError("incompatible types")
            return any(_equal(item, operand) for item in value)
        raise ValueError("incompatible types")

    raise ValueError("unknown operator")


def _valid_value(value):
    if value is None or isinstance(value, (str, bool, int)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_valid_value(item) for item in value)
    if isinstance(value, dict):
        return all(
            isinstance(key, str) and _valid_value(item)
            for key, item in value.items()
        )
    return False


def _type_group(value):
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if value is None:
        return "null"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    return None


def _orderable(value):
    return isinstance(value, (str, int, float)) and not isinstance(value, bool)


def _compatible(left, right):
    left_group = _type_group(left)
    right_group = _type_group(right)

    if left_group != right_group:
        return False
    if left_group == "list":
        return len(left) == len(right) and all(
            _compatible(a, b) for a, b in zip(left, right)
        )
    if left_group == "dict":
        return (
            set(left) == set(right)
            and all(_compatible(left[key], right[key]) for key in left)
        )
    return True


def _equal(left, right):
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _equal(a, b) for a, b in zip(left, right)
        )
    if isinstance(left, dict):
        return set(left) == set(right) and all(
            _equal(left[key], right[key]) for key in left
        )
    return left == right