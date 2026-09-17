import math


_MAX_DEPTH = 100


def evaluate_filter(expression, record) -> bool:
    if type(record) is not dict:
        raise ValueError("malformed record")
    if any(type(key) is not str for key in record):
        raise ValueError("malformed record")
    return _evaluate(expression, record, 0, set())


def _evaluate(expression, record, depth, active):
    if depth > _MAX_DEPTH or type(expression) is not dict:
        raise ValueError("malformed expression")

    identity = id(expression)
    if identity in active:
        raise ValueError("malformed expression")
    active.add(identity)

    try:
        keys = set(expression)
        logical_keys = keys & {"and", "or", "not"}

        if logical_keys:
            if len(expression) != 1:
                raise ValueError("malformed expression")

            if "not" in expression:
                return not _evaluate(expression["not"], record, depth + 1, active)

            value = expression[next(iter(logical_keys))]
            if type(value) is not list or not value:
                raise ValueError("malformed expression")

            if "and" in expression:
                return all(
                    _evaluate(item, record, depth + 1, active)
                    for item in value
                )
            return any(
                _evaluate(item, record, depth + 1, active)
                for item in value
            )

        required = {"field", "op", "value"}
        if keys != required:
            raise ValueError("malformed expression")

        field = expression["field"]
        operator = expression["op"]

        if type(field) is not str or field not in record:
            raise ValueError("unknown field")
        if type(operator) is not str:
            raise ValueError("unknown operator")

        allowed = {"eq", "ne", "gt", "gte", "lt", "lte", "in", "contains"}
        if operator not in allowed:
            raise ValueError("unknown operator")

        left = record[field]
        right = expression["value"]
        _validate_value(left, 0, set())
        _validate_value(right, 0, set())

        if operator in {"eq", "ne"}:
            compatible = _compatible(left, right)
            if not compatible:
                raise ValueError("incompatible types")
            result = _safe_equal(left, right)
            return result if operator == "eq" else not result

        if operator in {"gt", "gte", "lt", "lte"}:
            if not _scalar_comparable(left, right):
                raise ValueError("incompatible types")
            try:
                if operator == "gt":
                    return left > right
                if operator == "gte":
                    return left >= right
                if operator == "lt":
                    return left < right
                return left <= right
            except (TypeError, ValueError, ArithmeticError):
                raise ValueError("incompatible types")

        if operator == "in":
            if not _is_collection(right) or not all(
                _compatible(left, item) for item in right
            ):
                raise ValueError("incompatible types")
            return any(_safe_equal(left, item) for item in right)

        if not _is_collection(left) and type(left) is not str:
            raise ValueError("incompatible types")

        if type(left) is str:
            if type(right) is not str:
                raise ValueError("incompatible types")
            return right in left

        if not all(_compatible(right, item) for item in left):
            raise ValueError("incompatible types")
        return any(_safe_equal(right, item) for item in left)
    finally:
        active.remove(identity)


def _validate_value(value, depth, active):
    if depth > _MAX_DEPTH:
        raise ValueError("malformed expression")

    value_type = type(value)
    if value is None or value_type is bool or value_type is str:
        return
    if value_type is int:
        return
    if value_type is float:
        if not math.isfinite(value):
            raise ValueError("malformed expression")
        return

    if value_type in (list, tuple, set, frozenset):
        identity = id(value)
        if identity in active:
            raise ValueError("malformed expression")
        active.add(identity)
        try:
            for item in value:
                _validate_value(item, depth + 1, active)
        finally:
            active.remove(identity)
        return

    if value_type is dict:
        identity = id(value)
        if identity in active:
            raise ValueError("malformed expression")
        active.add(identity)
        try:
            for key, item in value.items():
                if type(key) is not str:
                    raise ValueError("malformed expression")
                _validate_value(item, depth + 1, active)
        finally:
            active.remove(identity)
        return

    raise ValueError("malformed expression")


def _is_collection(value):
    return type(value) in (list, tuple, set, frozenset)


def _scalar_kind(value):
    value_type = type(value)
    if value is None:
        return "none"
    if value_type is bool:
        return "bool"
    if value_type in (int, float):
        return "number"
    if value_type is str:
        return "str"
    return None


def _scalar_comparable(left, right):
    left_kind = _scalar_kind(left)
    right_kind = _scalar_kind(right)
    return (
        left_kind is not None
        and right_kind is not None
        and left_kind == right_kind
        and left_kind in {"number", "str"}
    )


def _compatible(left, right):
    left_kind = _scalar_kind(left)
    right_kind = _scalar_kind(right)

    if left_kind is not None or right_kind is not None:
        return left_kind == right_kind

    if _is_collection(left) and _is_collection(right):
        left_items = list(left)
        right_items = list(right)
        return len(left_items) == len(right_items) and all(
            _compatible(a, b) for a, b in zip(left_items, right_items)
        )

    if type(left) is dict and type(right) is dict:
        if set(left) != set(right):
            return False
        return all(_compatible(left[key], right[key]) for key in left)

    return False


def _safe_equal(left, right):
    try:
        return bool(left == right)
    except (TypeError, ValueError, ArithmeticError):
        raise ValueError("incompatible types")