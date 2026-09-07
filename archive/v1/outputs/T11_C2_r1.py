def evaluate(expression) -> float:
    if not isinstance(expression, str):
        raise ValueError("Expression must be a string")
    
    expr = expression.strip().replace(" ", "")
    if not expr:
        raise ValueError("Expression cannot be empty")
    
    tokens = []
    i = 0
    
    while i < len(expr):
        if expr[i].isdigit() or expr[i] == '.':
            j = i
            dot_count = 0
            while j < len(expr) and (expr[j].isdigit() or expr[j] == '.'):
                if expr[j] == '.':
                    dot_count += 1
                j += 1
            
            if dot_count > 1:
                raise ValueError("Invalid number format")
            
            num_str = expr[i:j]
            if num_str == '.':
                raise ValueError("Invalid number")
            
            try:
                tokens.append(float(num_str))
            except ValueError:
                raise ValueError("Invalid number")
            
            i = j
        elif expr[i] in '+-*/()':
            tokens.append(expr[i])
            i += 1
        else:
            raise ValueError("Invalid character in expression")
    
    if not tokens:
        raise ValueError("Expression cannot be empty")
    
    class Parser:
        def __init__(self, tokens):
            self.tokens = tokens
            self.pos = 0
        
        def parse(self):
            result = self.parse_expression()
            if self.pos != len(self.tokens):
                raise ValueError("Invalid expression")
            return result
        
        def parse_expression(self):
            result = self.parse_term()
            while self.pos < len(self.tokens) and self.tokens[self.pos] in ['+', '-']:
                op = self.tokens[self.pos]
                self.pos += 1
                right = self.parse_term()
                if op == '+':
                    result += right
                else:
                    result -= right
            return result
        
        def parse_term(self):
            result = self.parse_factor()
            while self.pos < len(self.tokens) and self.tokens[self.pos] in ['*', '/']:
                op = self.tokens[self.pos]
                self.pos += 1
                right = self.parse_factor()
                if op == '*':
                    result *= right
                else:
                    if right == 0:
                        raise ValueError("Division by zero")
                    result /= right
            return result
        
        def parse_factor(self):
            if self.pos >= len(self.tokens):
                raise ValueError("Unexpected end of expression")
            
            token = self.tokens[self.pos]
            
            if token == '(':
                self.pos += 1
                result = self.parse_expression()
                if self.pos >= len(self.tokens) or self.tokens[self.pos] != ')':
                    raise ValueError("Missing closing parenthesis")
                self.pos += 1
                return result
            
            elif token == '-':
                self.pos += 1
                return -self.parse_factor()
            
            elif token == '+':
                self.pos += 1
                return self.parse_factor()
            
            elif isinstance(token, float):
                self.pos += 1
                return token
            
            else:
                raise ValueError("Invalid expression")
    
    parser = Parser(tokens)
    return parser.parse()
