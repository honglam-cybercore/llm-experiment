def evaluate_filter(expression, record) -> bool:
    MAX_DEPTH = 10
    
    def is_numeric(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    
    def _evaluate(expr, rec, depth):
        if depth > MAX_DEPTH:
            raise ValueError("Expression nesting too deep")
        
        if not isinstance(expr, dict):
            raise ValueError("Expression must be a dict")
        
        if "and" in expr:
            operands = expr["and"]
            if not isinstance(operands, list):
                raise ValueError("'and' value must be a list")
            if len(operands) == 0:
                raise ValueError("'and' list cannot be empty")
            return all(_evaluate(e, rec, depth + 1) for e in operands)
        
        elif "or" in expr:
            operands = expr["or"]
            if not isinstance(operands, list):
                raise ValueError("'or' value must be a list")
            if len(operands) == 0:
                raise ValueError("'or' list cannot be empty")
            return any(_evaluate(e, rec, depth + 1) for e in operands)
        
        elif "not" in expr:
            operand = expr["not"]
            return not _evaluate(operand, rec, depth + 1)
        
        elif "field" in expr and "op" in expr and "value" in expr:
            field = expr["field"]
            op = expr["op"]
            value = expr["value"]
            
            if not isinstance(field, str):
                raise ValueError("Field must be a string")
            if not isinstance(op, str):
                raise ValueError("Operator must be a string")
            
            if field not in rec:
                raise ValueError(f"Unknown field: {field}")
            
            rec_value = rec[field]
            
            if op == "eq":
                return rec_value == value
            elif op == "ne":
                return rec_value != value
            elif op == "gt":
                if not is_numeric(rec_value) or not is_numeric(value):
                    raise ValueError("Incompatible types for 'gt' operator")
                return rec_value > value
            elif op == "gte":
                if not is_numeric(rec_value) or not is_numeric(value):
                    raise ValueError("Incompatible types for 'gte' operator")
                return rec_value >= value
            elif op == "lt":
                if not is_numeric(rec_value) or not is_numeric(value):
                    raise ValueError("Incompatible types for 'lt' operator")
                return rec_value < value
            elif op == "lte":
                if not is_numeric(rec_value) or not is_numeric(value):
                    raise ValueError("Incompatible types for 'lte' operator")
                return rec_value <= value
            elif op == "in":
                if not isinstance(value, (list, tuple, set, frozenset, dict)):
                    raise ValueError("Incompatible types for 'in' operator")
                return rec_value in value
            elif op == "contains":
                if not isinstance(rec_value, (list, tuple, str, set, frozenset)):
                    raise ValueError("Incompatible types for 'contains' operator")
                return value in rec_value
            else:
                raise ValueError(f"Unknown operator: {op}")
        
        else:
            raise ValueError("Malformed expression")
    
    return _evaluate(expression, record, 0)
