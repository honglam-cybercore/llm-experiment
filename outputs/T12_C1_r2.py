def evaluate_filter(expression, record) -> bool:
    if not isinstance(expression, dict):
        raise ValueError("Expression must be a dict")
    
    # Handle logical operations
    if "and" in expression:
        if not isinstance(expression["and"], list):
            raise ValueError("Malformed expression")
        return all(evaluate_filter(expr, record) for expr in expression["and"])
    
    if "or" in expression:
        if not isinstance(expression["or"], list):
            raise ValueError("Malformed expression")
        return any(evaluate_filter(expr, record) for expr in expression["or"])
    
    if "not" in expression:
        sub_expr = expression["not"]
        if not isinstance(sub_expr, dict):
            raise ValueError("Malformed expression")
        return not evaluate_filter(sub_expr, record)
    
    # Handle comparison
    if "field" in expression and "op" in expression and "value" in expression:
        field = expression["field"]
        op = expression["op"]
        value = expression["value"]
        
        if not isinstance(field, str):
            raise ValueError("Malformed expression")
        
        # Check if field exists in record
        if field not in record:
            raise ValueError(f"Unknown field: {field}")
        
        field_value = record[field]
        
        # Define operators
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
                raise ValueError("Incompatible types for comparison")
        elif op == "contains":
            try:
                return value in field_value
            except TypeError:
                raise ValueError("Incompatible types for comparison")
        else:
            raise ValueError(f"Unknown operator: {op}")
    else:
        raise ValueError("Malformed expression")
