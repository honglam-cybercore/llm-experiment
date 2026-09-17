import re

_NUMBER = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)")


class _Parser:
    def __init__(self, expression):
        self.expression = expression
        self.position = 0
        self.length = len(expression)

    def _skip_whitespace(self):
        while self.position < self.length and self.expression[self.position].isspace():
            self.position += 1

    def _peek(self):
        self._skip_whitespace()
        if self.position >= self.length:
            return None
        return self.expression[self.position]

    def parse(self):
        self._skip_whitespace()
        if self.position >= self.length:
            raise ValueError("empty expression")

        result = self._parse_expression()
        self._skip_whitespace()

        if self.position != self.length:
            raise ValueError("malformed expression")

        return float(result)

    def _parse_expression(self):
        result = self._parse_term()

        while True:
            operator = self._peek()
            if operator not in ("+", "-"):
                return result

            self.position += 1
            operand = self._parse_term()
            result = result + operand if operator == "+" else result - operand

    def _parse_term(self):
        result = self._parse_factor()

        while True:
            operator = self._peek()
            if operator not in ("*", "/"):
                return result

            self.position += 1
            operand = self._parse_factor()

            if operator == "*":
                result *= operand
            else:
                if operand == 0:
                    raise ValueError("division by zero")
                result /= operand

    def _parse_factor(self):
        operator = self._peek()

        if operator in ("+", "-"):
            self.position += 1
            value = self._parse_factor()
            return value if operator == "+" else -value

        if operator == "(":
            self.position += 1
            value = self._parse_expression()
            if self._peek() != ")":
                raise ValueError("malformed expression")
            self.position += 1
            return value

        match = _NUMBER.match(self.expression, self.position)
        if match is None:
            raise ValueError("malformed expression")

        self.position = match.end()
        try:
            return float(match.group())
        except (OverflowError, ValueError) as exc:
            raise ValueError("malformed expression") from exc


def evaluate(expression) -> float:
    if not isinstance(expression, str):
        raise ValueError("expression must be a string")
    return _Parser(expression).parse()