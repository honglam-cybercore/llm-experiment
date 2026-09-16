import re


_EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)


def validate_registration(username, email, password) -> dict:
    errors = []

    if (
        not isinstance(username, str)
        or not 3 <= len(username) <= 20
        or not username.strip()
    ):
        errors.append("username")

    if not isinstance(email, str) or not _EMAIL_PATTERN.fullmatch(email):
        errors.append("email")

    if (
        not isinstance(password, str)
        or len(password) < 8
        or not any(character.isupper() for character in password)
        or not any(character.islower() for character in password)
        or not any(character.isdigit() for character in password)
        or not any(not character.isalnum() for character in password)
    ):
        errors.append("password")

    return {"valid": not errors, "errors": errors}