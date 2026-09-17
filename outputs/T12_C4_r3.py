def evaluate_filter(expression, record) -> bool:
    MAX_DEPTH = 20
    
    def _evaluate(expr, depth=0):
        if depth > MAX_DEPTH:
            raise ValueError(f"Expression nesting exceeds maximum depth of {MAX_DEPTH}")
        
        if not isinstance(expr, dict):
            raise ValueError("Expression must be a dict")
        
        if not expr:
            raise ValueError("Expression cannot be empty")
        
        keys = set(expr.keys())
        logical_keys = {"and", "or", "not"}
        logical_in_expr = keys & logical_keys
        
        if logical_in_expr:
            if len(expr) != 1:
                raise ValueError("Logical operator expression must have exactly one key")
            
            op = list(logical_in_expr)[0]
            
            if op == "not":
                if not isinstance(expr["not"], dict):
                    raise ValueError("'not' operator must have a dict value")
                return not _evaluate(expr["not"], depth + 1)
            else:
                if not isinstance(expr[op], list):
                    raise ValueError(f"'{op}' operator must have a list value")
                if not expr[op]:
                    raise ValueError(f"'{op}' operator list cannot be empty")
                
                if op == "and":
                    return all(_evaluate(sub_expr, depth + 1) for sub_expr in expr[op])
                else:
                    return any(_evaluate(sub_expr, depth + 1) for sub_expr in expr[op])
        
        required_keys = {"field", "op", "value"}
        if not required_keys.issubset(keys):
            raise ValueError("Comparison expression must have 'field', 'op', and 'value' keys")
        
        if len(expr) != 3:
            raise ValueError("Comparison expression must have exactly 'field', 'op', and 'value' keys")
        
        field = expr["field"]
        op = expr["op"]
        value = expr["value"]
        
        if not isinstance(field, str):
            raise ValueError("Field name must be a string")
        
        if field not in record:
            raise ValueError(f"Unknown field: {field}")
        
        valid_operators = {"eq", "ne", "gt", "gte", "lt", "lte", "in", "contains"}
        if op not in valid_operators:
            raise ValueError(f"Unknown operator: {op}")
        
        field_value = record[field]
        
        try:
            if op == "eq":
                return field_value == value
            elif op == "ne":
                return field_value != value
            elif op == "gt":
                return field_value > value
            elif op == "gte":
                return field_value >= value
            elif op == "lt":
                return field_value < value
            elif op == "lte":
                return field_value <= value
            elif op == "in":
                return field_value in value
            elif op == "contains":
                return value in field_value
        except TypeError:
            raise ValueError(f"Incompatible types for operator '{op}'")
    
    return _evaluate(expression)
