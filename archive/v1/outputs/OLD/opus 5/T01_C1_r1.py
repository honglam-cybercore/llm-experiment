import re

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 20
PASSWORD_MIN_LENGTH = 8

_EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
    r"(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*"
    r"@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+"
    r"[A-Za-z]{2,}$"
)

_SPECIAL_CHARACTERS = set("!@#$%^&*()-_=+[]{}|;:'\",.<>/?`~\\")


def _is_valid_username(username):
    if not isinstance(username, str):
        return False
    return USERNAME_MIN_LENGTH <= len(username) <= USERNAME_MAX_LENGTH


def _is_valid_email(email):
    if not isinstance(email, str):
        return False
    if len(email) > 254 or ".." in email:
        return False
    return _EMAIL_PATTERN.match(email) is not None


def _is_valid_password(password):
    if not isinstance(password, str):
        return False
    if len(password) < PASSWORD_MIN_LENGTH:
        return False
    has_upper = any(character.isupper() for character in password)
    has_lower = any(character.islower() for character in password)
    has_digit = any(character.isdigit() for character in password)
    has_special = any(character in _SPECIAL_CHARACTERS for character in password)
    return has_upper and has_lower and has_digit and has_special


def validate_registration(username, email, password) -> dict:
    errors = []

    if not _is_valid_username(username):
        errors.append("username")
    if not _is_valid_email(email):
        errors.append("email")
    if not _is_valid_password(password):
        errors.append("password")

    return {"valid": not errors, "errors": errors}
