import math


class _Parser:
    def __init__(self, expression):
        self.expression = expression
        self.length = len(expression)
        self.position = 0
        self.depth = 0
        self.max_depth = 1000

    def _skip_whitespace(self):
        while self.position < self.length and self.expression[self.position].isspace():
            self.position += 1

    def _peek(self):
        self._skip_whitespace()
        if self.position >= self.length:
            return ""
        return self.expression[self.position]

    def parse(self):
        self._skip_whitespace()
        if self.position >= self.length:
            raise ValueError("empty expression")
        result = self._parse_expression()
        self._skip_whitespace()
        if self.position != self.length:
            raise ValueError("malformed expression")
        if not math.isfinite(result):
            raise ValueError("non-finite result")
        return float(result)

    def _parse_expression(self):
        result = self._parse_term()

        while True:
            operator = self._peek()
            if operator not in ("+", "-"):
                return result
            self.position += 1
            right = self._parse_term()
            result = result + right if operator == "+" else result - right

    def _parse_term(self):
        result = self._parse_unary()

        while True:
            operator = self._peek()
            if operator not in ("*", "/"):
                return result
            self.position += 1
            right = self._parse_unary()
            if operator == "*":
                result *= right
            else:
                if right == 0.0:
                    raise ValueError("division by zero")
                result /= right

    def _parse_unary(self):
        operator = self._peek()
        if operator in ("+", "-"):
            self.position += 1
            value = self._parse_unary()
            return value if operator == "+" else -value
        return self._parse_primary()

    def _parse_primary(self):
        character = self._peek()

        if character == "(":
            self.position += 1
            self.depth += 1
            if self.depth > self.max_depth:
                raise ValueError("expression too deeply nested")
            result = self._parse_expression()
            self._skip_whitespace()
            if self._peek() != ")":
                raise ValueError("malformed expression")
            self.position += 1
            self.depth -= 1
            return result

        if character == "" or not (character.isdigit() or character == "."):
            raise ValueError("malformed expression")

        start = self.position
        digit_count = 0
        dot_count = 0

        while self.position < self.length:
            character = self.expression[self.position]
            if character.isdigit() and character.isascii():
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
            raise ValueError("malformed number")

        try:
            value = float(self.expression[start:self.position])
        except (OverflowError, ValueError):
            raise ValueError("malformed number") from None

        if not math.isfinite(value):
            raise ValueError("non-finite number")
        return value


def evaluate(expression) -> float:
    if not isinstance(expression, str):
        raise ValueError("expression must be text")
    return _Parser(expression).parse()