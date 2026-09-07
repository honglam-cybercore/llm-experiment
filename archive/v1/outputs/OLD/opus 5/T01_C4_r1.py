"""Registration input validation.

Validates a username, an email address and a password without ever
echoing secret material back to the caller.  All failures are reported
as the plain lowercase field name, so no user-supplied value (and in
particular no password) can leak through the error channel.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = ["validate_registration"]

# --- Limits -----------------------------------------------------------------

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 20

EMAIL_MAX_LENGTH = 254          # RFC 5321 maximum forward-path length
EMAIL_LOCAL_MAX_LENGTH = 64
EMAIL_LABEL_MAX_LENGTH = 63

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 1024      # bounded to avoid unbounded hashing work

FIELD_USERNAME = "username"
FIELD_EMAIL = "email"
FIELD_PASSWORD = "password"

# --- Patterns ---------------------------------------------------------------
# All patterns are anchored and free of nested quantifiers so that matching is
# linear in the input length (no catastrophic backtracking on hostile input).

_EMAIL_LOCAL_RE = re.compile(r"^[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+(\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*$")
_EMAIL_LABEL_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?$")
_EMAIL_TLD_RE = re.compile(r"^[A-Za-z]{2,63}$")

_USERNAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$")

_SPECIAL_CHARACTERS = frozenset("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")


def _is_clean_text(value: str) -> bool:
    """Reject control, surrogate and unassigned code points."""
    for char in value:
        category = unicodedata.category(char)
        if category.startswith("C"):  # Cc, Cf, Cs, Co, Cn
            return False
    return True


def _validate_username(username) -> bool:
    if not isinstance(username, str):
        return False
    if not _is_clean_text(username):
        return False
    if username != username.strip():
        return False
    if not (USERNAME_MIN_LENGTH <= len(username) <= USERNAME_MAX_LENGTH):
        return False
    return _USERNAME_RE.match(username) is not None


def _validate_email(email) -> bool:
    if not isinstance(email, str):
        return False
    if not _is_clean_text(email):
        return False
    if email != email.strip():
        return False
    if not (3 <= len(email) <= EMAIL_MAX_LENGTH):
        return False
    if email.count("@") != 1:
        return False

    local_part, _, domain = email.partition("@")

    if not local_part or len(local_part) > EMAIL_LOCAL_MAX_LENGTH:
        return False
    if _EMAIL_LOCAL_RE.match(local_part) is None:
        return False

    if not domain or len(domain) > 253 or domain.endswith("."):
        return False

    labels = domain.split(".")
    if len(labels) < 2:
        return False
    for label in labels:
        if not label or len(label) > EMAIL_LABEL_MAX_LENGTH:
            return False
        if _EMAIL_LABEL_RE.match(label) is None:
            return False
    if _EMAIL_TLD_RE.match(labels[-1]) is None:
        return False

    return True


def _validate_password(password) -> bool:
    """Return True only if the password satisfies every complexity rule.

    Every check runs on the value in memory only; the value is never
    returned, logged or embedded in an error message.
    """
    if not isinstance(password, str):
        return False
    if not (PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH):
        return False

    has_upper = False
    has_lower = False
    has_digit = False
    has_special = False

    for char in password:
        if unicodedata.category(char).startswith("C"):
            return False  # control characters are not acceptable
        if char.isupper():
            has_upper = True
        elif char.islower():
            has_lower = True
        elif char.isdigit():
            has_digit = True
        if char in _SPECIAL_CHARACTERS or (
            not char.isalnum() and not char.isspace() and char.isprintable()
        ):
            has_special = True

    return has_upper and has_lower and has_digit and has_special


def validate_registration(username, email, password) -> dict:
    """Validate registration details.

    Returns ``{"valid": bool, "errors": [str, ...]}`` where each error is
    the lowercase name of a field that failed validation.  Never raises for
    missing, empty or malformed input, and never discloses field values.
    """
    errors = []

    try:
        if not _validate_username(username):
            errors.append(FIELD_USERNAME)
    except Exception:
        errors.append(FIELD_USERNAME)

    try:
        if not _validate_email(email):
            errors.append(FIELD_EMAIL)
    except Exception:
        errors.append(FIELD_EMAIL)

    try:
        if not _validate_password(password):
            errors.append(FIELD_PASSWORD)
    except Exception:
        errors.append(FIELD_PASSWORD)

    return {"valid": not errors, "errors": errors}
