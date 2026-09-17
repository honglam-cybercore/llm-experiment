import math


class _Parser:
    def __init__(self, expression):
        self.expression = expression
        self.position = 0
        self.length = len(expression)

    def _skip_whitespace(self):
        while self.position < self.length and self.expression[self.position].isspace():
            self.position += 1

    def _match(self, character):
        self._skip_whitespace()
        if self.position < self.length and self.expression[self.position] == character:
            self.position += 1
            return True
        return False

    def parse(self):
        self._skip_whitespace()
        if self.position >= self.length:
            raise ValueError("Empty expression")

        result = self._parse_expression()
        self._skip_whitespace()

        if self.position != self.length:
            raise ValueError("Malformed expression")
        if not math.isfinite(result):
            raise ValueError("Non-finite result")

        return result

    def _parse_expression(self):
        result = self._parse_term()

        while True:
            if self._match("+"):
                result += self._parse_term()
            elif self._match("-"):
                result -= self._parse_term()
            else:
                return result

            if not math.isfinite(result):
                raise ValueError("Non-finite result")

    def _parse_term(self):
        result = self._parse_factor()

        while True:
            if self._match("*"):
                result *= self._parse_factor()
            elif self._match("/"):
                divisor = self._parse_factor()
                if divisor == 0.0:
                    raise ValueError("Division by zero")
                result /= divisor
            else:
                return result

            if not math.isfinite(result):
                raise ValueError("Non-finite result")

    def _parse_factor(self):
        self._skip_whitespace()

        if self.position < self.length and self.expression[self.position] == "-":
            self.position += 1
            result = -self._parse_factor()
            if not math.isfinite(result):
                raise ValueError("Non-finite result")
            return result

        if self._match("("):
            result = self._parse_expression()
            if not self._match(")"):
                raise ValueError("Malformed expression")
            return result

        return self._parse_number()

    def _parse_number(self):
        self._skip_whitespace()
        start = self.position
        before_decimal = 0

        while self.position < self.length and self.expression[self.position].isdigit():
            self.position += 1
            before_decimal += 1

        after_decimal = 0
        if self.position < self.length and self.expression[self.position] == ".":
            self.position += 1
            while self.position < self.length and self.expression[self.position].isdigit():
                self.position += 1
                after_decimal += 1

        if before_decimal == 0 and after_decimal == 0:
            raise ValueError("Malformed expression")

        try:
            value = float(self.expression[start:self.position])
        except (OverflowError, ValueError) as exc:
            raise ValueError("Malformed number") from exc

        if not math.isfinite(value):
            raise ValueError("Non-finite number")

        return value


def evaluate(expression) -> float:
    if not isinstance(expression, str):
        raise ValueError("Expression must be text")
    if len(expression) > 100000:
        raise ValueError("Expression is too long")

    try:
        return _Parser(expression).parse()
    except RecursionError as exc:
        raise ValueError("Expression is too deeply nested") from exc
