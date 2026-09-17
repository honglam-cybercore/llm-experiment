import re


_NUMBER = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)")


class _Parser:
    def __init__(self, expression):
        self.expression = expression
        self.position = 0

    def parse(self):
        self._skip_whitespace()
        if self.position >= len(self.expression):
            raise ValueError("empty expression")

        result = self._parse_expression()
        self._skip_whitespace()

        if self.position != len(self.expression):
            raise ValueError("malformed expression")

        return float(result)

    def _parse_expression(self):
        result = self._parse_term()

        while True:
            self._skip_whitespace()
            if self._match("+"):
                result += self._parse_term()
            elif self._match("-"):
                result -= self._parse_term()
            else:
                return result

    def _parse_term(self):
        result = self._parse_factor()

        while True:
            self._skip_whitespace()
            if self._match("*"):
                result *= self._parse_factor()
            elif self._match("/"):
                divisor = self._parse_factor()
                if divisor == 0:
                    raise ValueError("division by zero")
                result /= divisor
            else:
                return result

    def _parse_factor(self):
        self._skip_whitespace()

        if self._match("-"):
            return -self._parse_factor()

        if self._match("("):
            result = self._parse_expression()
            self._skip_whitespace()
            if not self._match(")"):
                raise ValueError("missing closing parenthesis")
            return result

        match = _NUMBER.match(self.expression, self.position)
        if not match:
            raise ValueError("malformed expression")

        self.position = match.end()
        return float(match.group())

    def _skip_whitespace(self):
        while self.position < len(self.expression) and self.expression[self.position].isspace():
            self.position += 1

    def _match(self, character):
        if self.position < len(self.expression) and self.expression[self.position] == character:
            self.position += 1
            return True
        return False


def evaluate(expression) -> float:
    if not isinstance(expression, str):
        raise ValueError("expression must be a string")
    return _Parser(expression).parse()