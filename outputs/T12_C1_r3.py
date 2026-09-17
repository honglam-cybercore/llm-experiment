def evaluate_filter(expression, record) -> bool:
    if not isinstance(expression, dict):
        raise ValueError("Expression must be a dict")
    
    if "field" in expression:
        if not ("op" in expression and "value" in expression):
            raise ValueError("Comparison expression must have 'field', 'op', and 'value'")
        return _evaluate_comparison(expression, record)
    elif "and" in expression:
        return _evaluate_and(expression, record)
    elif "or" in expression:
        return _evaluate_or(expression, record)
    elif "not" in expression:
        return _evaluate_not(expression, record)
    else:
        raise ValueError("Invalid expression format")


def _evaluate_comparison(expr, record):
    field = expr["field"]
    op = expr["op"]
    value = expr["value"]
    
    if field not in record:
        raise ValueError(f"Unknown field: {field}")
    
    field_value = record[field]
    
    valid_ops = {"eq", "ne", "gt", "gte", "lt", "lte", "in", "contains"}
    if op not in valid_ops:
        raise ValueError(f"Unknown operator: {op}")
    
    if op == "eq":
        return field_value == value
    elif op == "ne":
        return field_value != value
    elif op in ("gt", "gte", "lt", "lte"):
        try:
            if op == "gt":
                return field_value > value
            elif op == "gte":
                return field_value >= value
            elif op == "lt":
                return field_value < value
            elif op == "lte":
                return field_value <= value
        except TypeError:
            raise ValueError("Comparison between incompatible types")
    elif op == "in":
        if not isinstance(value, (list, tuple, set)):
            raise ValueError("'in' operator requires a list/tuple/set value")
        return field_value in value
    elif op == "contains":
        if isinstance(field_value, str) and isinstance(value, str):
            return value in field_value
        elif isinstance(field_value, (list, tuple, set)):
            return value in field_value
        else:
            raise ValueError("Comparison between incompatible types")


def _evaluate_and(expr, record):
    exprs = expr["and"]
    if not isinstance(exprs, list):
        raise ValueError("'and' value must be a list")
    
    for e in exprs:
        if not evaluate_filter(e, record):
            return False
    return True


def _evaluate_or(expr, record):
    exprs = expr["or"]
    if not isinstance(exprs, list):
        raise ValueError("'or' value must be a list")
    
    for e in exprs:
        if evaluate_filter(e, record):
            return True
    return False


def _evaluate_not(expr, record):
    inner_expr = expr["not"]
    return not evaluate_filter(inner_expr, record)
