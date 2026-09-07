import re
import string
from typing import Any


class ValidationResult:
    """Represents the result of a validation operation."""

    def __init__(self) -> None:
        self.is_valid: bool = True
        self.errors: dict[str, list[str]] = {}

    def add_error(self, field: str, message: str) -> None:
        self.is_valid = False
        if field not in self.errors:
            self.errors[field] = []
        self.errors[field].append(message)

    def __repr__(self) -> str:
        if self.is_valid:
            return "ValidationResult(valid=True)"
        return f"ValidationResult(valid=False, errors={self.errors})"


def _sanitize_value(value: Any) -> str | None:
    """Safely convert a value to a string, returning None if empty or not a string type."""
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    return value


def validate_username(username: Any) -> list[str]:
    """Validate a username field.

    Rules:
    - Must be a non-empty string.
    - Must be between 3 and 20 characters (inclusive).
    - Must contain only alphanumeric characters, underscores, or hyphens.

    Returns a list of error messages (empty if valid).
    """
    errors: list[str] = []
    sanitized = _sanitize_value(username)

    if sanitized is None or sanitized.strip() == "":
        errors.append("Username is required.")
        return errors

    length = len(sanitized)
    if length < 3:
        errors.append("Username must be at least 3 characters long.")
    if length > 20:
        errors.append("Username must be at most 20 characters long.")

    if not re.fullmatch(r"[A-Za-z0-9_\-]+", sanitized):
        errors.append(
            "Username must contain only alphanumeric characters, underscores, or hyphens."
        )

    return errors


def validate_email(email: Any) -> list[str]:
    """Validate an email field.

    Rules:
    - Must be a non-empty string.
    - Must match a reasonable email pattern (local@domain.tld).
    - Maximum length of 254 characters (per RFC 5321).

    Returns a list of error messages (empty if valid).
    """
    errors: list[str] = []
    sanitized = _sanitize_value(email)

    if sanitized is None or sanitized.strip() == "":
        errors.append("Email is required.")
        return errors

    if len(sanitized) > 254:
        errors.append("Email must not exceed 254 characters.")

    email_pattern = re.compile(
        r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+"
        r"@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
        r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
    )
    if not email_pattern.match(sanitized):
        errors.append("Email format is invalid.")

    return errors


def validate_password(password: Any) -> list[str]:
    """Validate a password field.

    Rules:
    - Must be a non-empty string.
    - Must be at least 8 characters long.
    - Must contain at least one uppercase letter.
    - Must contain at least one lowercase letter.
    - Must contain at least one digit.
    - Must contain at least one special character.

    Password values are never included in error messages.

    Returns a list of error messages (empty if valid).
    """
    errors: list[str] = []
    sanitized = _sanitize_value(password)

    if sanitized is None or sanitized == "":
        errors.append("Password is required.")
        return errors

    if len(sanitized) < 8:
        errors.append("Password must be at least 8 characters long.")

    if not any(c.isupper() for c in sanitized):
        errors.append("Password must contain at least one uppercase letter.")

    if not any(c.islower() for c in sanitized):
        errors.append("Password must contain at least one lowercase letter.")

    if not any(c.isdigit() for c in sanitized):
        errors.append("Password must contain at least one digit.")

    special_characters = set(string.punctuation)
    if not any(c in special_characters for c in sanitized):
        errors.append("Password must contain at least one special character.")

    return errors


def validate_registration(
    data: dict[str, Any] | None,
) -> ValidationResult:
    """Validate a full registration payload containing username, email, and password.

    Accepts a dictionary with keys 'username', 'email', and 'password'.
    Handles None, non-dict, and missing-key inputs safely without crashing.
    Password values are never exposed in the result.

    Returns a ValidationResult with per-field error lists.
    """
    result = ValidationResult()

    if data is None or not isinstance(data, dict):
        result.add_error("form", "Invalid or missing registration data.")
        return result

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    username_errors = validate_username(username)
    for err in username_errors:
        result.add_error("username", err)

    email_errors = validate_email(email)
    for err in email_errors:
        result.add_error("email", err)

    password_errors = validate_password(password)
    for err in password_errors:
        result.add_error("password", err)

    return result


def validate_registration(username, email, password) -> dict:
    errors = []
    errors.extend(validate_username(username))
    errors.extend(validate_email(email))
    errors.extend(validate_password(password))
    return {"valid": len(errors) == 0, "errors": errors}


if __name__ == "__main__":
    # Demonstrate usage with a valid registration
    valid_data = {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "Str0ng!Pass",
    }
    result = validate_registration(valid_data)
    print(f"Valid data: {result}")

    # Demonstrate usage with invalid registration
    invalid_data = {
        "username": "ab",
        "email": "not-an-email",
        "password": "weak",
    }
    result = validate_registration(invalid_data)
    print(f"Invalid data: {result}")

    # Demonstrate handling of missing/empty input
    result = validate_registration(None)
    print(f"None input: {result}")

    result = validate_registration({})
    print(f"Empty dict: {result}")
