def evaluate(expression) -> float:
    if not isinstance(expression, str):
        raise ValueError("Expression must be a string")
    
    expression = expression.replace(" ", "").replace("\t", "")
    
    if not expression:
        raise ValueError("Empty expression")
    
    tokens = tokenize(expression)
    
    if not tokens:
        raise ValueError("Empty expression")
    
    parser = Parser(tokens)
    result = parser.parse_expression()
    
    if parser.pos < len(parser.tokens):
        raise ValueError("Invalid expression: unexpected tokens after parsing")
    
    return float(result)


def tokenize(expression):
    tokens = []
    i = 0
    while i < len(expression):
        if expression[i].isspace():
            i += 1
        elif expression[i] in "+-*/()":
            tokens.append(expression[i])
            i += 1
        elif expression[i].isdigit() or expression[i] == '.':
            j = i
            has_dot = False
            while j < len(expression) and (expression[j].isdigit() or expression[j] == '.'):
                if expression[j] == '.':
                    if has_dot:
                        raise ValueError("Invalid number: multiple decimal points")
                    has_dot = True
                j += 1
            tokens.append(expression[i:j])
            i = j
        else:
            raise ValueError(f"Invalid character: {expression[i]}")
    return tokens


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
    
    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None
    
    def consume(self):
        token = self.peek()
        self.pos += 1
        return token
    
    def parse_expression(self):
        result = self.parse_term()
        
        while self.peek() in ['+', '-']:
            op = self.consume()
            right = self.parse_term()
            if op == '+':
                result = result + right
            else:
                result = result - right
        
        return result
    
    def parse_term(self):
        result = self.parse_factor()
        
        while self.peek() in ['*', '/']:
            op = self.consume()
            right = self.parse_factor()
            if op == '*':
                result = result * right
            else:
                if right == 0:
                    raise ValueError("Division by zero")
                result = result / right
        
        return result
    
    def parse_factor(self):
        token = self.peek()
        
        if token == '(':
            self.consume()
            result = self.parse_expression()
            if self.consume() != ')':
                raise ValueError("Missing closing parenthesis")
            return result
        elif token == '-':
            self.consume()
            return -self.parse_factor()
        elif token == '+':
            self.consume()
            return self.parse_factor()
        elif token is not None and is_number(token):
            return float(self.consume())
        else:
            raise ValueError("Invalid expression: expected number or '('")


def is_number(token):
    try:
        float(token)
        return True
    except ValueError:
        return False
