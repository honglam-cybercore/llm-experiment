import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ValidationResult:
    is_valid: bool = True
    errors: list[str] = field(default_factory=list)

    def add_error(self, error: str) -> None:
        self.is_valid = False
        self.errors.append(error)


def validate_username(username: Optional[str]) -> ValidationResult:
    result = ValidationResult()

    if username is None:
        result.add_error("Username is required.")
        return result

    if not isinstance(username, str):
        result.add_error("Username must be a string.")
        return result

    stripped = username.strip()

    if len(stripped) == 0:
        result.add_error("Username is required.")
        return result

    if len(stripped) < 3:
        result.add_error("Username must be at least 3 characters.")

    if len(stripped) > 20:
        result.add_error("Username must be at most 20 characters.")

    return result


def validate_email(email: Optional[str]) -> ValidationResult:
    result = ValidationResult()

    if email is None:
        result.add_error("Email is required.")
        return result

    if not isinstance(email, str):
        result.add_error("Email must be a string.")
        return result

    stripped = email.strip()

    if len(stripped) == 0:
        result.add_error("Email is required.")
        return result

    email_pattern = re.compile(
        r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    )

    if not email_pattern.match(stripped):
        result.add_error("Email format is invalid.")

    return result


def validate_password(password: Optional[str]) -> ValidationResult:
    result = ValidationResult()

    if password is None:
        result.add_error("Password is required.")
        return result

    if not isinstance(password, str):
        result.add_error("Password must be a string.")
        return result

    if len(password) == 0:
        result.add_error("Password is required.")
        return result

    if len(password) < 8:
        result.add_error("Password must be at least 8 characters.")

    if not re.search(r"[A-Z]", password):
        result.add_error("Password must contain at least one uppercase letter.")

    if not re.search(r"[a-z]", password):
        result.add_error("Password must contain at least one lowercase letter.")

    if not re.search(r"[0-9]", password):
        result.add_error("Password must contain at least one number.")

    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?`~]", password):
        result.add_error("Password must contain at least one special character.")

    return result


def validate_registration(
    username: Optional[str] = None,
    email: Optional[str] = None,
    password: Optional[str] = None,
) -> ValidationResult:
    overall = ValidationResult()

    username_result = validate_username(username)
    email_result = validate_email(email)
    password_result = validate_password(password)

    if not username_result.is_valid:
        overall.is_valid = False
        overall.errors.extend(username_result.errors)

    if not email_result.is_valid:
        overall.is_valid = False
        overall.errors.extend(email_result.errors)

    if not password_result.is_valid:
        overall.is_valid = False
        overall.errors.extend(password_result.errors)

    return overall


def safe_validate_registration(
    username=None, email=None, password=None
) -> ValidationResult:
    try:
        return validate_registration(username, email, password)
    except Exception:
        result = ValidationResult()
        result.add_error("An unexpected error occurred during validation.")
        return result


def validate_registration(username, email, password) -> dict:
    errors = []
    errors.extend(validate_username(username).errors)
    errors.extend(validate_email(email).errors)
    errors.extend(validate_password(password).errors)
    return {"valid": len(errors) == 0, "errors": errors}


if __name__ == "__main__":
    print("=== Valid Registration ===")
    result = safe_validate_registration("john_doe", "john@example.com", "Passw0rd!")
    print(f"Valid: {result.is_valid}")
    print(f"Errors: {result.errors}")
    print()

    print("=== Invalid Username (too short) ===")
    result = safe_validate_registration("ab", "john@example.com", "Passw0rd!")
    print(f"Valid: {result.is_valid}")
    print(f"Errors: {result.errors}")
    print()

    print("=== Invalid Email ===")
    result = safe_validate_registration("john_doe", "not-an-email", "Passw0rd!")
    print(f"Valid: {result.is_valid}")
    print(f"Errors: {result.errors}")
    print()

    print("=== Weak Password ===")
    result = safe_validate_registration("john_doe", "john@example.com", "weak")
    print(f"Valid: {result.is_valid}")
    print(f"Errors: {result.errors}")
    print()

    print("=== Missing All Fields ===")
    result = safe_validate_registration()
    print(f"Valid: {result.is_valid}")
    print(f"Errors: {result.errors}")
    print()

    print("=== Empty Strings ===")
    result = safe_validate_registration("", "", "")
    print(f"Valid: {result.is_valid}")
    print(f"Errors: {result.errors}")
    print()

    print("=== Non-string Inputs ===")
    result = safe_validate_registration(123, None, True)
    print(f"Valid: {result.is_valid}")
    print(f"Errors: {result.errors}")
