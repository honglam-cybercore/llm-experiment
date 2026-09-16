import re

_EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)


def validate_registration(username, email, password) -> dict:
    errors = []

    if not isinstance(username, str) or not 3 <= len(username) <= 20:
        errors.append("username")

    if not isinstance(email, str) or not _EMAIL_PATTERN.fullmatch(email):
        errors.append("email")

    if (
        not isinstance(password, str)
        or len(password) < 8
        or not any("A" <= char <= "Z" for char in password)
        or not any("a" <= char <= "z" for char in password)
        or not any("0" <= char <= "9" for char in password)
        or not any(not char.isalnum() for char in password)
    ):
        errors.append("password")

    return {"valid": not errors, "errors": errors}