def evaluate_filter(expression, record) -> bool:
    if not isinstance(record, dict):
        raise ValueError("record must be a dict")

    def kind(value):
        if value is None:
            return "none"
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return "number"
        if isinstance(value, str):
            return "string"
        if isinstance(value, list):
            return "list"
        if isinstance(value, tuple):
            return "tuple"
        if isinstance(value, (set, frozenset)):
            return "set"
        if isinstance(value, dict):
            return "dict"
        return None

    def compatible(left, right):
        left_kind = kind(left)
        right_kind = kind(right)

        if left_kind is None or right_kind is None:
            return False
        if left_kind == "number" and right_kind == "number":
            return True
        if left_kind != right_kind:
            return False

        if left_kind in {"list", "tuple"}:
            return len(left) == len(right) and all(
                compatible(a, b) for a, b in zip(left, right)
            )
        if left_kind == "dict":
            return len(left) == len(right)
        if left_kind == "set":
            return True
        return True

    def safe_equal(left, right):
        if not compatible(left, right):
            return False

        left_kind = kind(left)
        if left_kind in {"none", "bool", "number", "string"}:
            return left == right
        if left_kind in {"list", "tuple"}:
            return len(left) == len(right) and all(
                safe_equal(a, b) for a, b in zip(left, right)
            )
        if left_kind == "dict":
            if len(left) != len(right):
                return False
            for key, value in left.items():
                if key not in right or not safe_equal(value, right[key]):
                    return False
            return True
        if left_kind == "set":
            return len(left) == len(right) and all(
                any(safe_equal(item, other) for other in right)
                for item in left
            )
        return False

    def contains(container, item):
        container_kind = kind(container)
        if container_kind == "string":
            if kind(item) != "string":
                raise ValueError("incompatible types")
            return item in container

        if container_kind in {"list", "tuple"}:
            return any(safe_equal(element, item) for element in container)

        if container_kind == "set":
            return any(safe_equal(element, item) for element in container)

        if container_kind == "dict":
            return any(safe_equal(key, item) for key in container)

        raise ValueError("incompatible types")

    def parse(node):
        if not isinstance(node, dict):
            raise ValueError("malformed expression")

        keys = set(node.keys())

        if keys == {"field", "op", "value"}:
            field = node["field"]
            operator = node["op"]

            if not isinstance(field, str):
                raise ValueError("malformed expression")
            if field not in record:
                raise ValueError("unknown field")
            if operator not in {
                "eq", "ne", "gt", "gte", "lt", "lte", "in", "contains"
            }:
                raise ValueError("unknown operator")

            return ("comparison", field, operator, node["value"])

        if keys == {"and"}:
            expressions = node["and"]
            if not isinstance(expressions, list):
                raise ValueError("malformed expression")
            return ("and", [parse(item) for item in expressions])

        if keys == {"or"}:
            expressions = node["or"]
            if not isinstance(expressions, list):
                raise ValueError("malformed expression")
            return ("or", [parse(item) for item in expressions])

        if keys == {"not"}:
            return ("not", parse(node["not"]))

        raise ValueError("malformed expression")

    def evaluate(node):
        node_type = node[0]

        if node_type == "and":
            return all(evaluate(item) for item in node[1])
        if node_type == "or":
            return any(evaluate(item) for item in node[1])
        if node_type == "not":
            return not evaluate(node[1])

        _, field, operator, expected = node
        actual = record[field]

        if operator in {"eq", "ne"}:
            if not compatible(actual, expected):
                raise ValueError("incompatible types")
            result = safe_equal(actual, expected)
            return result if operator == "eq" else not result

        if operator in {"gt", "gte", "lt", "lte"}:
            actual_kind = kind(actual)
            expected_kind = kind(expected)

            if actual_kind == "number" and expected_kind == "number":
                pass
            elif actual_kind == "string" and expected_kind == "string":
                pass
            else:
                raise ValueError("incompatible types")

            if operator == "gt":
                return actual > expected
            if operator == "gte":
                return actual >= expected
            if operator == "lt":
                return actual < expected
            return actual <= expected

        if operator == "in":
            return contains(expected, actual)

        return contains(actual, expected)

    return bool(evaluate(parse(expression)))