import re

_NUMBER = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)")


def evaluate(expression) -> float:
    if not isinstance(expression, str):
        raise ValueError("Expression must be a string")

    text = expression
    position = 0
    length = len(text)

    def skip_whitespace():
        nonlocal position
        while position < length and text[position].isspace():
            position += 1

    def parse_expression():
        nonlocal position
        value = parse_term()

        while True:
            skip_whitespace()
            if position >= length or text[position] not in "+-":
                return value

            operator = text[position]
            position += 1
            right = parse_term()
            value = value + right if operator == "+" else value - right

    def parse_term():
        nonlocal position
        value = parse_factor()

        while True:
            skip_whitespace()
            if position >= length or text[position] not in "*/":
                return value

            operator = text[position]
            position += 1
            right = parse_factor()

            if operator == "*":
                value *= right
            else:
                if right == 0:
                    raise ValueError("Division by zero")
                value /= right

    def parse_factor():
        nonlocal position
        skip_whitespace()

        sign = 1
        while position < length and text[position] in "+-":
            if text[position] == "-":
                sign = -sign
            position += 1
            skip_whitespace()

        if position >= length:
            raise ValueError("Malformed expression")

        if text[position] == "(":
            position += 1
            value = parse_expression()
            skip_whitespace()
            if position >= length or text[position] != ")":
                raise ValueError("Malformed expression")
            position += 1
            return sign * value

        match = _NUMBER.match(text, position)
        if not match:
            raise ValueError("Malformed expression")

        position = match.end()
        return sign * float(match.group())

    skip_whitespace()
    if position >= length:
        raise ValueError("Expression is empty")

    result = parse_expression()
    skip_whitespace()

    if position != length:
        raise ValueError("Malformed expression")

    return float(result)