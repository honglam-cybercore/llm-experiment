from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any


# Set this to an iterable of permitted field names. When left as None, the
# record's keys are treated as the permitted fields.
ALLOWED_FIELDS = None
_MAX_NESTING = 100
_COMPARISON_OPERATORS = frozenset({"eq", "ne", "gt", "gte", "lt", "lte", "in", "contains"})
_LOGICAL_OPERATORS = frozenset({"and", "or", "not"})
_SCALAR_TYPES = (str, int, float, bool, type(None))
_SEQUENCE_TYPES = (list, tuple, set, frozenset)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _compatible(left: Any, right: Any) -> bool:
    if _is_number(left) and _is_number(right):
        return True
    if type(left) is not type(right):
        return False
    return isinstance(left, _SCALAR_TYPES + _SEQUENCE_TYPES + (dict,))


def _validate_value(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("invalid operand value")

    if isinstance(value, _SCALAR_TYPES):
        return

    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("invalid operand type")
            _validate_value(item)
        return

    if isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            _validate_value(item)
        return

    raise ValueError("invalid operand type")


def _allowed_fields(record: Mapping[str, Any]):
    if ALLOWED_FIELDS is None:
        return set(record.keys())
    try:
        return set(ALLOWED_FIELDS)
    except TypeError as exc:
        raise ValueError("invalid allowed field configuration") from exc


def _compare(field_value: Any, operator: str, operand: Any) -> bool:
    if operator in {"eq", "ne"}:
        if not _compatible(field_value, operand):
            raise ValueError("comparison between incompatible types")
        return field_value == operand if operator == "eq" else field_value != operand

    if operator in {"gt", "gte", "lt", "lte"}:
        if not ((_is_number(field_value) and _is_number(operand)) or
                (isinstance(field_value, str) and isinstance(operand, str))):
            raise ValueError("comparison between incompatible types")
        if operator == "gt":
            return field_value > operand
        if operator == "gte":
            return field_value >= operand
        if operator == "lt":
            return field_value < operand
        return field_value <= operand

    if operator == "in":
        if not isinstance(operand, (list, tuple, set, frozenset, str)):
            raise ValueError("invalid operand type")
        if isinstance(operand, str) and not isinstance(field_value, str):
            raise ValueError("comparison between incompatible types")
        if isinstance(operand, (list, tuple, set, frozenset)):
            if not all(_compatible(field_value, item) for item in operand):
                raise ValueError("comparison between incompatible types")
        return field_value in operand

    if operator == "contains":
        if not isinstance(field_value, (list, tuple, set, frozenset, str, dict)):
            raise ValueError("invalid operand type")
        if isinstance(field_value, str) and not isinstance(operand, str):
            raise ValueError("comparison between incompatible types")
        if isinstance(field_value, dict) and not isinstance(operand, str):
            raise ValueError("comparison between incompatible types")
        if isinstance(field_value, (list, tuple, set, frozenset)):
            if not all(_compatible(operand, item) for item in field_value):
                raise ValueError("comparison between incompatible types")
        return operand in field_value

    raise ValueError("unknown operator")


def _evaluate(expression: Any, record: Mapping[str, Any], allowed: set[str], depth: int) -> bool:
    if depth > _MAX_NESTING or not isinstance(expression, dict):
        raise ValueError("malformed expression")

    keys = set(expression)
    if len(keys) != 1:
        if keys != {"field", "op", "value"}:
            raise ValueError("malformed expression")

        field = expression["field"]
        operator = expression["op"]
        if not isinstance(field, str) or field not in allowed:
            raise ValueError("unknown field")
        if not isinstance(operator, str) or operator not in _COMPARISON_OPERATORS:
            raise ValueError("unknown operator")
        if field not in record:
            raise ValueError("unknown field")

        operand = expression["value"]
        _validate_value(operand)
        return _compare(record[field], operator, operand)

    operator = next(iter(keys))
    if operator not in _LOGICAL_OPERATORS:
        raise ValueError("unknown operator")

    if operator in {"and", "or"}:
        operands = expression[operator]
        if not isinstance(operands, list) or not operands:
            raise ValueError("malformed expression")
        results = [_evaluate(item, record, allowed, depth + 1) for item in operands]
        return all(results) if operator == "and" else any(results)

    return not _evaluate(expression["not"], record, allowed, depth + 1)


def evaluate_filter(expression, record) -> bool:
    if not isinstance(record, dict) or any(not isinstance(key, str) for key in record):
        raise ValueError("malformed record")
    allowed = _allowed_fields(record)
    return _evaluate(expression, record, allowed, 0)