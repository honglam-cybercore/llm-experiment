from numbers import Real


def evaluate_filter(expression, record) -> bool:
    if type(record) is not dict:
        raise ValueError("Malformed record")

    def is_number(value):
        return isinstance(value, Real) and not isinstance(value, bool)

    def is_scalar(value):
        return value is None or type(value) in (str, bool, int, float)

    def compatible(left, right):
        if is_number(left) and is_number(right):
            return True
        if type(left) is type(right) and is_scalar(left):
            return True
        return False

    def validate_value(value):
        if is_scalar(value):
            return
        if type(value) in (list, tuple, set, frozenset):
            for item in value:
                if not is_scalar(item):
                    raise ValueError("Incompatible value type")
            return
        raise ValueError("Incompatible value type")

    def compare(left, operator, right):
        validate_value(left)
        validate_value(right)

        if operator in ("eq", "ne"):
            if not compatible(left, right):
                raise ValueError("Incompatible comparison types")
            result = (left == right)
            return result if operator == "eq" else not result

        if operator in ("gt", "gte", "lt", "lte"):
            if not compatible(left, right):
                raise ValueError("Incompatible comparison types")
            try:
                if operator == "gt":
                    return left > right
                if operator == "gte":
                    return left >= right
                if operator == "lt":
                    return left < right
                return left <= right
            except (TypeError, ValueError):
                raise ValueError("Incompatible comparison types")

        if operator == "in":
            if type(right) not in (list, tuple, set, frozenset):
                raise ValueError("Incompatible comparison types")
            for item in right:
                if not compatible(left, item):
                    raise ValueError("Incompatible comparison types")
            return any(left == item for item in right)

        if operator == "contains":
            if type(left) is str:
                if type(right) is not str:
                    raise ValueError("Incompatible comparison types")
                return right in left
            if type(left) in (list, tuple, set, frozenset):
                if not is_scalar(right):
                    raise ValueError("Incompatible comparison types")
                for item in left:
                    if not compatible(item, right):
                        raise ValueError("Incompatible comparison types")
                return any(item == right for item in left)
            raise ValueError("Incompatible comparison types")

        raise ValueError("Unknown operator")

    def evaluate(node):
        if type(node) is not dict:
            raise ValueError("Malformed expression")

        keys = set(node)

        if "and" in node or "or" in node:
            if len(keys) != 1:
                raise ValueError("Malformed expression")
            operator = next(iter(keys))
            expressions = node[operator]
            if type(expressions) is not list:
                raise ValueError("Malformed expression")
            results = [evaluate(item) for item in expressions]
            return all(results) if operator == "and" else any(results)

        if "not" in node:
            if len(keys) != 1:
                raise ValueError("Malformed expression")
            return not evaluate(node["not"])

        required = {"field", "op", "value"}
        if keys != required:
            raise ValueError("Malformed expression")

        field = node["field"]
        operator = node["op"]
        value = node["value"]

        if type(field) is not str or field not in record:
            raise ValueError("Unknown field")
        if type(operator) is not str:
            raise ValueError("Unknown operator")

        validate_value(value)
        return compare(record[field], operator, value)

    return bool(evaluate(expression))