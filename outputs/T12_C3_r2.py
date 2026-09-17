def evaluate_filter(expression, record) -> bool:
    if not isinstance(expression, dict):
        raise ValueError("Expression must be a dict")
    
    if not isinstance(record, dict):
        raise ValueError("Record must be a dict")
    
    has_and = "and" in expression
    has_or = "or" in expression
    has_not = "not" in expression
    has_field = "field" in expression
    
    logical_ops = sum([has_and, has_or, has_not])
    
    if logical_ops > 1:
        raise ValueError("Expression cannot have multiple logical operators")
    
    if logical_ops > 0 and has_field:
        raise ValueError("Expression cannot mix logical and comparison operators")
    
    if has_and:
        if not isinstance(expression["and"], list):
            raise ValueError("'and' value must be a list")
        return all(evaluate_filter(e, record) for e in expression["and"])
    
    if has_or:
        if not isinstance(expression["or"], list):
            raise ValueError("'or' value must be a list")
        return any(evaluate_filter(e, record) for e in expression["or"])
    
    if has_not:
        if not isinstance(expression["not"], dict):
            raise ValueError("'not' value must be a dict")
        return not evaluate_filter(expression["not"], record)
    
    if has_field:
        if "op" not in expression or "value" not in expression:
            raise ValueError("Comparison must have 'field', 'op', and 'value'")
        
        field = expression["field"]
        op = expression["op"]
        value = expression["value"]
        
        if not isinstance(field, str):
            raise ValueError("Field name must be a string")
        
        if field not in record:
            raise ValueError(f"Unknown field: {field}")
        
        if op not in ["eq", "ne", "gt", "gte", "lt", "lte", "in", "contains"]:
            raise ValueError(f"Unknown operator: {op}")
        
        record_value = record[field]
        
        if op == "eq":
            return record_value == value
        elif op == "ne":
            return record_value != value
        elif op in ["gt", "gte", "lt", "lte"]:
            try:
                if op == "gt":
                    return record_value > value
                elif op == "gte":
                    return record_value >= value
                elif op == "lt":
                    return record_value < value
                else:
                    return record_value <= value
            except TypeError:
                raise ValueError(f"Cannot compare {type(record_value).__name__} with {type(value).__name__}")
        elif op == "in":
            if not isinstance(value, (list, tuple, set)):
                raise ValueError("'in' operator requires value to be a list, tuple, or set")
            return record_value in value
        elif op == "contains":
            if isinstance(record_value, str):
                if not isinstance(value, str):
                    raise ValueError(f"Cannot check if string contains {type(value).__name__}")
                return value in record_value
            elif isinstance(record_value, (list, tuple)):
                return value in record_value
            elif isinstance(record_value, dict):
                return value in record_value
            else:
                raise ValueError(f"'contains' not supported for {type(record_value).__name__}")
    
    raise ValueError("Expression must contain 'field', 'and', 'or', or 'not'")
