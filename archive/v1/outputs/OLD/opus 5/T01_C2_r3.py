"""Registration input validation.

Validates username, email, and password fields and reports which named
fields failed. Password values are never echoed back in errors or output.
"""

import re

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 20
PASSWORD_MIN_LENGTH = 8

_EMAIL_RE = re.compile(
    r"^[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
    r"(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*"
    r"@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"[A-Za-z]{2,63}$"
)

_SPECIAL_CHARS = set("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")


def _is_valid_username(username) -> bool:
    if not isinstance(username, str):
        return False
    if len(username) != len(username.strip()):
        return False
    if not (USERNAME_MIN_LENGTH <= len(username) <= USERNAME_MAX_LENGTH):
        return False
    return True


def _is_valid_email(email) -> bool:
    if not isinstance(email, str):
        return False
    if len(email) > 254 or email != email.strip():
        return False
    local, _, domain = email.partition("@")
    if len(local) > 64 or ".." in email:
        return False
    if not domain or domain.startswith(".") or domain.endswith("."):
        return False
    return _EMAIL_RE.match(email) is not None


def _is_valid_password(password) -> bool:
    if not isinstance(password, str):
        return False
    if len(password) < PASSWORD_MIN_LENGTH:
        return False
    has_upper = has_lower = has_digit = has_special = False
    for char in password:
        if char.isupper():
            has_upper = True
        elif char.islower():
            has_lower = True
        elif char.isdigit():
            has_digit = True
        elif char in _SPECIAL_CHARS:
            has_special = True
    return has_upper and has_lower and has_digit and has_special


def validate_registration(username, email, password) -> dict:
    """Validate registration fields.

    Returns a dict with "valid" (bool) and "errors" (list of failing field
    names: "username", "email", "password"). Never includes field values.
    """
    errors = []

    try:
        if not _is_valid_username(username):
            errors.append("username")
    except Exception:
        errors.append("username")

    try:
        if not _is_valid_email(email):
            errors.append("email")
    except Exception:
        errors.append("email")

    try:
        if not _is_valid_password(password):
            errors.append("password")
    except Exception:
        errors.append("password")

    return {"valid": not errors, "errors": errors}
