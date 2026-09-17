ALLOWED_FIELDS = None
MAX_NESTING = 100

_COMPARISON_OPERATORS = {"eq", "ne", "gt", "gte", "lt", "lte", "in", "contains"}
_LOGICAL_OPERATORS = {"and", "or", "not"}


def evaluate_filter(expression, record) -> bool:
    if not isinstance(record, dict):
        raise ValueError("record must be a dict")

    active = set()

    def validate_field(field):
        if not isinstance(field, str):
            raise ValueError("field name must be a string")
        if ALLOWED_FIELDS is not None:
            try:
                allowed = field in ALLOWED_FIELDS
            except TypeError:
                raise ValueError("invalid allowed field configuration")
        else:
            allowed = field in record
        if not allowed:
            raise ValueError("unknown field")

    def compatible(left, right):
        if isinstance(left, bool) or isinstance(right, bool):
            return type(left) is type(right)
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return True
        return type(left) is type(right)

    def compare(expr):
        if set(expr) != {"field", "op", "value"}:
            raise ValueError("malformed comparison")

        field = expr["field"]
        op = expr["op"]
        value = expr["value"]

        validate_field(field)

        if not isinstance(op, str) or op not in _COMPARISON_OPERATORS:
            raise ValueError("unknown operator")

        if field not in record:
            raise ValueError("unknown field")

        current = record[field]

        if op in {"eq", "ne"}:
            if not compatible(current, value):
                raise ValueError("incompatible types")
            return current == value if op == "eq" else current != value

        if op in {"gt", "gte", "lt", "lte"}:
            if not compatible(current, value):
                raise ValueError("incompatible types")
            if not (
                isinstance(current, (int, float, str))
                and not isinstance(current, bool)
            ):
                raise ValueError("incompatible types")
            if op == "gt":
                return current > value
            if op == "gte":
                return current >= value
            if op == "lt":
                return current < value
            return current <= value

        if op == "in":
            if not isinstance(value, (list, tuple, set, frozenset)):
                raise ValueError("in requires a collection")
            for item in value:
                if not compatible(current, item):
                    raise ValueError("incompatible types")
            return current in value

        if op == "contains":
            if not isinstance(current, (str, list, tuple, set, frozenset)):
                raise ValueError("contains requires a container")
            if isinstance(current, str):
                if not isinstance(value, str):
                    raise ValueError("incompatible types")
            else:
                for item in current:
                    if not compatible(item, value):
                        raise ValueError("incompatible types")
            return value in current

        raise ValueError("unknown operator")

    def evaluate(node, depth):
        if depth > MAX_NESTING:
            raise ValueError("excessive nesting")
        if not isinstance(node, dict) or not node:
            raise ValueError("malformed expression")

        identity = id(node)
        if identity in active:
            raise ValueError("cyclic expression")

        active.add(identity)
        try:
            keys = set(node)

            if keys & _LOGICAL_OPERATORS:
                if len(keys) != 1:
                    raise ValueError("malformed expression")

                operator = next(iter(keys))
                operand = node[operator]

                if operator == "not":
                    if not isinstance(operand, dict):
                        raise ValueError("malformed expression")
                    return not evaluate(operand, depth + 1)

                if (
                    not isinstance(operand, list)
                    or not operand
                    or any(not isinstance(item, dict) for item in operand)
                ):
                    raise ValueError("malformed expression")

                results = [evaluate(item, depth + 1) for item in operand]
                return all(results) if operator == "and" else any(results)

            if keys == {"field", "op", "value"}:
                return bool(compare(node))

            raise ValueError("malformed expression")
        finally:
            active.remove(identity)

    return bool(evaluate(expression, 0))