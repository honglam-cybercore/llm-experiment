def evaluate(expression) -> float:
    if not isinstance(expression, str) or not expression:
        raise ValueError("Expression cannot be empty")
    
    expression = expression.replace(" ", "")
    
    if not expression:
        raise ValueError("Expression cannot be empty")
    
    tokens = _tokenize(expression)
    result, pos = _parse_expression(tokens, 0)
    
    if pos != len(tokens):
        raise ValueError("Malformed expression")
    
    return result


def _tokenize(expression: str):
    tokens = []
    i = 0
    while i < len(expression):
        if expression[i] in "+-*/()":
            tokens.append(expression[i])
            i += 1
        elif expression[i].isdigit() or expression[i] == '.':
            j = i
            while j < len(expression) and (expression[j].isdigit() or expression[j] == '.'):
                j += 1
            tokens.append(expression[i:j])
            i = j
        else:
            raise ValueError("Invalid character in expression")
    return tokens


def _parse_expression(tokens, pos):
    left, pos = _parse_term(tokens, pos)
    while pos < len(tokens) and tokens[pos] in "+-":
        op = tokens[pos]
        pos += 1
        right, pos = _parse_term(tokens, pos)
        if op == '+':
            left = left + right
        else:
            left = left - right
    return left, pos


def _parse_term(tokens, pos):
    left, pos = _parse_factor(tokens, pos)
    while pos < len(tokens) and tokens[pos] in "*/":
        op = tokens[pos]
        pos += 1
        right, pos = _parse_factor(tokens, pos)
        if op == '*':
            left = left * right
        else:
            if right == 0:
                raise ValueError("Division by zero")
            left = left / right
    return left, pos


def _parse_factor(tokens, pos):
    if pos >= len(tokens):
        raise ValueError("Malformed expression")
    
    if tokens[pos] == '(':
        pos += 1
        result, pos = _parse_expression(tokens, pos)
        if pos >= len(tokens) or tokens[pos] != ')':
            raise ValueError("Malformed expression")
        pos += 1
        return result, pos
    elif tokens[pos] == '-':
        pos += 1
        result, pos = _parse_factor(tokens, pos)
        return -result, pos
    elif tokens[pos] == '+':
        pos += 1
        result, pos = _parse_factor(tokens, pos)
        return result, pos
    else:
        return _parse_atom(tokens, pos)


def _parse_atom(tokens, pos):
    if pos >= len(tokens):
        raise ValueError("Malformed expression")
    
    token = tokens[pos]
    
    try:
        return float(token), pos + 1
    except ValueError:
        raise ValueError("Malformed expression")
