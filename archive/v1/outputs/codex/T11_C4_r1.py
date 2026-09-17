import math


_MAX_LENGTH = 10000
_MAX_NUMBER_LENGTH = 1000


class _Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    def _current(self):
        if self.position >= len(self.tokens):
            return None
        return self.tokens[self.position]

    def _consume(self):
        token = self._current()
        self.position += 1
        return token

    def parse(self):
        if not self.tokens:
            raise ValueError("Invalid expression")
        result = self._parse_expression()
        if self._current() is not None:
            raise ValueError("Invalid expression")
        return result

    def _parse_expression(self):
        result = self._parse_term()
        while self._current() in ("+", "-"):
            operator = self._consume()
            right = self._parse_term()
            result = result + right if operator == "+" else result - right
            self._validate_result(result)
        return result

    def _parse_term(self):
        result = self._parse_unary()
        while self._current() in ("*", "/"):
            operator = self._consume()
            right = self._parse_unary()
            if operator == "*":
                result *= right
            else:
                if right == 0.0:
                    raise ValueError("Division by zero")
                result /= right
            self._validate_result(result)
        return result

    def _parse_unary(self):
        token = self._current()
        if token == "+":
            self._consume()
            return self._parse_unary()
        if token == "-":
            self._consume()
            result = -self._parse_unary()
            self._validate_result(result)
            return result
        return self._parse_primary()

    def _parse_primary(self):
        token = self._current()
        if token is None:
            raise ValueError("Invalid expression")

        if token == "(":
            self._consume()
            result = self._parse_expression()
            if self._consume() != ")":
                raise ValueError("Invalid expression")
            return result

        if isinstance(token, float):
            self._consume()
            return token

        raise ValueError("Invalid expression")

    @staticmethod
    def _validate_result(value):
        if not math.isfinite(value):
            raise ValueError("Invalid numeric result")


def _tokenize(expression):
    tokens = []
    index = 0
    length = len(expression)

    while index < length:
        character = expression[index]

        if character.isspace():
            index += 1
            continue

        if character in "+-*/()":
            tokens.append(character)
            index += 1
            continue

        if ("0" <= character <= "9") or character == ".":
            start = index
            digits_before = 0

            while index < length and "0" <= expression[index] <= "9":
                index += 1
                digits_before += 1

            digits_after = 0
            if index < length and expression[index] == ".":
                index += 1
                while index < length and "0" <= expression[index] <= "9":
                    index += 1
                    digits_after += 1

            if digits_before == 0 and digits_after == 0:
                raise ValueError("Invalid expression")

            literal = expression[start:index]
            if len(literal) > _MAX_NUMBER_LENGTH:
                raise ValueError("Invalid expression")

            try:
                number = float(literal)
            except (OverflowError, ValueError):
                raise ValueError("Invalid expression") from None

            if not math.isfinite(number):
                raise ValueError("Invalid expression")

            tokens.append(number)
            continue

        raise ValueError("Unsupported operation")

    return tokens


def evaluate(expression) -> float:
    if type(expression) is not str:
        raise ValueError("Invalid expression")
    if not expression or len(expression) > _MAX_LENGTH:
        raise ValueError("Invalid expression")

    try:
        return _Parser(_tokenize(expression)).parse()
    except (RecursionError, ZeroDivisionError, OverflowError):
        raise ValueError("Invalid expression") from None