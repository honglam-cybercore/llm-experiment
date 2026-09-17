def evaluate_filter(expression, record):
    if not isinstance(expression, dict):
        raise ValueError("Expression must be a dict")
    
    # Check for logical operators - they should be the only key
    if "and" in expression:
        if len(expression) != 1:
            raise ValueError("Malformed expression")
        and_expr = expression["and"]
        if not isinstance(and_expr, list):
            raise ValueError("Malformed expression")
        return all(evaluate_filter(e, record) for e in and_expr)
    
    if "or" in expression:
        if len(expression) != 1:
            raise ValueError("Malformed expression")
        or_expr = expression["or"]
        if not isinstance(or_expr, list):
            raise ValueError("Malformed expression")
        return any(evaluate_filter(e, record) for e in or_expr)
    
    if "not" in expression:
        if len(expression) != 1:
            raise ValueError("Malformed expression")
        return not evaluate_filter(expression["not"], record)
    
    # Check for comparison
    if "field" in expression or "op" in expression or "value" in expression:
        # Must have all three
        if not ("field" in expression and "op" in expression and "value" in expression):
            raise ValueError("Malformed expression")
        if len(expression) != 3:
            raise ValueError("Malformed expression")
        
        field = expression["field"]
        op = expression["op"]
        value = expression["value"]
        
        # Check if field exists in record
        if field not in record:
            raise ValueError("Unknown field")
        
        # Check if operator is valid
        if op not in ["eq", "ne", "gt", "gte", "lt", "lte", "in", "contains"]:
            raise ValueError("Unknown operator")
        
        record_value = record[field]
        
        # Perform comparison
        if op == "eq":
            return record_value == value
        elif op == "ne":
            return record_value != value
        elif op == "gt":
            try:
                return record_value > value
            except TypeError:
                raise ValueError("Comparison between incompatible types")
        elif op == "gte":
            try:
                return record_value >= value
            except TypeError:
                raise ValueError("Comparison between incompatible types")
        elif op == "lt":
            try:
                return record_value < value
            except TypeError:
                raise ValueError("Comparison between incompatible types")
        elif op == "lte":
            try:
                return record_value <= value
            except TypeError:
                raise ValueError("Comparison between incompatible types")
        elif op == "in":
            try:
                return record_value in value
            except TypeError:
                raise ValueError("Comparison between incompatible types")
        elif op == "contains":
            try:
                return value in record_value
            except TypeError:
                raise ValueError("Comparison between incompatible types")
    
    # If we get here, expression is malformed
    raise ValueError("Malformed expression")
