def evaluate(expression) -> float:
    if not isinstance(expression, str):
        raise ValueError("Expression must be a string")
    
    expr = expression.strip()
    if not expr:
        raise ValueError("Expression cannot be empty")
    
    tokens = tokenize(expr)
    result, pos = parse_expression(tokens, 0)
    
    if pos != len(tokens):
        raise ValueError("Malformed expression")
    
    return result


def tokenize(expr: str) -> list:
    tokens = []
    i = 0
    
    while i < len(expr):
        if expr[i].isspace():
            i += 1
        elif expr[i] in '()+-*/':
            tokens.append(expr[i])
            i += 1
        elif expr[i].isdigit() or expr[i] == '.':
            j = i
            while j < len(expr) and (expr[j].isdigit() or expr[j] == '.'):
                j += 1
            try:
                tokens.append(float(expr[i:j]))
            except ValueError:
                raise ValueError("Malformed expression")
            i = j
        else:
            raise ValueError("Malformed expression")
    
    return tokens


def parse_expression(tokens: list, pos: int):
    left, pos = parse_term(tokens, pos)
    
    while pos < len(tokens) and tokens[pos] in ['+', '-']:
        op = tokens[pos]
        pos += 1
        right, pos = parse_term(tokens, pos)
        if op == '+':
            left = left + right
        else:
            left = left - right
    
    return left, pos


def parse_term(tokens: list, pos: int):
    left, pos = parse_factor(tokens, pos)
    
    while pos < len(tokens) and tokens[pos] in ['*', '/']:
        op = tokens[pos]
        pos += 1
        right, pos = parse_factor(tokens, pos)
        if op == '*':
            left = left * right
        else:
            if right == 0:
                raise ValueError("Division by zero")
            left = left / right
    
    return left, pos


def parse_factor(tokens: list, pos: int):
    if pos >= len(tokens):
        raise ValueError("Malformed expression")
    
    token = tokens[pos]
    
    if token == '-':
        pos += 1
        result, pos = parse_factor(tokens, pos)
        return -result, pos
    elif token == '+':
        pos += 1
        return parse_factor(tokens, pos)
    elif isinstance(token, float):
        return token, pos + 1
    elif token == '(':
        pos += 1
        result, pos = parse_expression(tokens, pos)
        if pos >= len(tokens) or tokens[pos] != ')':
            raise ValueError("Mismatched parentheses")
        return result, pos + 1
    else:
        raise ValueError("Malformed expression")
