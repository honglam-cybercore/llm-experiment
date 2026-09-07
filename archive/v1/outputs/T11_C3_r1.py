def evaluate(expression) -> float:
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("Expression cannot be empty")
    
    expression = expression.strip()
    
    # Tokenize the expression
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
                        raise ValueError("Invalid number format")
                j += 1
            num_str = expression[i:j]
            if num_str == '.':
                raise ValueError("Invalid number format")
            try:
                tokens.append(float(num_str))
            except ValueError:
                raise ValueError("Invalid number format")
            i = j
        else:
            raise ValueError("Invalid character in expression")
    
    if not tokens:
        raise ValueError("Expression cannot be empty")
    
    # Parse with recursive descent parser
    pos = 0
    
    def peek():
        nonlocal pos
        return tokens[pos] if pos < len(tokens) else None
    
    def consume():
        nonlocal pos
        token = tokens[pos]
        pos += 1
        return token
    
    def parse_expression():
        nonlocal pos
        left = parse_term()
        while peek() in ('+', '-'):
            op = consume()
            right = parse_term()
            left = left + right if op == '+' else left - right
        return left
    
    def parse_term():
        nonlocal pos
        left = parse_factor()
        while peek() in ('*', '/'):
            op = consume()
            right = parse_factor()
            if op == '*':
                left = left * right
            else:
                if right == 0:
                    raise ValueError("Division by zero")
                left = left / right
        return left
    
    def parse_factor():
        nonlocal pos
        token = peek()
        
        if isinstance(token, float):
            return consume()
        elif token == '(':
            consume()
            result = parse_expression()
            if peek() != ')':
                raise ValueError("Mismatched parentheses")
            consume()
            return result
        elif token in ('+', '-'):
            op = consume()
            value = parse_factor()
            return -value if op == '-' else value
        else:
            raise ValueError("Malformed expression")
    
    result = parse_expression()
    if pos < len(tokens):
        raise ValueError("Malformed expression")
    
    return result
