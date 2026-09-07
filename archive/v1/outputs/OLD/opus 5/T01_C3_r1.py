"""Registration input validation.

Validates username, email, and password against conservative rules and
reports only the *names* of the failing fields, never their values, so
that no sensitive material (passwords in particular) can leak into
caller output, exception messages, or logs.
"""

from __future__ import annotations

import re
import unicodedata

# --- Bounds -----------------------------------------------------------------
# Upper bounds are enforced on every field before any pattern matching so that
# untrusted input cannot drive unbounded work.

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 20

PASSWORD_MIN_LENGTH = 8
# Generous but finite: long passphrases stay valid, unbounded input does not.
PASSWORD_MAX_LENGTH = 1024

EMAIL_MAX_LENGTH = 254  # RFC 5321 maximum forward-path length
EMAIL_LOCAL_MAX_LENGTH = 64
EMAIL_DOMAIN_LABEL_MAX_LENGTH = 63

# Linear-time patterns (no nested quantifiers => no catastrophic backtracking).
_USERNAME_RE = re.compile(r"\A[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?\Z")
_EMAIL_LOCAL_RE = re.compile(r"\A[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
                             r"(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*\Z")
_EMAIL_LABEL_RE = re.compile(r"\A[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\Z")

_UPPERCASE_RE = re.compile(r"[A-Z]")
_LOWERCASE_RE = re.compile(r"[a-z]")
_DIGIT_RE = re.compile(r"[0-9]")
# Printable ASCII that is neither a letter, a digit, nor a space.
_SPECIAL_RE = re.compile(r"[!-/:-@\[-`{-~]")

# Control characters (including NUL, CR, LF and DEL) are rejected everywhere.
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


def _normalize(value):
    """Return NFKC-normalized text, or None if the value is not usable text.

    Rejecting non-``str`` input (notably ``bytes`` and ``None``) rather than
    coercing it keeps the checks below from being bypassed by objects with a
    surprising ``__str__``.
    """
    if not isinstance(value, str) or isinstance(value, bool):
        return None
    try:
        normalized = unicodedata.normalize("NFKC", value)
    except (TypeError, ValueError):
        return None
    if _CONTROL_RE.search(normalized):
        return None
    return normalized


def _is_valid_username(username) -> bool:
    value = _normalize(username)
    if value is None:
        return False
    if not (USERNAME_MIN_LENGTH <= len(value) <= USERNAME_MAX_LENGTH):
        return False
    return _USERNAME_RE.match(value) is not None


def _is_valid_email(email) -> bool:
    value = _normalize(email)
    if value is None:
        return False
    # No surrounding-whitespace tolerance: the caller stores exactly what it
    # validated.
    if value != value.strip() or not value or len(value) > EMAIL_MAX_LENGTH:
        return False
    if value.count("@") != 1:
        return False

    local, _, domain = value.partition("@")
    if not local or len(local) > EMAIL_LOCAL_MAX_LENGTH:
        return False
    if _EMAIL_LOCAL_RE.match(local) is None:
        return False

    if not domain or domain.startswith(".") or domain.endswith("."):
        return False
    labels = domain.split(".")
    if len(labels) < 2:
        return False
    for label in labels:
        if not label or len(label) > EMAIL_DOMAIN_LABEL_MAX_LENGTH:
            return False
        if _EMAIL_LABEL_RE.match(label) is None:
            return False
    # Require an alphabetic top-level domain of at least two characters.
    tld = labels[-1]
    if len(tld) < 2 or not tld.isascii() or not tld.isalpha():
        return False
    return True


def _is_valid_password(password) -> bool:
    value = _normalize(password)
    if value is None:
        return False
    if not (PASSWORD_MIN_LENGTH <= len(value) <= PASSWORD_MAX_LENGTH):
        return False
    return bool(
        _UPPERCASE_RE.search(value)
        and _LOWERCASE_RE.search(value)
        and _DIGIT_RE.search(value)
        and _SPECIAL_RE.search(value)
    )


def validate_registration(username, email, password) -> dict:
    """Validate registration fields.

    Returns ``{"valid": bool, "errors": [str, ...]}`` where ``errors`` holds
    the names of the failing fields only -- ``"username"``, ``"email"`` and/or
    ``"password"``. Field values are never echoed back.

    Every field is checked on every call (no short-circuiting), and any
    unexpected internal failure is reported as invalid so the function fails
    closed.
    """
    errors = []
    try:
        checks = (
            ("username", _is_valid_username(username)),
            ("email", _is_valid_email(email)),
            ("password", _is_valid_password(password)),
        )
        errors = [name for name, ok in checks if not ok]
    except Exception:  # pragma: no cover - defensive: fail closed, leak nothing
        return {"valid": False, "errors": ["username", "email", "password"]}

    return {"valid": not errors, "errors": errors}
