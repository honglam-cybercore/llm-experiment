"""Registration input validation.

Validates username, email, and password without echoing any user-supplied
value (especially the password) into return values, exceptions, or logs.
"""

import re
import unicodedata

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 20
PASSWORD_MIN_LENGTH = 8
# Upper bound guards against resource-exhaustion via absurdly long inputs.
PASSWORD_MAX_LENGTH = 1024
EMAIL_MAX_LENGTH = 254
EMAIL_LOCAL_MAX_LENGTH = 64

# Conservative username policy: letters, digits, underscore, hyphen, dot;
# must start and end with an alphanumeric character.
_USERNAME_RE = re.compile(r"\A[A-Za-z0-9](?:[A-Za-z0-9._-]{1,18}[A-Za-z0-9])\Z")
_USERNAME_SHORT_RE = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9][A-Za-z0-9]\Z")

# Linear-time (no nested quantifiers) local/domain patterns to avoid
# catastrophic backtracking on hostile input.
_EMAIL_LOCAL_RE = re.compile(r"\A[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*\Z")
_EMAIL_LABEL_RE = re.compile(r"\A[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\Z")

_UPPER_RE = re.compile(r"[A-Z]")
_LOWER_RE = re.compile(r"[a-z]")
_DIGIT_RE = re.compile(r"[0-9]")
_SPECIAL_RE = re.compile(r"[!-/:-@\[-`{-~]")

_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


def _is_clean_text(value):
    """True only for a str with no control characters or surrounding space."""
    if not isinstance(value, str):
        return False
    if _CONTROL_RE.search(value):
        return False
    if value != value.strip():
        return False
    return True


def _valid_username(username):
    if not _is_clean_text(username):
        return False
    # Normalize so visually identical forms are length-checked consistently.
    normalized = unicodedata.normalize("NFKC", username)
    if normalized != username:
        return False
    length = len(username)
    if length < USERNAME_MIN_LENGTH or length > USERNAME_MAX_LENGTH:
        return False
    if length == USERNAME_MIN_LENGTH:
        return bool(_USERNAME_SHORT_RE.match(username))
    return bool(_USERNAME_RE.match(username))


def _valid_email(email):
    if not _is_clean_text(email):
        return False
    if not 3 <= len(email) <= EMAIL_MAX_LENGTH:
        return False
    if email.count("@") != 1:
        return False
    local, _, domain = email.partition("@")
    if not local or len(local) > EMAIL_LOCAL_MAX_LENGTH:
        return False
    if not _EMAIL_LOCAL_RE.match(local):
        return False
    if not domain or len(domain) > 253 or domain.endswith("."):
        return False
    labels = domain.split(".")
    if len(labels) < 2:
        return False
    if not all(_EMAIL_LABEL_RE.match(label) for label in labels):
        return False
    # Require a plausible alphabetic TLD.
    if len(labels[-1]) < 2 or not labels[-1].isalpha():
        return False
    return True


def _valid_password(password):
    if not isinstance(password, str):
        return False
    if _CONTROL_RE.search(password):
        return False
    if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        return False
    if not _UPPER_RE.search(password):
        return False
    if not _LOWER_RE.search(password):
        return False
    if not _DIGIT_RE.search(password):
        return False
    if not _SPECIAL_RE.search(password):
        return False
    return True


def validate_registration(username, email, password) -> dict:
    """Validate registration fields.

    Returns {"valid": bool, "errors": [str]} where each error is the lowercase
    name of the failing field. No user-supplied value is included in the result.
    """
    errors = []

    checks = (
        ("username", _valid_username, username),
        ("email", _valid_email, email),
        ("password", _valid_password, password),
    )

    for field, check, value in checks:
        try:
            ok = check(value)
        except Exception:
            # Fail closed: any unexpected condition is a validation failure.
            ok = False
        if not ok:
            errors.append(field)

    return {"valid": not errors, "errors": errors}
