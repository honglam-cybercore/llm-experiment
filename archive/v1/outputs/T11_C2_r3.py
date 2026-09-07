def evaluate(expression: str) -> float:
    if not expression or not isinstance(expression, str):
        raise ValueError("Expression cannot be empty")
    
    expression = expression.strip()
    if not expression:
        raise ValueError("Expression cannot be empty")
    
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
            while j < len(expression) and (expression[j].isdigit() or expression[j] == '.'):
                j += 1
            token_str = expression[i:j]
            try:
                tokens.append(float(token_str))
            except ValueError:
                raise ValueError(f"Invalid number: {token_str}")
            i = j
        else:
            raise ValueError(f"Invalid character: {expression[i]}")
    
    if not tokens:
        raise ValueError("Expression cannot be empty")
    
    class Parser:
        def __init__(self, tokens):
            self.tokens = tokens
            self.pos = 0
        
        def parse(self):
            result = self.parse_expression()
            if self.pos < len(self.tokens):
                raise ValueError("Unexpected tokens at end of expression")
            return result
        
        def parse_expression(self):
            result = self.parse_term()
            while self.pos < len(self.tokens) and self.tokens[self.pos] in ('+', '-'):
                op = self.tokens[self.pos]
                self.pos += 1
                right = self.parse_term()
                if op == '+':
                    result = result + right
                else:
                    result = result - right
            return result
        
        def parse_term(self):
            result = self.parse_factor()
            while self.pos < len(self.tokens) and self.tokens[self.pos] in ('*', '/'):
                op = self.tokens[self.pos]
                self.pos += 1
                right = self.parse_factor()
                if op == '*':
                    result = result * right
                else:
                    if right == 0:
                        raise ValueError("Division by zero")
                    result = result / right
            return result
        
        def parse_factor(self):
            if self.pos >= len(self.tokens):
                raise ValueError("Unexpected end of expression")
            
            token = self.tokens[self.pos]
            
            if token == '-':
                self.pos += 1
                return -self.parse_factor()
            elif token == '+':
                self.pos += 1
                return self.parse_factor()
            elif token == '(':
                self.pos += 1
                result = self.parse_expression()
                if self.pos >= len(self.tokens) or self.tokens[self.pos] != ')':
                    raise ValueError("Missing closing parenthesis")
                self.pos += 1
                return result
            elif isinstance(token, float):
                self.pos += 1
                return token
            else:
                raise ValueError(f"Unexpected token: {token}")
    
    parser = Parser(tokens)
    return parser.parse()
