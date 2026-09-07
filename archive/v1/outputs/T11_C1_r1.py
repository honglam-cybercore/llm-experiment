def evaluate(expression) -> float:
    if not expression or not expression.strip():
        raise ValueError("Empty expression")
    
    expression = expression.strip()
    
    tokens = []
    i = 0
    while i < len(expression):
        if expression[i].isspace():
            i += 1
        elif expression[i] in '+-*/()':
            tokens.append(expression[i])
            i += 1
        elif expression[i].isdigit() or expression[i] == '.':
            j = i
            dot_count = 0
            while j < len(expression) and (expression[j].isdigit() or expression[j] == '.'):
                if expression[j] == '.':
                    dot_count += 1
                    if dot_count > 1:
                        raise ValueError("Invalid number")
                j += 1
            try:
                tokens.append(float(expression[i:j]))
            except ValueError:
                raise ValueError("Invalid number")
            i = j
        else:
            raise ValueError("Invalid character")
    
    if not tokens:
        raise ValueError("Empty expression")
    
    pos = [0]
    
    def parse_expression():
        left = parse_term()
        while pos[0] < len(tokens) and tokens[pos[0]] in ['+', '-']:
            op = tokens[pos[0]]
            pos[0] += 1
            right = parse_term()
            left = left + right if op == '+' else left - right
        return left
    
    def parse_term():
        left = parse_factor()
        while pos[0] < len(tokens) and tokens[pos[0]] in ['*', '/']:
            op = tokens[pos[0]]
            pos[0] += 1
            right = parse_factor()
            if op == '*':
                left = left * right
            else:
                if right == 0:
                    raise ValueError("Division by zero")
                left = left / right
        return left
    
    def parse_factor():
        if pos[0] >= len(tokens):
            raise ValueError("Unexpected end of expression")
        
        token = tokens[pos[0]]
        
        if token == '-':
            pos[0] += 1
            return -parse_factor()
        elif token == '+':
            pos[0] += 1
            return parse_factor()
        elif token == '(':
            pos[0] += 1
            result = parse_expression()
            if pos[0] >= len(tokens) or tokens[pos[0]] != ')':
                raise ValueError("Mismatched parentheses")
            pos[0] += 1
            return result
        elif isinstance(token, float):
            pos[0] += 1
            return token
        else:
            raise ValueError("Unexpected token")
    
    result = parse_expression()
    
    if pos[0] < len(tokens):
        raise ValueError("Unexpected token at end of expression")
    
    return result
