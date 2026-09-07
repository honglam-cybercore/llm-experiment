import re

_EMAIL_RE = re.compile(
    r"^[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
    r"(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*"
    r"@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+$"
)

_SPECIAL_CHARS = set("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")


def _is_valid_username(username):
    if not isinstance(username, str):
        return False
    return 3 <= len(username) <= 20


def _is_valid_email(email):
    if not isinstance(email, str):
        return False
    if len(email) > 254 or ".." in email:
        return False
    return _EMAIL_RE.match(email) is not None


def _is_valid_password(password):
    if not isinstance(password, str):
        return False
    if len(password) < 8:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in _SPECIAL_CHARS for c in password)
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
