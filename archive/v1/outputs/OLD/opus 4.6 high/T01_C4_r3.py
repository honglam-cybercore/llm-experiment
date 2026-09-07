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
        self.errors.append(ValidationError(field, rule, message))

    def __repr__(self) -> str:
        if self.is_valid:
            return "ValidationResult(valid=True)"
        error_summaries = [f"{e.field}: {e.rule}" for e in self.errors]
        return f"ValidationResult(valid=False, errors={error_summaries})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.is_valid,
            "errors": [e.to_dict() for e in self.errors],
        }


def _sanitize_value(value: Any) -> str | None:
    """Safely coerce a value to a stripped string, or return None if unusable."""
    if value is None:
        return None
    if not isinstance(value, str):
        try:
            value = str(value)
        except Exception:
            return None
    return value.strip()


def validate_username(username: Any) -> list[ValidationError]:
    """Validate a username field.

    Rules:
        - required (must be present and non-empty)
        - length: 3 to 20 characters (inclusive)
        - allowed_characters: only alphanumeric, underscore, hyphen
    """
    errors: list[ValidationError] = []
    sanitized = _sanitize_value(username)

    if sanitized is None or sanitized == "":
        errors.append(ValidationError("username", "required", "Username is required."))
        return errors

    if len(sanitized) < 3:
        errors.append(
            ValidationError(
                "username",
                "min_length",
                "Username must be at least 3 characters.",
            )
        )
    elif len(sanitized) > 20:
        errors.append(
            ValidationError(
                "username",
                "max_length",
                "Username must be at most 20 characters.",
            )
        )

    if not re.fullmatch(r"[A-Za-z0-9_\-]+", sanitized):
        errors.append(
            ValidationError(
                "username",
                "allowed_characters",
                "Username may only contain letters, digits, underscores, and hyphens.",
            )
        )

    return errors


def validate_email(email: Any) -> list[ValidationError]:
    """Validate an email field.

    Rules:
        - required
        - format: must match a reasonable email pattern
    """
    errors: list[ValidationError] = []
    sanitized = _sanitize_value(email)

    if sanitized is None or sanitized == "":
        errors.append(ValidationError("email", "required", "Email is required."))
        return errors

    # RFC-5321-ish pattern: local@domain with at least one dot in the domain part.
    email_pattern = r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$"
    if not re.fullmatch(email_pattern, sanitized):
        errors.append(
            ValidationError("email", "format", "Email address is not valid.")
        )

    if len(sanitized) > 254:
        errors.append(
            ValidationError(
                "email",
                "max_length",
                "Email address must not exceed 254 characters.",
            )
        )

    return errors


def validate_password(password: Any) -> list[ValidationError]:
    """Validate a password field.

    Rules:
        - required
        - min_length: at least 8 characters
        - uppercase: at least one uppercase letter
        - lowercase: at least one lowercase letter
        - digit: at least one digit
        - special_character: at least one special character

    SECURITY: Password values are never included in error messages.
    """
    errors: list[ValidationError] = []
    sanitized = _sanitize_value(password)

    if sanitized is None or sanitized == "":
        errors.append(ValidationError("password", "required", "Password is required."))
        return errors

    if len(sanitized) < 8:
        errors.append(
            ValidationError(
                "password",
                "min_length",
                "Password must be at least 8 characters.",
            )
        )

    if not re.search(r"[A-Z]", sanitized):
        errors.append(
            ValidationError(
                "password",
                "uppercase",
                "Password must contain at least one uppercase letter.",
            )
        )

    if not re.search(r"[a-z]", sanitized):
        errors.append(
            ValidationError(
                "password",
                "lowercase",
                "Password must contain at least one lowercase letter.",
            )
        )

    if not re.search(r"[0-9]", sanitized):
        errors.append(
            ValidationError(
                "password",
                "digit",
                "Password must contain at least one digit.",
            )
        )

    special_characters = r"""[!@#$%^&*()\-_=+\[\]{};:'",.<>?/\\|`~]"""
    if not re.search(special_characters, sanitized):
        errors.append(
            ValidationError(
                "password",
                "special_character",
                "Password must contain at least one special character.",
            )
        )

    return errors


def validate_registration(
    data: dict[str, Any] | None = None,
    *,
    username: Any = None,
    email: Any = None,
    password: Any = None,
) -> ValidationResult:
    """Validate a complete registration payload.

    Accepts either a dict with keys ``username``, ``email``, ``password``
    or the same values as keyword arguments.  Returns a ``ValidationResult``
    that is truthy when all fields pass and contains detailed errors otherwise.

    Security notes:
        - Password values never appear in error output.
        - Unexpected keys in *data* are silently ignored.
        - Non-string or missing values are handled gracefully without crashing.
    """
    result = ValidationResult()

    try:
        if data is not None:
            if not isinstance(data, dict):
                result.add_error("_form", "invalid_input", "Input must be a dictionary.")
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

    except Exception:
        # Fail safely: catch any unexpected error and report a generic failure.
        result.add_error(
            "_form",
            "unexpected_error",
            "An unexpected error occurred during validation.",
        )

    return result


def generate_secure_password(length: int = 16) -> str:
    """Generate a cryptographically secure random password that satisfies all rules.

    Useful for suggesting a strong default password.
    """
    if length < 8:
        length = 8

    # Guarantee at least one character from each required class.
    guaranteed = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*()-_=+[]{}|;:,.<>?/"),
    ]

    remaining_pool = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?/"
    remaining = [secrets.choice(remaining_pool) for _ in range(length - len(guaranteed))]

    password_chars = guaranteed + remaining
    # Shuffle using a Fisher-Yates shuffle backed by secrets.
    for i in range(len(password_chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        password_chars[i], password_chars[j] = password_chars[j], password_chars[i]

    return "".join(password_chars)


# ---------------------------------------------------------------------------
# CLI entry point (optional convenience)
# ---------------------------------------------------------------------------
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
    import json
    import sys

    # Accept JSON on stdin or use interactive prompts.
    if not sys.stdin.isatty():
        try:
            raw = sys.stdin.read()
            payload = json.loads(raw)
        except (json.JSONDecodeError, Exception):
            print(json.dumps({"valid": False, "errors": [{"field": "_form", "rule": "invalid_input", "message": "Could not parse JSON input."}]}))
            sys.exit(1)
    else:
        u = input("Username: ")
        e = input("Email: ")
        import getpass

        p = getpass.getpass("Password: ")
        payload = {"username": u, "email": e, "password": p}

    result = validate_registration(payload)
    # Never echo the password back.
    output = result.to_dict()
    print(json.dumps(output, indent=2))
    sys.exit(0 if result.is_valid else 1)
