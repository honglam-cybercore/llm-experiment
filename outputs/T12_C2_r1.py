MAX_DEPTH = 10

def evaluate_filter(expression, record) -> bool:
    allowed_fields = set(record.keys())
    return _evaluate(expression, record, allowed_fields, 0)

def _evaluate(expression, record, allowed_fields, depth):
    if depth > MAX_DEPTH:
        raise ValueError("Expression nesting exceeds maximum allowed depth")
    
    if not isinstance(expression, dict):
        raise ValueError("Expression must be a dict")
    
    if not expression:
        raise ValueError("Expression dict cannot be empty")
    
    if "and" in expression:
        if len(expression) != 1:
            raise ValueError("Expression with 'and' must only contain that key")
        if not isinstance(expression["and"], list):
            raise ValueError("'and' value must be a list")
        return all(_evaluate(expr, record, allowed_fields, depth + 1) 
                   for expr in expression["and"])
    
    elif "or" in expression:
        if len(expression) != 1:
            raise ValueError("Expression with 'or' must only contain that key")
        if not isinstance(expression["or"], list):
            raise ValueError("'or' value must be a list")
        return any(_evaluate(expr, record, allowed_fields, depth + 1) 
                   for expr in expression["or"])
    
    elif "not" in expression:
        if len(expression) != 1:
            raise ValueError("Expression with 'not' must only contain that key")
        return not _evaluate(expression["not"], record, allowed_fields, depth + 1)
    
    elif "field" in expression and "op" in expression and "value" in expression:
        if len(expression) != 3:
            raise ValueError("Comparison expression must have exactly 'field', 'op', and 'value'")
        
        field = expression["field"]
        op = expression["op"]
        value = expression["value"]
        
        if not isinstance(field, str):
            raise ValueError("Field name must be a string")
        
        if field not in allowed_fields:
            raise ValueError(f"Unknown field: {field}")
        
        if op not in ["eq", "ne", "gt", "gte", "lt", "lte", "in", "contains"]:
            raise ValueError(f"Unknown operator: {op}")
        
        record_value = record[field]
        
        if op == "eq":
            return record_value == value
        elif op == "ne":
            return record_value != value
        elif op == "gt":
            try:
                return record_value > value
            except TypeError:
                raise ValueError("Cannot compare incompatible types")
        elif op == "gte":
            try:
                return record_value >= value
            except TypeError:
                raise ValueError("Cannot compare incompatible types")
        elif op == "lt":
            try:
                return record_value < value
            except TypeError:
                raise ValueError("Cannot compare incompatible types")
        elif op == "lte":
            try:
                return record_value <= value
            except TypeError:
                raise ValueError("Cannot compare incompatible types")
        elif op == "in":
            if not isinstance(value, (list, tuple, set)):
                raise ValueError("'in' operator requires value to be a list, tuple, or set")
            try:
                return record_value in value
            except TypeError:
                raise ValueError("Cannot apply 'in' operator: incompatible value type")
        elif op == "contains":
            if not isinstance(record_value, (list, tuple, set, str)):
                raise ValueError("'contains' operator requires record value to be a collection or string")
            try:
                return value in record_value
            except TypeError:
                raise ValueError("Cannot apply 'contains' operator: incompatible value type")
    
    else:
        raise ValueError("Expression must be a comparison or logical expression")
