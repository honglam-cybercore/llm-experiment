def evaluate(expression) -> float:
    if not isinstance(expression, str):
        raise ValueError("Expression must be a string")
    
    expression = expression.replace(" ", "").replace("\t", "").replace("\n", "").replace("\r", "")
    
    if not expression:
        raise ValueError("Expression cannot be empty")
    
    tokens = []
    i = 0
    while i < len(expression):
        if expression[i].isdigit():
            j = i
            while j < len(expression) and expression[j].isdigit():
                j += 1
            if j < len(expression) and expression[j] == '.':
                j += 1
                while j < len(expression) and expression[j].isdigit():
                    j += 1
            try:
                num = float(expression[i:j])
                tokens.append(('NUM', num))
            except ValueError:
                raise ValueError(f"Invalid number: {expression[i:j]}")
            i = j
        elif expression[i] == '.' and i + 1 < len(expression) and expression[i + 1].isdigit():
            j = i + 1
            while j < len(expression) and expression[j].isdigit():
                j += 1
            try:
                num = float(expression[i:j])
                tokens.append(('NUM', num))
            except ValueError:
                raise ValueError(f"Invalid number: {expression[i:j]}")
            i = j
        elif expression[i] in '+-*/()':
            tokens.append((expression[i], expression[i]))
            i += 1
        else:
            raise ValueError(f"Invalid character: '{expression[i]}'")
    
    if not tokens:
        raise ValueError("Empty expression")
    
    class Parser:
        def __init__(self, tokens):
            self.tokens = tokens
            self.pos = 0
        
        def current(self):
            return self.tokens[self.pos] if self.pos < len(self.tokens) else None
        
        def consume(self, expected=None):
            token = self.current()
            if token is None:
                raise ValueError("Unexpected end of expression")
            if expected and token[0] != expected:
                raise ValueError(f"Expected {expected}, got {token[0]}")
            self.pos += 1
            return token
        
        def parse(self):
            result = self.parse_expression()
            if self.pos != len(self.tokens):
                raise ValueError("Unexpected tokens after expression")
            return result
        
        def parse_expression(self):
            result = self.parse_term()
            while self.current() and self.current()[0] in ['+', '-']:
                op = self.consume()[0]
                right = self.parse_term()
                result = result + right if op == '+' else result - right
            return result
        
        def parse_term(self):
            result = self.parse_factor()
            while self.current() and self.current()[0] in ['*', '/']:
                op = self.consume()[0]
                right = self.parse_factor()
                if op == '*':
                    result = result * right
                else:
                    if right == 0:
                        raise ValueError("Division by zero")
                    result = result / right
            return result
        
        def parse_factor(self):
            token = self.current()
            
            if token and token[0] in ['+', '-']:
                op = self.consume()[0]
                value = self.parse_factor()
                return -value if op == '-' else value
            
            if token and token[0] == '(':
                self.consume('(')
                result = self.parse_expression()
                if not self.current() or self.current()[0] != ')':
                    raise ValueError("Missing closing parenthesis")
                self.consume(')')
                return result
            
            if token and token[0] == 'NUM':
                return self.consume()[1]
            
            raise ValueError(f"Expected number or expression, got {token}")
    
    try:
        parser = Parser(tokens)
        return parser.parse()
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(str(e))
