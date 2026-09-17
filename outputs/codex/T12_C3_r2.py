def evaluate_filter(expression, record) -> bool:
    if type(record) is not dict:
        raise ValueError("record must be a dict")

    max_depth = 100

    def validate_value(value, active, depth):
        if depth > max_depth:
            raise ValueError("value nesting is too deep")

        value_type = type(value)

        if value_type in (type(None), bool, int, float, str):
            return

        if value_type in (list, tuple, set, frozenset):
            identity = id(value)
            if identity in active:
                raise ValueError("cyclic value")
            active.add(identity)
            try:
                for item in value:
                    validate_value(item, active, depth + 1)
            finally:
                active.remove(identity)
            return

        if value_type is dict:
            identity = id(value)
            if identity in active:
                raise ValueError("cyclic value")
            active.add(identity)
            try:
                for key, item in value.items():
                    if type(key) is not str:
                        raise ValueError("dictionary keys must be strings")
                    validate_value(item, active, depth + 1)
            finally:
                active.remove(identity)
            return

        raise ValueError("unsupported value type")

    def compatible(left, right):
        left_type = type(left)
        right_type = type(right)

        if left_type in (int, float) and left_type is not bool:
            return right_type in (int, float) and right_type is not bool

        if left_type != right_type:
            return False

        if left_type in (list, tuple):
            if len(left) != len(right):
                return True
            return all(compatible(a, b) for a, b in zip(left, right))

        if left_type in (set, frozenset):
            return True

        if left_type is dict:
            if set(left.keys()) != set(right.keys()):
                return True
            return all(compatible(left[key], right[key]) for key in left)

        return True

    def compile_expression(node, depth=0, active=None):
        if active is None:
            active = set()

        if depth > max_depth or type(node) is not dict:
            raise ValueError("malformed expression")

        identity = id(node)
        if identity in active:
            raise ValueError("cyclic expression")
        active.add(identity)

        try:
            keys = set(node.keys())

            if "field" in keys:
                if keys != {"field", "op", "value"}:
                    raise ValueError("malformed comparison")

                field = node["field"]
                operator = node["op"]
                value = node["value"]

                if type(field) is not str or field not in record:
                    raise ValueError("unknown field")
                if type(operator) is not str:
                    raise ValueError("unknown operator")

                allowed = {"eq", "ne", "gt", "gte", "lt", "lte", "in", "contains"}
                if operator not in allowed:
                    raise ValueError("unknown operator")

                validate_value(value, set(), 0)
                record_value = record[field]
                validate_value(record_value, set(), 0)

                if operator in {"eq", "ne"}:
                    if not compatible(record_value, value):
                        raise ValueError("incompatible types")
                elif operator in {"gt", "gte", "lt", "lte"}:
                    scalar_types = (int, float, str)
                    if (
                        type(record_value) is bool
                        or type(value) is bool
                        or type(record_value) not in scalar_types
                        or type(value) not in scalar_types
                        or not compatible(record_value, value)
                    ):
                        raise ValueError("incompatible types")
                elif operator == "in":
                    if type(value) not in (list, tuple, set, frozenset, str):
                        raise ValueError("incompatible types")
                    if any(not compatible(record_value, item) for item in value):
                        raise ValueError("incompatible types")
                elif operator == "contains":
                    if type(record_value) not in (list, tuple, set, frozenset, str):
                        raise ValueError("incompatible types")
                    if type(record_value) is str and type(value) is not str:
                        raise ValueError("incompatible types")
                    if type(record_value) is not str and any(
                        not compatible(item, value) for item in record_value
                    ):
                        raise ValueError("incompatible types")

                return ("comparison", record_value, operator, value)

            if len(keys) != 1:
                raise ValueError("malformed logical expression")

            operator = next(iter(keys))

            if operator in {"and", "or"}:
                operands = node[operator]
                if type(operands) is not list or not operands:
                    raise ValueError("malformed logical expression")
                return (
                    operator,
                    [
                        compile_expression(item, depth + 1, active)
                        for item in operands
                    ],
                )

            if operator == "not":
                return ("not", compile_expression(node["not"], depth + 1, active))

            raise ValueError("malformed expression")
        finally:
            active.remove(identity)

    def evaluate(compiled):
        kind = compiled[0]

        if kind == "comparison":
            _, left, operator, right = compiled
            if operator == "eq":
                return left == right
            if operator == "ne":
                return left != right
            if operator == "gt":
                return left > right
            if operator == "gte":
                return left >= right
            if operator == "lt":
                return left < right
            if operator == "lte":
                return left <= right
            if operator == "in":
                return left in right
            return right in left

        if kind == "and":
            return all(evaluate(item) for item in compiled[1])

        if kind == "or":
            return any(evaluate(item) for item in compiled[1])

        return not evaluate(compiled[1])

    return bool(evaluate(compile_expression(expression)))