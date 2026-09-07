def evaluate(expression) -> float:
    if not isinstance(expression, str):
        raise ValueError("Expression must be a string")
    
    expression = expression.strip()
    
    if not expression:
        raise ValueError("Expression is empty")
    
    # Tokenize
    tokens = []
    i = 0
    while i < len(expression):
        ch = expression[i]
        if ch.isspace():
            i += 1
        elif ch in '()+-*/':
            tokens.append(ch)
            i += 1
        elif ch.isdigit() or ch == '.':
            j = i
            while j < len(expression) and (expression[j].isdigit() or expression[j] == '.'):
                j += 1
            tokens.append(expression[i:j])
            i = j
        else:
            raise ValueError("Invalid character in expression")
    
    if not tokens:
        raise ValueError("Expression is empty")
    
    # Parser using closures
    pos = [0]
    
    def peek():
        return tokens[pos[0]] if pos[0] < len(tokens) else None
    
    def consume():
        token = peek()
        pos[0] += 1
        return token
    
    def parse_factor():
        token = peek()
        
        if token == '(':
            consume()
            result = parse_expression()
            if peek() != ')':
                raise ValueError("Missing closing parenthesis")
            consume()
            return result
        elif token == '-':
            consume()
            return -parse_factor()
        elif token == '+':
            consume()
            return parse_factor()
        elif token is not None and (token[0].isdigit() or token[0] == '.'):
            try:
                return float(consume())
            except ValueError:
                raise ValueError("Invalid number")
        else:
            raise ValueError("Unexpected token")
    
    def parse_term():
        left = parse_factor()
        
        while peek() in ['*', '/']:
            op = consume()
            right = parse_factor()
            if op == '*':
                left = left * right
            else:
                if right == 0:
                    raise ValueError("Division by zero")
                left = left / right
        
        return left
    
    def parse_expression():
        left = parse_term()
        
        while peek() in ['+', '-']:
            op = consume()
            right = parse_term()
            left = left + right if op == '+' else left - right
        
        return left
    
    result = parse_expression()
    
    if pos[0] != len(tokens):
        raise ValueError("Malformed expression")
    
    return result
