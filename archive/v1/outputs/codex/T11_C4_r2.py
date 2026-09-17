from decimal import Decimal, InvalidOperation, localcontext


class _ExpressionParser:
    def __init__(self, expression):
        self.expression = expression
        self.position = 0
        self.length = len(expression)

    def parse(self):
        self._skip_whitespace()
        if self.position >= self.length:
            raise ValueError("Invalid expression")

        result = self._parse_expression()
        self._skip_whitespace()

        if self.position != self.length:
            raise ValueError("Invalid expression")

        return result

    def _skip_whitespace(self):
        while (
            self.position < self.length
            and self.expression[self.position].isspace()
        ):
            self.position += 1

    def _parse_expression(self):
        result = self._parse_term()

        while True:
            self._skip_whitespace()
            if self.position >= self.length:
                return result

            operator = self.expression[self.position]
            if operator not in "+-":
                return result

            self.position += 1
            right = self._parse_term()
            result = result + right if operator == "+" else result - right

    def _parse_term(self):
        result = self._parse_factor()

        while True:
            self._skip_whitespace()
            if self.position >= self.length:
                return result

            operator = self.expression[self.position]
            if operator not in "*/":
                return result

            self.position += 1
            right = self._parse_factor()

            if operator == "*":
                result *= right
            else:
                if right == 0:
                    raise ValueError("Division by zero")
                result /= right

    def _parse_factor(self):
        self._skip_whitespace()

        if self.position >= self.length:
            raise ValueError("Invalid expression")

        if self.expression[self.position] == "-":
            self.position += 1
            return -self._parse_factor()

        if self.expression[self.position] == "(":
            self.position += 1
            result = self._parse_expression()
            self._skip_whitespace()

            if (
                self.position >= self.length
                or self.expression[self.position] != ")"
            ):
                raise ValueError("Invalid expression")

            self.position += 1
            return result

        return self._parse_number()

    def _parse_number(self):
        start = self.position
        digits_before_decimal = 0
        digits_after_decimal = 0

        while (
            self.position < self.length
            and self.expression[self.position].isdigit()
            and self.expression[self.position].isascii()
        ):
            self.position += 1
            digits_before_decimal += 1

        if (
            self.position < self.length
            and self.expression[self.position] == "."
        ):
            self.position += 1
            while (
                self.position < self.length
                and self.expression[self.position].isdigit()
                and self.expression[self.position].isascii()
            ):
                self.position += 1
                digits_after_decimal += 1

        if digits_before_decimal == 0 and digits_after_decimal == 0:
            raise ValueError("Invalid expression")

        try:
            return Decimal(self.expression[start:self.position])
        except InvalidOperation as exc:
            raise ValueError("Invalid expression") from exc


def evaluate(expression) -> float:
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("Invalid expression")

    if len(expression) > 10000:
        raise ValueError("Invalid expression")

    try:
        with localcontext() as context:
            context.prec = max(28, len(expression) + 10)
            result = _ExpressionParser(expression).parse()

        value = float(result)
    except (ArithmeticError, OverflowError, ValueError) as exc:
        raise ValueError("Invalid expression") from exc

    if value != value or value in (float("inf"), float("-inf")):
        raise ValueError("Invalid expression")

    return value