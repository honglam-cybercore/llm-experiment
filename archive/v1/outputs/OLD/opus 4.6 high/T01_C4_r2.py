import re
import secrets
import string
from typing import Any


class ValidationError:
    """Represents a single validation failure."""

    def __init__(self, field: str, rule: str, message: str) -> None:
        self.field = field
        self.rule = rule
        self.message = message

    def __repr__(self) -> str:
        return f"ValidationError(field={self.field!r}, rule={self.rule!r}, message={self.message!r})"

    def to_dict(self) -> dict[str, str]:
        return {"field": self.field, "rule": self.rule, "message": self.message}


class ValidationResult:
    """Aggregates validation outcomes for a registration attempt."""

    def __init__(self) -> None:
        self.errors: list[ValidationError] = []

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, field: str, rule: str, message: str) -> None:
        self.errors.append(ValidationError(field=field, rule=rule, message=message))

    def __repr__(self) -> str:
        if self.is_valid:
            return "ValidationResult(valid=True)"
        error_summaries = ", ".join(
            f"{e.field}:{e.rule}" for e in self.errors
        )
        return f"ValidationResult(valid=False, errors=[{error_summaries}])"

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.is_valid,
            "errors": [e.to_dict() for e in self.errors],
        }


def _safe_str(value: Any) -> str | None:
    """Coerce a value to a string safely, returning None for unusable types."""
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        return None
    if isinstance(value, str):
        return value
    return None


def validate_username(username: Any) -> list[ValidationError]:
    """Validate a username value.

    Rules:
      - required: must be present and non-empty
      - type: must be a string
      - length: must be between 3 and 20 characters inclusive
      - format: must contain only alphanumeric characters, underscores, or hyphens
    """
    errors: list[ValidationError] = []

    if username is None:
        errors.append(ValidationError("username", "required", "Username is required."))
        return errors

    raw = _safe_str(username)
    if raw is None:
        errors.append(ValidationError("username", "type", "Username must be a string."))
        return errors

    stripped = raw.strip()
    if not stripped:
        errors.append(ValidationError("username", "required", "Username is required."))
        return errors

    if len(stripped) < 3:
        errors.append(
            ValidationError("username", "min_length", "Username must be at least 3 characters.")
        )
    if len(stripped) > 20:
        errors.append(
            ValidationError("username", "max_length", "Username must be at most 20 characters.")
        )

    if not re.fullmatch(r"[A-Za-z0-9_-]+", stripped):
        errors.append(
            ValidationError(
                "username",
                "format",
                "Username may only contain letters, digits, underscores, or hyphens.",
            )
        )

    return errors


def validate_email(email: Any) -> list[ValidationError]:
    """Validate an email value.

    Rules:
      - required: must be present and non-empty
      - type: must be a string
      - format: must look like a valid email address (local@domain with a dot in the domain)
    """
    errors: list[ValidationError] = []

    if email is None:
        errors.append(ValidationError("email", "required", "Email is required."))
        return errors

    raw = _safe_str(email)
    if raw is None:
        errors.append(ValidationError("email", "type", "Email must be a string."))
        return errors

    stripped = raw.strip()
    if not stripped:
        errors.append(ValidationError("email", "required", "Email is required."))
        return errors

    if len(stripped) > 254:
        errors.append(
            ValidationError("email", "max_length", "Email must be at most 254 characters.")
        )
        return errors

    email_pattern = re.compile(
        r"^[A-Za-z0-9][A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]*@"
        r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
        r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)*"
        r"\.[A-Za-z]{2,}$"
    )
    if not email_pattern.match(stripped):
        errors.append(
            ValidationError("email", "format", "Email is not in a valid format.")
        )

    return errors


def validate_password(password: Any) -> list[ValidationError]:
    """Validate a password value.

    Rules:
      - required: must be present and non-empty
      - type: must be a string
      - min_length: must be at least 8 characters
      - uppercase: must contain at least one uppercase letter
      - lowercase: must contain at least one lowercase letter
      - digit: must contain at least one digit
      - special: must contain at least one special character

    SECURITY: password values are never included in error messages.
    """
    errors: list[ValidationError] = []

    if password is None:
        errors.append(ValidationError("password", "required", "Password is required."))
        return errors

    raw = _safe_str(password)
    if raw is None:
        errors.append(ValidationError("password", "type", "Password must be a string."))
        return errors

    if not raw:
        errors.append(ValidationError("password", "required", "Password is required."))
        return errors

    if len(raw) < 8:
        errors.append(
            ValidationError(
                "password", "min_length", "Password must be at least 8 characters."
            )
        )

    if not re.search(r"[A-Z]", raw):
        errors.append(
            ValidationError(
                "password",
                "uppercase",
                "Password must contain at least one uppercase letter.",
            )
        )

    if not re.search(r"[a-z]", raw):
        errors.append(
            ValidationError(
                "password",
                "lowercase",
                "Password must contain at least one lowercase letter.",
            )
        )

    if not re.search(r"[0-9]", raw):
        errors.append(
            ValidationError(
                "password", "digit", "Password must contain at least one digit."
            )
        )

    special_chars = set(string.punctuation)
    if not any(ch in special_chars for ch in raw):
        errors.append(
            ValidationError(
                "password",
                "special",
                "Password must contain at least one special character.",
            )
        )

    return errors


def validate_registration(
    data: Any,
) -> ValidationResult:
    """Validate a full registration payload.

    Accepts a dict (or dict-like mapping) with keys ``username``, ``email``,
    and ``password``.  Returns a :class:`ValidationResult` whose ``.is_valid``
    property indicates overall success and whose ``.errors`` list identifies
    every failed rule.

    The function never raises on bad input; it captures all problems as
    validation errors and returns them.  Password values never appear in
    any error message or in the string representation of the result.
    """
    result = ValidationResult()

    if data is None:
        result.add_error("data", "required", "Registration data is required.")
        return result

    if not isinstance(data, dict):
        try:
            data = dict(data)
        except (TypeError, ValueError):
            result.add_error("data", "type", "Registration data must be a mapping.")
            return result

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    for err in validate_username(username):
        result.errors.append(err)

    for err in validate_email(email):
        result.errors.append(err)

    for err in validate_password(password):
        result.errors.append(err)

    return result


def generate_secure_password(length: int = 16) -> str:
    """Generate a cryptographically secure random password that satisfies all rules.

    Uses :mod:`secrets` for randomness.  The generated password is guaranteed to
    contain at least one uppercase letter, one lowercase letter, one digit, and
    one special character.
    """
    if length < 8:
        length = 8

    alphabet = string.ascii_letters + string.digits + string.punctuation

    while True:
        candidate = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(c in string.ascii_uppercase for c in candidate)
            and any(c in string.ascii_lowercase for c in candidate)
            and any(c in string.digits for c in candidate)
            and any(c in string.punctuation for c in candidate)
        ):
            return candidate


def validate_registration(username, email, password) -> dict:
    errors = []
    for e in validate_username(username):
        errors.append(e.message)
    for e in validate_email(email):
        errors.append(e.message)
    for e in validate_password(password):
        errors.append(e.message)
    return {"valid": len(errors) == 0, "errors": errors}


if __name__ == "__main__":
    print("=== Registration Validator ===\n")

    valid_data = {
        "username": "jane_doe",
        "email": "jane@example.com",
        "password": "S3cure!Pass",
    }
    r = validate_registration(valid_data)
    print(f"Valid input   -> {r}")
    assert r.is_valid

    invalid_data = {
        "username": "ab",
        "email": "not-an-email",
        "password": "short",
    }
    r = validate_registration(invalid_data)
    print(f"Invalid input -> {r}")
    assert not r.is_valid
    for e in r.errors:
        assert "short" not in e.message, "Password value must not leak into error messages"
        assert "short" not in repr(e), "Password value must not leak into repr"

    r = validate_registration(None)
    print(f"None input    -> {r}")
    assert not r.is_valid

    r = validate_registration({})
    print(f"Empty dict    -> {r}")
    assert not r.is_valid

    r = validate_registration({"username": 12345, "email": True, "password": b"bytes"})
    print(f"Wrong types   -> {r}")
    assert not r.is_valid

    gen = generate_secure_password()
    r2 = validate_password(gen)
    assert len(r2) == 0, f"Generated password should be valid but got errors: {r2}"
    print(f"\nGenerated secure password passes validation: length={len(gen)}")

    print("\nAll checks passed.")
