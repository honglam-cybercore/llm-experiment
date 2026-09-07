def evaluate(expression) -> float:
    if not isinstance(expression, str):
        raise ValueError("Expression must be a string")
    
    expression = expression.strip()
    
    if not expression:
        raise ValueError("Expression cannot be empty")
    
    allowed_chars = set('0123456789+-*/(). ')
    if not all(c in allowed_chars for c in expression):
        raise ValueError("Expression contains invalid characters")
    
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
                j += 1
            if dot_count > 1:
                raise ValueError("Invalid number format")
            num_str = expression[i:j]
            try:
                tokens.append(float(num_str))
            except ValueError:
                raise ValueError("Invalid number format")
            i = j
        else:
            raise ValueError("Invalid character in expression")
    
    if not tokens:
        raise ValueError("Expression cannot be empty")
    
    index = [0]
    
    def parse_expression():
        result = parse_term()
        while index[0] < len(tokens) and tokens[index[0]] in ('+', '-'):
            op = tokens[index[0]]
            index[0] += 1
            right = parse_term()
            if op == '+':
                result += right
            else:
                result -= right
        return result
    
    def parse_term():
        result = parse_factor()
        while index[0] < len(tokens) and tokens[index[0]] in ('*', '/'):
            op = tokens[index[0]]
            index[0] += 1
            right = parse_factor()
            if op == '*':
                result *= right
            else:
                if right == 0:
                    raise ValueError("Division by zero")
                result /= right
        return result
    
    def parse_factor():
        if index[0] >= len(tokens):
            raise ValueError("Malformed expression")
        
        token = tokens[index[0]]
        
        if isinstance(token, float):
            index[0] += 1
            return token
        elif token == '(':
            index[0] += 1
            result = parse_expression()
            if index[0] >= len(tokens) or tokens[index[0]] != ')':
                raise ValueError("Mismatched parentheses")
            index[0] += 1
            return result
        elif token == '-':
            index[0] += 1
            return -parse_factor()
        elif token == '+':
            index[0] += 1
            return parse_factor()
        else:
            raise ValueError("Malformed expression")
    
    result = parse_expression()
    
    if index[0] != len(tokens):
        raise ValueError("Malformed expression")
    
    return result
