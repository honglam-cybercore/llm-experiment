def evaluate_filter(expression, record) -> bool:
    if not isinstance(expression, dict):
        raise ValueError("Expression must be a dictionary")
    
    if not expression:
        raise ValueError("Expression cannot be empty")
    
    if "and" in expression:
        if len(expression) != 1:
            raise ValueError("'and' expression must have exactly one key")
        conditions = expression["and"]
        if not isinstance(conditions, list):
            raise ValueError("'and' value must be a list")
        return all(evaluate_filter(cond, record) for cond in conditions)
    
    if "or" in expression:
        if len(expression) != 1:
            raise ValueError("'or' expression must have exactly one key")
        conditions = expression["or"]
        if not isinstance(conditions, list):
            raise ValueError("'or' value must be a list")
        return any(evaluate_filter(cond, record) for cond in conditions)
    
    if "not" in expression:
        if len(expression) != 1:
            raise ValueError("'not' expression must have exactly one key")
        return not evaluate_filter(expression["not"], record)
    
    if "field" in expression and "op" in expression and "value" in expression:
        if len(expression) != 3:
            raise ValueError("Comparison expression must have exactly 3 keys")
        
        field = expression["field"]
        op = expression["op"]
        value = expression["value"]
        
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
        elif op == "gt":
            try:
                return field_value > value
            except TypeError:
                raise ValueError("Incompatible types for comparison")
        elif op == "gte":
            try:
                return field_value >= value
            except TypeError:
                raise ValueError("Incompatible types for comparison")
        elif op == "lt":
            try:
                return field_value < value
            except TypeError:
                raise ValueError("Incompatible types for comparison")
        elif op == "lte":
            try:
                return field_value <= value
            except TypeError:
                raise ValueError("Incompatible types for comparison")
        elif op == "in":
            try:
                return field_value in value
            except TypeError:
                raise ValueError("Value must be iterable for 'in' operator")
        elif op == "contains":
            try:
                return value in field_value
            except TypeError:
                raise ValueError("Field value must support 'in' operator for 'contains'")
    
    raise ValueError("Malformed expression")
