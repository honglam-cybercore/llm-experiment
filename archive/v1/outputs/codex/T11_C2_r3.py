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

    def _consume(self, character):
        if self._peek() != character:
            raise ValueError("Malformed expression")
        self.position += 1

    def parse(self):
        self._skip_whitespace()
        if self.position >= self.length:
            raise ValueError("Empty expression")

        result = self._parse_expression()
        self._skip_whitespace()

        if self.position != self.length:
            raise ValueError("Malformed expression")

        return float(result)

    def _parse_expression(self):
        result = self._parse_term()

        while True:
            operator = self._peek()
            if operator not in ("+", "-"):
                break

            self.position += 1
            operand = self._parse_term()
            result = result + operand if operator == "+" else result - operand

        return result

    def _parse_term(self):
        result = self._parse_factor()

        while True:
            operator = self._peek()
            if operator not in ("*", "/"):
                break

            self.position += 1
            operand = self._parse_factor()

            if operator == "*":
                result *= operand
            else:
                if operand == 0:
                    raise ValueError("Division by zero")
                result /= operand

        return result

    def _parse_factor(self):
        operator = self._peek()

        if operator == "-":
            self.position += 1
            return -self._parse_factor()

        if operator == "+":
            raise ValueError("Unsupported or malformed operation")

        if operator == "(":
            self.position += 1
            result = self._parse_expression()
            self._consume(")")
            return result

        self._skip_whitespace()
        match = _NUMBER.match(self.expression, self.position)
        if not match:
            raise ValueError("Malformed expression")

        self.position = match.end()
        try:
            return float(match.group())
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("Malformed expression") from exc


def evaluate(expression) -> float:
    if not isinstance(expression, str):
        raise ValueError("Expression must be text")
    return _Parser(expression).parse()