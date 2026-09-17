import math
import re

_NUMBER = re.compile(r"(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)")


class _Parser:
    def __init__(self, expression):
        self.expression = expression
        self.position = 0
        self.length = len(expression)
        self.depth = 0

    def _skip_whitespace(self):
        while self.position < self.length and self.expression[self.position].isspace():
            self.position += 1

    def _error(self):
        raise ValueError("Malformed expression")

    def parse(self):
        result = self._parse_expression()
        self._skip_whitespace()
        if self.position != self.length or not math.isfinite(result):
            self._error()
        return float(result)

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
            if not math.isfinite(value):
                self._error()

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
                    raise ValueError("Division by zero")
                value /= right

            if not math.isfinite(value):
                self._error()

    def _parse_factor(self):
        self._skip_whitespace()

        if self.position < self.length and self.expression[self.position] == "-":
            self.position += 1
            value = -self._parse_factor()
            if not math.isfinite(value):
                self._error()
            return value

        if self.position < self.length and self.expression[self.position] == "(":
            self.depth += 1
            if self.depth > 1000:
                self._error()
            self.position += 1
            value = self._parse_expression()
            self._skip_whitespace()
            if self.position >= self.length or self.expression[self.position] != ")":
                self._error()
            self.position += 1
            self.depth -= 1
            return value

        match = _NUMBER.match(self.expression, self.position)
        if match is None:
            self._error()

        self.position = match.end()
        try:
            value = float(match.group(0))
        except (OverflowError, ValueError):
            self._error()

        if not math.isfinite(value):
            self._error()
        return value


def evaluate(expression) -> float:
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("Expression must be a non-empty string")
    if len(expression) > 10000:
        raise ValueError("Expression is too long")
    return _Parser(expression).parse()
