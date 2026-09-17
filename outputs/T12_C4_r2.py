def evaluate_filter(expression, record) -> bool:
    if not isinstance(record, dict):
        raise ValueError("Record must be a dict")
    
    def evaluate(expr, depth):
        if depth > 100:
            raise ValueError("Expression nesting too deep")
        
        if not isinstance(expr, dict):
            raise ValueError("Expression must be a dict")
        
        keys = set(expr.keys())
        
        if keys == {'and'}:
            exprs = expr['and']
            if not isinstance(exprs, list):
                raise ValueError("'and' value must be a list")
            return all(evaluate(e, depth + 1) for e in exprs)
        
        elif keys == {'or'}:
            exprs = expr['or']
            if not isinstance(exprs, list):
                raise ValueError("'or' value must be a list")
            return any(evaluate(e, depth + 1) for e in exprs)
        
        elif keys == {'not'}:
            e = expr['not']
            if not isinstance(e, dict):
                raise ValueError("'not' value must be an expression")
            return not evaluate(e, depth + 1)
        
        elif keys == {'field', 'op', 'value'}:
            field = expr['field']
            op = expr['op']
            value = expr['value']
            
            if not isinstance(field, str):
                raise ValueError("Field name must be a string")
            
            if field not in record:
                raise ValueError(f"Unknown field: {field}")
            
            if not isinstance(op, str):
                raise ValueError("Operator must be a string")
            
            valid_ops = {'eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'in', 'contains'}
            if op not in valid_ops:
                raise ValueError(f"Unknown operator: {op}")
            
            record_value = record[field]
            
            try:
                if op == 'eq':
                    return record_value == value
                elif op == 'ne':
                    return record_value != value
                elif op == 'gt':
                    return record_value > value
                elif op == 'gte':
                    return record_value >= value
                elif op == 'lt':
                    return record_value < value
                elif op == 'lte':
                    return record_value <= value
                elif op == 'in':
                    return record_value in value
                elif op == 'contains':
                    return value in record_value
            except TypeError:
                raise ValueError(f"Invalid operand types for '{op}'")
        
        else:
            raise ValueError("Malformed expression")
    
    return evaluate(expression, 0)
