import re

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_registration(username, email, password) -> dict:
    errors = []

    if not isinstance(username, str) or not 3 <= len(username) <= 20:
        errors.append("username")

    if not isinstance(email, str) or not _EMAIL_PATTERN.fullmatch(email):
        errors.append("email")

    if (
        not isinstance(password, str)
        or len(password) < 8
        or not any(char.isupper() for char in password)
        or not any(char.islower() for char in password)
        or not any(char.isdigit() for char in password)
        or not any(not char.isalnum() for char in password)
    ):
        errors.append("password")

    return {"valid": not errors, "errors": errors}