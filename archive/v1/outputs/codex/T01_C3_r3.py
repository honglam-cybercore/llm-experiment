import re

_EMAIL_RE = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)


def validate_registration(username, email, password) -> dict:
    errors = []

    if (
        not isinstance(username, str)
        or not 3 <= len(username) <= 20
        or any(char.isspace() for char in username)
    ):
        errors.append("username")

    if (
        not isinstance(email, str)
        or len(email) > 254
        or not _EMAIL_RE.fullmatch(email)
    ):
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