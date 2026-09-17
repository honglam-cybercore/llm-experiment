def evaluate_filter(expression, record) -> bool:
    allowed_fields = set(record.keys())
    max_depth = 10
    
    def _evaluate(expr, depth=0):
        if depth > max_depth:
            raise ValueError("Expression nesting exceeds maximum depth")
        
        if not isinstance(expr, dict):
            raise ValueError("Malformed expression")
        
        if "and" in expr:
            if len(expr) != 1:
                raise ValueError("Malformed expression")
            and_list = expr["and"]
            if not isinstance(and_list, list):
                raise ValueError("Malformed expression")
            return all(_evaluate(e, depth + 1) for e in and_list)
        
        elif "or" in expr:
            if len(expr) != 1:
                raise ValueError("Malformed expression")
            or_list = expr["or"]
            if not isinstance(or_list, list):
                raise ValueError("Malformed expression")
            return any(_evaluate(e, depth + 1) for e in or_list)
        
        elif "not" in expr:
            if len(expr) != 1:
                raise ValueError("Malformed expression")
            return not _evaluate(expr["not"], depth + 1)
        
        elif "field" in expr and "op" in expr and "value" in expr:
            if len(expr) != 3:
                raise ValueError("Malformed expression")
            
            field = expr["field"]
            op = expr["op"]
            value = expr["value"]
            
            if not isinstance(field, str):
                raise ValueError("Malformed expression")
            
            if field not in allowed_fields:
                raise ValueError(f"Unknown field: {field}")
            
            if op not in ["eq", "ne", "gt", "gte", "lt", "lte", "in", "contains"]:
                raise ValueError(f"Unknown operator: {op}")
            
            field_value = record[field]
            
            if op == "in":
                if not isinstance(value, (list, tuple, set)):
                    raise ValueError("Invalid operand types for operator 'in'")
            
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
                raise ValueError("Invalid operand types")
        
        else:
            raise ValueError("Malformed expression")
    
    return _evaluate(expression)
