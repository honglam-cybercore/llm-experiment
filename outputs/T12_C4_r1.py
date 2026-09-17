def evaluate_filter(expression, record) -> bool:
    allowed_fields = set(record.keys())
    max_depth = 10
    
    def evaluate_expression(expr, depth=0):
        if depth > max_depth:
            raise ValueError("Expression nesting exceeds maximum depth")
        
        if not isinstance(expr, dict):
            raise ValueError("Expression must be a dict")
        
        if len(expr) == 0:
            raise ValueError("Expression cannot be empty")
        
        # Handle logical operators
        if "and" in expr:
            if len(expr) != 1:
                raise ValueError("'and' must be the only key in expression")
            if not isinstance(expr["and"], list):
                raise ValueError("'and' value must be a list")
            if len(expr["and"]) == 0:
                raise ValueError("'and' list cannot be empty")
            return all(evaluate_expression(e, depth + 1) for e in expr["and"])
        
        if "or" in expr:
            if len(expr) != 1:
                raise ValueError("'or' must be the only key in expression")
            if not isinstance(expr["or"], list):
                raise ValueError("'or' value must be a list")
            if len(expr["or"]) == 0:
                raise ValueError("'or' list cannot be empty")
            return any(evaluate_expression(e, depth + 1) for e in expr["or"])
        
        if "not" in expr:
            if len(expr) != 1:
                raise ValueError("'not' must be the only key in expression")
            return not evaluate_expression(expr["not"], depth + 1)
        
        # Handle comparison operators
        if "field" in expr and "op" in expr and "value" in expr:
            if len(expr) != 3:
                raise ValueError("Comparison must have exactly 'field', 'op', and 'value' keys")
            
            field = expr["field"]
            op = expr["op"]
            value = expr["value"]
            
            if not isinstance(field, str):
                raise ValueError("Field must be a string")
            
            if not isinstance(op, str):
                raise ValueError("Operator must be a string")
            
            if field not in allowed_fields:
                raise ValueError(f"Unknown field: {field}")
            
            valid_ops = {"eq", "ne", "gt", "gte", "lt", "lte", "in", "contains"}
            if op not in valid_ops:
                raise ValueError(f"Unknown operator: {op}")
            
            record_value = record[field]
            
            # Execute comparison
            if op == "eq":
                return record_value == value
            elif op == "ne":
                return record_value != value
            elif op == "gt":
                try:
                    return record_value > value
                except TypeError:
                    raise ValueError("Invalid operand types for comparison")
            elif op == "gte":
                try:
                    return record_value >= value
                except TypeError:
                    raise ValueError("Invalid operand types for comparison")
            elif op == "lt":
                try:
                    return record_value < value
                except TypeError:
                    raise ValueError("Invalid operand types for comparison")
            elif op == "lte":
                try:
                    return record_value <= value
                except TypeError:
                    raise ValueError("Invalid operand types for comparison")
            elif op == "in":
                try:
                    return record_value in value
                except TypeError:
                    raise ValueError("Invalid operand types for comparison")
            elif op == "contains":
                try:
                    return value in record_value
                except TypeError:
                    raise ValueError("Invalid operand types for comparison")
        
        raise ValueError("Malformed expression")
    
    return evaluate_expression(expression)
