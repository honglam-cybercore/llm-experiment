import re

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 20
PASSWORD_MIN_LENGTH = 8

_EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
    r"(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*"
    r"@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"[A-Za-z]{2,63}$"
)

_SPECIAL_CHARACTERS = set("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")


def _is_valid_username(username) -> bool:
    if not isinstance(username, str):
        return False
    if username != username.strip():
        return False
    if not (USERNAME_MIN_LENGTH <= len(username) <= USERNAME_MAX_LENGTH):
        return False
    return re.fullmatch(r"[A-Za-z0-9._-]+", username) is not None


def _is_valid_email(email) -> bool:
    if not isinstance(email, str):
        return False
    if email != email.strip():
        return False
    if not email or len(email) > 254:
        return False
    if ".." in email:
        return False
    local, sep, domain = email.rpartition("@")
    if not sep or len(local) > 64 or len(domain) > 253:
        return False
    return _EMAIL_PATTERN.fullmatch(email) is not None


def _is_valid_password(password) -> bool:
    if not isinstance(password, str):
        return False
    if len(password) < PASSWORD_MIN_LENGTH:
        return False
    if any(ch.isspace() for ch in password):
        return False
    has_upper = False
    has_lower = False
    has_digit = False
    has_special = False
    for ch in password:
        if ch.isupper():
            has_upper = True
        elif ch.islower():
            has_lower = True
        elif ch.isdigit():
            has_digit = True
        elif ch in _SPECIAL_CHARACTERS:
            has_special = True
    return has_upper and has_lower and has_digit and has_special


def validate_registration(username, email, password) -> dict:
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
