"""Registration input validation.

Validates a username, an email address and a password, reporting which
field failed without ever echoing the submitted values (in particular the
password) back to the caller, to logs, or into exception messages.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = ["validate_registration"]

# --- Bounds -----------------------------------------------------------------
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 20

PASSWORD_MIN_LENGTH = 8
# Upper bound guards against memory/CPU exhaustion from unbounded input.
PASSWORD_MAX_LENGTH = 128

EMAIL_MAX_LENGTH = 254          # RFC 5321 maximum forward-path length
EMAIL_LOCAL_MAX_LENGTH = 64
EMAIL_LABEL_MAX_LENGTH = 63

# Any input longer than this is rejected before pattern matching runs.
ABSOLUTE_MAX_INPUT_LENGTH = 4096

# --- Patterns ---------------------------------------------------------------
# All patterns are linear-time (no nested quantifiers) to avoid ReDoS.
_USERNAME_RE = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._-]*[A-Za-z0-9]\Z")

_EMAIL_LOCAL_RE = re.compile(r"\A[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
                             r"(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*\Z")
_EMAIL_LABEL_RE = re.compile(r"\A[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\Z")
_EMAIL_TLD_RE = re.compile(r"\A[A-Za-z]{2,63}\Z")

_UPPER_RE = re.compile(r"[A-Z]")
_LOWER_RE = re.compile(r"[a-z]")
_DIGIT_RE = re.compile(r"[0-9]")
_SPECIAL_RE = re.compile(r"[!-/:-@\[-`{-~]")   # printable ASCII punctuation

FIELD_USERNAME = "username"
FIELD_EMAIL = "email"
FIELD_PASSWORD = "password"


def _as_text(value):
    """Return ``value`` as a ``str`` if it is safe text, else ``None``.

    Non-string input (``None``, numbers, bytes, arbitrary objects) is treated
    as invalid rather than coerced, so nothing unexpected reaches the
    validators and no ``__str__`` side effects are triggered.
    """
    if not isinstance(value, str):
        return None
    if len(value) > ABSOLUTE_MAX_INPUT_LENGTH:
        return None
    return value


def _has_forbidden_characters(text):
    """True if ``text`` holds control, format, surrogate or unassigned chars."""
    for char in text:
        if unicodedata.category(char) in ("Cc", "Cf", "Cs", "Co", "Cn"):
            return True
    return False


def _is_valid_username(value):
    text = _as_text(value)
    if text is None:
        return False
    if text != text.strip():
        return False
    if _has_forbidden_characters(text):
        return False
    if not (USERNAME_MIN_LENGTH <= len(text) <= USERNAME_MAX_LENGTH):
        return False
    if ".." in text or "__" in text or "--" in text:
        return False
    return _USERNAME_RE.match(text) is not None


def _is_valid_email(value):
    text = _as_text(value)
    if text is None:
        return False
    if text != text.strip():
        return False
    if _has_forbidden_characters(text):
        return False
    if not 3 <= len(text) <= EMAIL_MAX_LENGTH:
        return False
    if text.count("@") != 1:
        return False

    local_part, _, domain = text.partition("@")

    if not local_part or len(local_part) > EMAIL_LOCAL_MAX_LENGTH:
        return False
    if _EMAIL_LOCAL_RE.match(local_part) is None:
        return False

    if not domain or len(domain) > EMAIL_MAX_LENGTH - EMAIL_LOCAL_MAX_LENGTH:
        return False
    if domain.startswith(".") or domain.endswith(".") or ".." in domain:
        return False

    labels = domain.split(".")
    if len(labels) < 2:
        return False
    for label in labels:
        if not 0 < len(label) <= EMAIL_LABEL_MAX_LENGTH:
            return False
        if _EMAIL_LABEL_RE.match(label) is None:
            return False
    if _EMAIL_TLD_RE.match(labels[-1]) is None:
        return False
    return True


def _is_valid_password(value):
    text = _as_text(value)
    if text is None:
        return False
    if not (PASSWORD_MIN_LENGTH <= len(text) <= PASSWORD_MAX_LENGTH):
        return False
    # Reject control characters, but allow every other printable character.
    for char in text:
        if unicodedata.category(char) in ("Cc", "Cs", "Cn"):
            return False
    if _UPPER_RE.search(text) is None:
        return False
    if _LOWER_RE.search(text) is None:
        return False
    if _DIGIT_RE.search(text) is None:
        return False
    if _SPECIAL_RE.search(text) is None:
        return False
    return True


def validate_registration(username, email, password) -> dict:
    """Validate registration fields.

    Returns ``{"valid": bool, "errors": [str, ...]}`` where ``errors``
    contains the lowercase name of each failing field
    (``"username"``, ``"email"``, ``"password"``) and is empty when valid.

    Never raises for untrusted input, and never includes any submitted
    value -- especially the password -- in its output.
    """
    errors = []

    checks = (
        (FIELD_USERNAME, _is_valid_username, username),
        (FIELD_EMAIL, _is_valid_email, email),
        (FIELD_PASSWORD, _is_valid_password, password),
    )

    for field_name, check, value in checks:
        try:
            ok = check(value)
        except Exception:
            # Fail closed: any unexpected condition marks the field invalid.
            # The exception is deliberately not propagated or logged, so no
            # sensitive value can leak through a traceback or message.
            ok = False
        if not ok:
            errors.append(field_name)

    return {"valid": not errors, "errors": errors}
