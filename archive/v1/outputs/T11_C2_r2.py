def evaluate(expression) -> float:
    if not expression or not isinstance(expression, str):
        raise ValueError("Expression cannot be empty")
    
    expr = expression.replace(" ", "").replace("\t", "")
    
    if not expr:
        raise ValueError("Expression cannot be empty")
    
    tokens = []
    i = 0
    while i < len(expr):
        if expr[i].isdigit() or (expr[i] == '.' and i + 1 < len(expr) and expr[i + 1].isdigit()):
            num_str = ""
            while i < len(expr) and (expr[i].isdigit() or expr[i] == '.'):
                num_str += expr[i]
                i += 1
            if num_str.count('.') > 1:
                raise ValueError("Invalid number format")
            tokens.append(('NUM', float(num_str)))
        elif expr[i] in "+-*/()":
            tokens.append((expr[i], expr[i]))
            i += 1
        else:
            raise ValueError("Invalid character")
    
    if not tokens:
        raise ValueError("Expression cannot be empty")
    
    pos = [0]
    
    def peek():
        if pos[0] < len(tokens):
            return tokens[pos[0]]
        return None
    
    def consume():
        token = tokens[pos[0]]
        pos[0] += 1
        return token
    
    def parse_expression():
        result = parse_term()
        while peek() and peek()[0] in "+-":
            op = consume()[0]
            right = parse_term()
            if op == '+':
                result = result + right
            else:
                result = result - right
        return result
    
    def parse_term():
        result = parse_factor()
        while peek() and peek()[0] in "*/":
            op = consume()[0]
            right = parse_factor()
            if op == '*':
                result = result * right
            else:
                if right == 0:
                    raise ValueError("Division by zero")
                result = result / right
        return result
    
    def parse_factor():
        token = peek()
        if not token:
            raise ValueError("Unexpected end of expression")
        
        if token[0] == 'NUM':
            consume()
            return token[1]
        elif token[0] == '(':
            consume()
            result = parse_expression()
            if not peek() or peek()[0] != ')':
                raise ValueError("Missing closing parenthesis")
            consume()
            return result
        elif token[0] in "+-":
            op = consume()[0]
            value = parse_factor()
            return -value if op == '-' else value
        else:
            raise ValueError("Invalid expression")
    
    result = parse_expression()
    
    if peek():
        raise ValueError("Unexpected token after expression")
    
    return result
