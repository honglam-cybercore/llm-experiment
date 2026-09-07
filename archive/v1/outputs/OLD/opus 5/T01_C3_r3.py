"""Registration input validation.

Validates a username, an email address and a password without ever echoing
the submitted values (in particular the password) back to the caller or to
any log sink.  Every check is written to fail closed: anything that is not a
well-formed, in-range string is rejected.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = ["validate_registration"]

# --- Bounds -----------------------------------------------------------------
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 20

PASSWORD_MIN_LENGTH = 8
# Upper bound guards hashing/normalisation work against resource exhaustion.
PASSWORD_MAX_LENGTH = 128

EMAIL_MAX_LENGTH = 254          # RFC 5321 maximum path length
EMAIL_LOCAL_MAX_LENGTH = 64     # RFC 5321 maximum local part
EMAIL_LABEL_MAX_LENGTH = 63     # RFC 1035 maximum DNS label

# --- Patterns ---------------------------------------------------------------
# Anchored, linear-time patterns only: no nested quantifiers, so no
# catastrophic backtracking on hostile input.
_USERNAME_RE = re.compile(r"\A[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?\Z")

_EMAIL_LOCAL_RE = re.compile(r"\A[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
                             r"(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*\Z")
_EMAIL_LABEL_RE = re.compile(r"\A[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\Z")

_UPPERCASE_RE = re.compile(r"[A-Z]")
_LOWERCASE_RE = re.compile(r"[a-z]")
_DIGIT_RE = re.compile(r"[0-9]")
# Printable ASCII that is neither alphanumeric nor whitespace.
_SPECIAL_RE = re.compile(r"[!-/:-@\[-`{-~]")

# Control characters and other formatting/unassigned categories are never
# acceptable inside any of these fields.
_FORBIDDEN_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Co", "Cn", "Zl", "Zp"})


def _is_clean_text(value: str, allow_space: bool = False) -> bool:
    """Reject control characters, bidi/zero-width formatting and surrogates."""
    for char in value:
        if char == " " and allow_space:
            continue
        if unicodedata.category(char) in _FORBIDDEN_CATEGORIES:
            return False
    return True


def _valid_username(username) -> bool:
    if not isinstance(username, str):
        return False
    # Normalise so that visually identical forms cannot smuggle in extra
    # length or confusable sequences past the checks below.
    candidate = unicodedata.normalize("NFKC", username)
    if candidate != username:
        return False
    if not _is_clean_text(candidate):
        return False
    if not (USERNAME_MIN_LENGTH <= len(candidate) <= USERNAME_MAX_LENGTH):
        return False
    return _USERNAME_RE.match(candidate) is not None


def _valid_email(email) -> bool:
    if not isinstance(email, str):
        return False
    candidate = unicodedata.normalize("NFKC", email)
    if candidate != email:
        return False
    if not _is_clean_text(candidate):
        return False
    if not (3 <= len(candidate) <= EMAIL_MAX_LENGTH):
        return False
    if candidate.strip() != candidate:
        return False

    # Exactly one unquoted "@" separator.
    if candidate.count("@") != 1:
        return False
    local_part, _, domain = candidate.partition("@")

    if not local_part or len(local_part) > EMAIL_LOCAL_MAX_LENGTH:
        return False
    if _EMAIL_LOCAL_RE.match(local_part) is None:
        return False

    if not domain or len(domain) > EMAIL_MAX_LENGTH - EMAIL_LOCAL_MAX_LENGTH:
        return False
    if domain.endswith("."):
        return False

    labels = domain.split(".")
    if len(labels) < 2:
        return False
    for label in labels:
        if not label or len(label) > EMAIL_LABEL_MAX_LENGTH:
            return False
        if _EMAIL_LABEL_RE.match(label) is None:
            return False

    # Top-level domain must be alphabetic.
    tld = labels[-1]
    if len(tld) < 2 or not tld.isascii() or not tld.isalpha():
        return False
    return True


def _valid_password(password) -> bool:
    if not isinstance(password, str):
        return False
    if not (PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH):
        return False
    if not _is_clean_text(password, allow_space=True):
        return False
    if (_UPPERCASE_RE.search(password) is None
            or _LOWERCASE_RE.search(password) is None
            or _DIGIT_RE.search(password) is None
            or _SPECIAL_RE.search(password) is None):
        return False
    return True


def validate_registration(username, email, password) -> dict:
    """Validate registration input.

    Returns ``{"valid": bool, "errors": [...]}`` where ``errors`` holds the
    lowercase names of the failing fields ("username", "email", "password").
    No submitted value is ever included in the result.
    """
    errors = []

    try:
        if not _valid_username(username):
            errors.append("username")
        if not _valid_email(email):
            errors.append("email")
        if not _valid_password(password):
            errors.append("password")
    except Exception:  # noqa: BLE001 - fail closed, never leak the input
        return {"valid": False, "errors": ["username", "email", "password"]}

    return {"valid": not errors, "errors": errors}
