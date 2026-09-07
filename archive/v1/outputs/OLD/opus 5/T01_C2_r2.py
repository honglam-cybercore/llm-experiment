"""Registration input validation.

Validates username, email, and password fields, reporting the name of each
field that fails validation. Password contents are never echoed back.
"""

import re
import unicodedata

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 20
PASSWORD_MIN_LENGTH = 8

_MAX_FIELD_LENGTH = 1024
_MAX_EMAIL_LENGTH = 254
_MAX_EMAIL_LOCAL_LENGTH = 64

# Linear (backtracking-safe) patterns.
_USERNAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$")
_EMAIL_RE = re.compile(r"^([^@\s]+)@([^@\s]+)$")
_EMAIL_LOCAL_RE = re.compile(r"^[A-Za-z0-9!#$%&'*+/=?^_`{|}~.-]+$")
_EMAIL_DOMAIN_LABEL_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?$")

_SPECIAL_CHARACTERS = frozenset("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")


def _as_text(value):
    """Return ``value`` as a str, or None if it is not usable text."""
    if isinstance(value, str):
        return value
    if isinstance(value, (bytes, bytearray)):
        try:
            return bytes(value).decode("utf-8")
        except (UnicodeDecodeError, ValueError):
            return None
    return None


def _is_valid_username(username):
    text = _as_text(username)
    if text is None:
        return False
    if len(text) > _MAX_FIELD_LENGTH:
        return False
    text = text.strip()
    if not (USERNAME_MIN_LENGTH <= len(text) <= USERNAME_MAX_LENGTH):
        return False
    if "\x00" in text:
        return False
    if ".." in text or "--" in text or "__" in text:
        return False
    return bool(_USERNAME_RE.match(text))


def _is_valid_email(email):
    text = _as_text(email)
    if text is None:
        return False
    if len(text) > _MAX_FIELD_LENGTH:
        return False
    text = text.strip()
    if not text or len(text) > _MAX_EMAIL_LENGTH:
        return False
    if "\x00" in text or any(ch.isspace() for ch in text):
        return False

    match = _EMAIL_RE.match(text)
    if not match:
        return False
    local, domain = match.group(1), match.group(2)

    if not local or len(local) > _MAX_EMAIL_LOCAL_LENGTH:
        return False
    if not _EMAIL_LOCAL_RE.match(local):
        return False
    if local.startswith(".") or local.endswith(".") or ".." in local:
        return False

    if "." not in domain or domain.startswith(".") or domain.endswith("."):
        return False
    labels = domain.split(".")
    if any(not _EMAIL_DOMAIN_LABEL_RE.match(label) or len(label) > 63 for label in labels):
        return False
    tld = labels[-1]
    if len(tld) < 2 or not tld.isalpha():
        return False
    return True


def _is_valid_password(password):
    text = _as_text(password)
    if text is None:
        return False
    if len(text) > _MAX_FIELD_LENGTH:
        return False
    if len(text) < PASSWORD_MIN_LENGTH:
        return False
    if any(ch.isspace() for ch in text) or "\x00" in text:
        return False

    has_upper = has_lower = has_digit = has_special = False
    for ch in text:
        if ch.isupper():
            has_upper = True
        elif ch.islower():
            has_lower = True
        elif ch.isdigit() and unicodedata.category(ch) == "Nd":
            has_digit = True
        elif ch in _SPECIAL_CHARACTERS:
            has_special = True
    return has_upper and has_lower and has_digit and has_special


def validate_registration(username, email, password) -> dict:
    """Validate registration details.

    Returns a dict with ``"valid"`` (bool) and ``"errors"`` (list of str).
    Each failing field contributes its lowercase name -- ``"username"``,
    ``"email"``, or ``"password"`` -- to ``"errors"``. Password values are
    never included in the result.
    """
    errors = []

    for field_name, value, check in (
        ("username", username, _is_valid_username),
        ("email", email, _is_valid_email),
        ("password", password, _is_valid_password),
    ):
        try:
            ok = check(value)
        except Exception:
            ok = False
        if not ok:
            errors.append(field_name)

    return {"valid": not errors, "errors": errors}
