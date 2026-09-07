def evaluate(expression) -> float:
    if not expression or not isinstance(expression, str):
        raise ValueError("Expression cannot be empty")
    
    expression = expression.strip()
    if not expression:
        raise ValueError("Expression cannot be empty")
    
    tokens = _tokenize(expression)
    if not tokens:
        raise ValueError("Expression cannot be empty")
    
    result, pos = _parse_expression(tokens, 0)
    
    if pos != len(tokens):
        raise ValueError("Malformed expression")
    
    return float(result)


def _tokenize(expression):
    tokens = []
    i = 0
    while i < len(expression):
        if expression[i].isspace():
            i += 1
        elif expression[i] in '+-*/()':
            tokens.append(expression[i])
            i += 1
        elif expression[i].isdigit() or expression[i] == '.':
            num_str = ''
            while i < len(expression) and (expression[i].isdigit() or expression[i] == '.'):
                num_str += expression[i]
                i += 1
            try:
                tokens.append(float(num_str))
            except ValueError:
                raise ValueError("Invalid number")
        else:
            raise ValueError("Invalid character")
    return tokens


def _parse_expression(tokens, pos):
    left, pos = _parse_term(tokens, pos)
    
    while pos < len(tokens) and tokens[pos] in ['+', '-']:
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
    
    while pos < len(tokens) and tokens[pos] in ['*', '/']:
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
        raise ValueError("Unexpected end of expression")
    
    token = tokens[pos]
    
    if token == '-':
        pos += 1
        value, pos = _parse_factor(tokens, pos)
        return -value, pos
    
    if token == '+':
        pos += 1
        return _parse_factor(tokens, pos)
    
    if token == '(':
        pos += 1
        value, pos = _parse_expression(tokens, pos)
        if pos >= len(tokens) or tokens[pos] != ')':
            raise ValueError("Unmatched parenthesis")
        pos += 1
        return value, pos
    
    if isinstance(token, (int, float)):
        return token, pos + 1
    
    raise ValueError("Invalid expression")
