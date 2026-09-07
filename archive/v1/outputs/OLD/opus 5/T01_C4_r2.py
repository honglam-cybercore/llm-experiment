"""Registration input validation.

Validates username, email and password without ever echoing the supplied
password (or any other raw value) back to the caller.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List

__all__ = ["validate_registration"]

# --- Limits -----------------------------------------------------------------

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 20

PASSWORD_MIN_LENGTH = 8
# Upper bound guards against resource-exhaustion via absurdly long input.
PASSWORD_MAX_LENGTH = 128

EMAIL_MAX_LENGTH = 254          # RFC 5321 practical maximum
EMAIL_LOCAL_MAX_LENGTH = 64
EMAIL_LABEL_MAX_LENGTH = 63

# --- Patterns ---------------------------------------------------------------
# All patterns are linear-time (no nested quantifiers) to avoid ReDoS.

_USERNAME_RE = re.compile(r"\A[A-Za-z0-9._-]{%d,%d}\Z" % (USERNAME_MIN_LENGTH,
                                                          USERNAME_MAX_LENGTH))

_EMAIL_LOCAL_RE = re.compile(r"\A[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
                             r"(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*\Z")

_EMAIL_LABEL_RE = re.compile(r"\A[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\Z")

_UPPERCASE_RE = re.compile(r"[A-Z]")
_LOWERCASE_RE = re.compile(r"[a-z]")
_DIGIT_RE = re.compile(r"[0-9]")
_SPECIAL_RE = re.compile(r"[!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~]")

FIELD_USERNAME = "username"
FIELD_EMAIL = "email"
FIELD_PASSWORD = "password"


def _is_text(value: Any) -> bool:
    """True only for genuine ``str`` values (bool/int/bytes are rejected)."""
    return isinstance(value, str)


def _has_forbidden_chars(value: str) -> bool:
    """Reject NUL, control characters and other non-printable code points."""
    for char in value:
        if char in ("\x00", "\r", "\n", "\t"):
            return True
        if unicodedata.category(char) in ("Cc", "Cf", "Cs", "Co", "Cn"):
            return True
    return False


def _valid_username(value: Any) -> bool:
    if not _is_text(value):
        return False
    if _has_forbidden_chars(value):
        return False
    # Length is measured on the raw string; surrounding whitespace is not
    # silently trimmed away, it simply makes the username invalid.
    if value != value.strip():
        return False
    return _USERNAME_RE.match(value) is not None


def _valid_email(value: Any) -> bool:
    if not _is_text(value):
        return False
    if _has_forbidden_chars(value):
        return False
    if value != value.strip():
        return False
    if not 3 <= len(value) <= EMAIL_MAX_LENGTH:
        return False
    if value.count("@") != 1:
        return False

    local, _, domain = value.partition("@")
    if not local or not domain:
        return False
    if len(local) > EMAIL_LOCAL_MAX_LENGTH:
        return False
    if _EMAIL_LOCAL_RE.match(local) is None:
        return False

    if domain.startswith(".") or domain.endswith(".") or ".." in domain:
        return False
    labels = domain.split(".")
    if len(labels) < 2:
        return False
    for label in labels:
        if not label or len(label) > EMAIL_LABEL_MAX_LENGTH:
            return False
        if _EMAIL_LABEL_RE.match(label) is None:
            return False
    # Top-level label must be alphabetic (no all-numeric TLDs).
    if not labels[-1].isalpha() or len(labels[-1]) < 2:
        return False
    return True


def _valid_password(value: Any) -> bool:
    """Check password complexity. Never logs or returns the value itself."""
    if not _is_text(value):
        return False
    if len(value) < PASSWORD_MIN_LENGTH or len(value) > PASSWORD_MAX_LENGTH:
        return False
    if "\x00" in value:
        return False
    if _UPPERCASE_RE.search(value) is None:
        return False
    if _LOWERCASE_RE.search(value) is None:
        return False
    if _DIGIT_RE.search(value) is None:
        return False
    if _SPECIAL_RE.search(value) is None:
        return False
    return True


def validate_registration(username, email, password) -> Dict[str, Any]:
    """Validate registration data.

    Returns ``{"valid": bool, "errors": [...]}`` where ``errors`` holds the
    lowercase names of the fields that failed: ``"username"``, ``"email"``
    and/or ``"password"``. No submitted value — least of all the password —
    is ever included in the result.
    """
    errors: List[str] = []

    try:
        if not _valid_username(username):
            errors.append(FIELD_USERNAME)
    except Exception:  # fail closed on any unexpected input behaviour
        errors.append(FIELD_USERNAME)

    try:
        if not _valid_email(email):
            errors.append(FIELD_EMAIL)
    except Exception:
        errors.append(FIELD_EMAIL)

    try:
        if not _valid_password(password):
            errors.append(FIELD_PASSWORD)
    except Exception:
        errors.append(FIELD_PASSWORD)

    return {"valid": not errors, "errors": errors}
