def evaluate_filter(expression, record) -> bool:
    if not isinstance(expression, dict):
        raise ValueError("Expression must be a dict")
    
    if not isinstance(record, dict):
        raise ValueError("Record must be a dict")
    
    keys = set(expression.keys())
    
    # Handle logical operators (must be the only key)
    if len(keys) == 1:
        if "and" in expression:
            if not isinstance(expression["and"], list):
                raise ValueError("'and' value must be a list")
            return all(evaluate_filter(expr, record) for expr in expression["and"])
        
        if "or" in expression:
            if not isinstance(expression["or"], list):
                raise ValueError("'or' value must be a list")
            return any(evaluate_filter(expr, record) for expr in expression["or"])
        
        if "not" in expression:
            return not evaluate_filter(expression["not"], record)
    
    # Handle comparison (must have exactly these three keys)
    if keys == {"field", "op", "value"}:
        field = expression["field"]
        op = expression["op"]
        value = expression["value"]
        
        # Validate operator
        valid_ops = {"eq", "ne", "gt", "gte", "lt", "lte", "in", "contains"}
        if op not in valid_ops:
            raise ValueError(f"Unknown operator: {op}")
        
        # Check field exists in record
        if field not in record:
            raise ValueError(f"Unknown field: {field}")
        
        record_value = record[field]
        
        # Perform comparison
        try:
            if op == "eq":
                return record_value == value
            elif op == "ne":
                return record_value != value
            elif op == "gt":
                return record_value > value
            elif op == "gte":
                return record_value >= value
            elif op == "lt":
                return record_value < value
            elif op == "lte":
                return record_value <= value
            elif op == "in":
                return record_value in value
            elif op == "contains":
                return value in record_value
        except TypeError:
            raise ValueError(f"Incompatible types for operator '{op}'")
    
    # Malformed expression
    raise ValueError("Malformed expression")
