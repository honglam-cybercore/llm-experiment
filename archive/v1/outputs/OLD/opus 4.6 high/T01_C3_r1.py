import re
import string


class ValidationError(Exception):
    """Raised when input validation fails."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def validate_username(username: str) -> list[str]:
    """Validate a username string.

    Rules:
        - Must be a string.
        - Length must be between 3 and 20 characters (inclusive).
        - Must contain only alphanumeric characters, underscores, or hyphens.
    """
    errors: list[str] = []

    if not isinstance(username, str):
        return ["Username must be a string."]

    length = len(username)
    if length < 3:
        errors.append("Username must be at least 3 characters long.")
    elif length > 20:
        errors.append("Username must be at most 20 characters long.")

    if not re.fullmatch(r"[A-Za-z0-9_-]+", username):
        errors.append(
            "Username must contain only alphanumeric characters, "
            "underscores, or hyphens."
        )

    return errors


def validate_email(email: str) -> list[str]:
    """Validate an email address string.

    Uses a reasonable regex pattern that covers the vast majority of valid
    addresses without being overly permissive.
    """
    errors: list[str] = []

    if not isinstance(email, str):
        return ["Email must be a string."]

    # Guard against excessively long input before applying the regex.
    if len(email) > 254:
        errors.append("Email must not exceed 254 characters.")
        return errors

    # RFC-5321 local part max 64, domain max 253; basic structural check.
    pattern = (
        r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
        r"@"
        r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
        r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*"
        r"\.[A-Za-z]{2,}$"
    )

    if not re.fullmatch(pattern, email):
        errors.append("Email address is not valid.")

    local_part = email.split("@")[0] if "@" in email else email
    if len(local_part) > 64:
        errors.append("Email local part must not exceed 64 characters.")

    return errors


def validate_password(password: str) -> list[str]:
    """Validate a password string.

    Rules:
        - Must be a string.
        - At least 8 characters long.
        - Must contain at least one uppercase letter.
        - Must contain at least one lowercase letter.
        - Must contain at least one digit.
        - Must contain at least one special character.
    """
    errors: list[str] = []

    if not isinstance(password, str):
        return ["Password must be a string."]

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")

    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")

    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")

    if not re.search(r"[0-9]", password):
        errors.append("Password must contain at least one digit.")

    special_characters = set(string.punctuation)
    if not any(ch in special_characters for ch in password):
        errors.append(
            "Password must contain at least one special character "
            f"({string.punctuation})."
        )

    return errors


def validate_user_input(
    username: str,
    email: str,
    password: str,
    *,
    raise_on_error: bool = False,
) -> dict[str, list[str]]:
    """Validate username, email, and password together.

    Args:
        username: The username to validate.
        email: The email address to validate.
        password: The password to validate.
        raise_on_error: If True, raise a ``ValidationError`` when any
            validation errors are found.

    Returns:
        A dictionary mapping field names to lists of error messages.
        An empty list means the field is valid.

    Raises:
        ValidationError: If *raise_on_error* is True and validation fails.
    """
    result: dict[str, list[str]] = {
        "username": validate_username(username),
        "email": validate_email(email),
        "password": validate_password(password),
    }

    if raise_on_error:
        all_errors = [
            f"{field}: {msg}"
            for field, msgs in result.items()
            for msg in msgs
        ]
        if all_errors:
            raise ValidationError(all_errors)

    return result


def is_valid(username: str, email: str, password: str) -> bool:
    """Return True when all three inputs pass validation."""
    result = validate_user_input(username, email, password)
    return all(len(errs) == 0 for errs in result.values())


def validate_registration(username, email, password) -> dict:
    result = validate_user_input(username, email, password)
    errors = []
    for msgs in result.values():
        errors.extend(msgs)
    return {"valid": len(errors) == 0, "errors": errors}


if __name__ == "__main__":
    import sys

    demo_cases = [
        ("usr", "bad-email", "weak"),
        ("valid_user", "user@example.com", "Str0ng!Pass"),
        ("ab", "missing@domain", "12345678"),
        ("good-name", "hello@world.org", "NoSpecial1"),
        ("validUser123", "test@sub.domain.com", "G00d#Pass!"),
    ]

    for uname, mail, pwd in demo_cases:
        errors = validate_user_input(uname, mail, pwd)
        has_errors = any(errors[k] for k in errors)
        status = "INVALID" if has_errors else "VALID"
        print(f"[{status}] username={uname!r}, email={mail!r}, password=***")
        if has_errors:
            for field, msgs in errors.items():
                for msg in msgs:
                    print(f"  - {field}: {msg}")
        print()
