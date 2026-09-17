def evaluate(expression) -> float:
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("invalid expression")
    if len(expression) > 100000:
        raise ValueError("invalid expression")

    class Parser:
        def __init__(self, text):
            self.text = text
            self.length = len(text)
            self.pos = 0
            self.depth = 0

        def skip_spaces(self):
            while self.pos < self.length and self.text[self.pos].isspace():
                self.pos += 1

        def parse(self):
            value = self.parse_expression()
            self.skip_spaces()
            if self.pos != self.length:
                raise ValueError("invalid expression")
            if value != value or value in (float("inf"), float("-inf")):
                raise ValueError("invalid result")
            return float(value)

        def parse_expression(self):
            value = self.parse_term()
            while True:
                self.skip_spaces()
                if self.pos >= self.length or self.text[self.pos] not in "+-":
                    return value
                operator = self.text[self.pos]
                self.pos += 1
                right = self.parse_term()
                value = value + right if operator == "+" else value - right

        def parse_term(self):
            value = self.parse_factor()
            while True:
                self.skip_spaces()
                if self.pos >= self.length or self.text[self.pos] not in "*/":
                    return value
                operator = self.text[self.pos]
                self.pos += 1
                right = self.parse_factor()
                if operator == "*":
                    value *= right
                else:
                    if right == 0.0:
                        raise ValueError("division by zero")
                    value /= right

        def parse_factor(self):
            self.skip_spaces()
            if self.pos < self.length and self.text[self.pos] in "+-":
                operator = self.text[self.pos]
                self.pos += 1
                value = self.parse_factor()
                return value if operator == "+" else -value
            return self.parse_primary()

        def parse_primary(self):
            self.skip_spaces()
            if self.pos >= self.length:
                raise ValueError("invalid expression")

            if self.text[self.pos] == "(":
                self.depth += 1
                if self.depth > 1000:
                    raise ValueError("invalid expression")
                self.pos += 1
                value = self.parse_expression()
                self.skip_spaces()
                if self.pos >= self.length or self.text[self.pos] != ")":
                    raise ValueError("invalid expression")
                self.pos += 1
                self.depth -= 1
                return value

            start = self.pos
            digits = 0

            while self.pos < self.length and self.text[self.pos].isdigit():
                self.pos += 1
                digits += 1

            if self.pos < self.length and self.text[self.pos] == ".":
                self.pos += 1
                while self.pos < self.length and self.text[self.pos].isdigit():
                    self.pos += 1
                    digits += 1

            if digits == 0:
                raise ValueError("invalid expression")

            try:
                return float(self.text[start:self.pos])
            except (OverflowError, ValueError):
                raise ValueError("invalid expression")

    return Parser(expression).parse()