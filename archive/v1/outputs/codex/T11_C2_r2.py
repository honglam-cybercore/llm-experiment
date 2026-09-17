class _Parser:
    def __init__(self, expression):
        self.expression = expression
        self.position = 0
        self.length = len(expression)

    def _skip_whitespace(self):
        while self.position < self.length and self.expression[self.position].isspace():
            self.position += 1

    def _parse_expression(self):
        value = self._parse_term()

        while True:
            self._skip_whitespace()
            if self.position >= self.length:
                return value

            operator = self.expression[self.position]
            if operator not in "+-":
                return value

            self.position += 1
            right = self._parse_term()
            value = value + right if operator == "+" else value - right

    def _parse_term(self):
        value = self._parse_factor()

        while True:
            self._skip_whitespace()
            if self.position >= self.length:
                return value

            operator = self.expression[self.position]
            if operator not in "*/":
                return value

            self.position += 1
            right = self._parse_factor()

            if operator == "*":
                value *= right
            else:
                if right == 0.0:
                    raise ValueError("division by zero")
                value /= right

    def _parse_factor(self):
        self._skip_whitespace()

        if self.position >= self.length:
            raise ValueError("malformed expression")

        character = self.expression[self.position]

        if character in "+-":
            self.position += 1
            value = self._parse_factor()
            return value if character == "+" else -value

        if character == "(":
            self.position += 1
            value = self._parse_expression()
            self._skip_whitespace()

            if self.position >= self.length or self.expression[self.position] != ")":
                raise ValueError("malformed expression")

            self.position += 1
            return value

        start = self.position
        digit_count = 0
        dot_count = 0

        while self.position < self.length:
            character = self.expression[self.position]

            if "0" <= character <= "9":
                digit_count += 1
                self.position += 1
            elif character == ".":
                dot_count += 1
                if dot_count > 1:
                    raise ValueError("malformed number")
                self.position += 1
            else:
                break

        if digit_count == 0:
            raise ValueError("malformed expression")

        try:
            return float(self.expression[start:self.position])
        except (TypeError, ValueError, OverflowError):
            raise ValueError("malformed number")


def evaluate(expression) -> float:
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("expression must not be empty")

    parser = _Parser(expression)
    result = parser._parse_expression()
    parser._skip_whitespace()

    if parser.position != parser.length:
        raise ValueError("malformed expression")

    return float(result)