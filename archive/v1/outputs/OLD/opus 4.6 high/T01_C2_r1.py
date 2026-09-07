import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ValidationResult:
    is_valid: bool = True
    errors: dict = field(default_factory=dict)

    def add_error(self, field_name: str, message: str):
        self.is_valid = False
        if field_name not in self.errors:
            self.errors[field_name] = []
        self.errors[field_name].append(message)

    def __str__(self):
        if self.is_valid:
            return "Validation passed."
        lines = ["Validation failed:"]
        for f, messages in self.errors.items():
            for msg in messages:
                lines.append(f"  {f}: {msg}")
        return "\n".join(lines)


def validate_username(username: Optional[str]) -> list[str]:
    errors = []
    if username is None:
        errors.append("Username is required.")
        return errors
    if not isinstance(username, str):
        errors.append("Username must be a string.")
        return errors
    if len(username) == 0:
        errors.append("Username is required.")
        return errors
    if len(username) < 3:
        errors.append("Username must be at least 3 characters.")
    if len(username) > 20:
        errors.append("Username must be at most 20 characters.")
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        errors.append("Username must contain only alphanumeric characters and underscores.")
    return errors


def validate_email(email: Optional[str]) -> list[str]:
    errors = []
    if email is None:
        errors.append("Email is required.")
        return errors
    if not isinstance(email, str):
        errors.append("Email must be a string.")
        return errors
    if len(email) == 0:
        errors.append("Email is required.")
        return errors
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        errors.append("Email format is invalid.")
    return errors


def validate_password(password: Optional[str]) -> list[str]:
    errors = []
    if password is None:
        errors.append("Password is required.")
        return errors
    if not isinstance(password, str):
        errors.append("Password must be a string.")
        return errors
    if len(password) == 0:
        errors.append("Password is required.")
        return errors
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter.")
    if not re.search(r'[0-9]', password):
        errors.append("Password must contain at least one number.")
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:\'",.<>?/\\`~]', password):
        errors.append("Password must contain at least one special character.")
    return errors


def validate_registration(data: Optional[dict] = None) -> ValidationResult:
    result = ValidationResult()

    if data is None or not isinstance(data, dict):
        result.add_error("input", "Registration data is required and must be a dictionary.")
        return result

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    for error in validate_username(username):
        result.add_error("username", error)

    for error in validate_email(email):
        result.add_error("email", error)

    for error in validate_password(password):
        result.add_error("password", error)

    return result


def validate_registration(username, email, password) -> dict:
    errors = []
    errors.extend(validate_username(username))
    errors.extend(validate_email(email))
    errors.extend(validate_password(password))
    return {"valid": len(errors) == 0, "errors": errors}


if __name__ == "__main__":
    test_cases = [
        {
            "username": "john_doe",
            "email": "john@example.com",
            "password": "Str0ng!Pass"
        },
        {
            "username": "ab",
            "email": "invalid-email",
            "password": "weak"
        },
        {
            "username": "",
            "email": "",
            "password": ""
        },
        {
            "username": "a" * 21,
            "email": "test@test.com",
            "password": "NoSpecial1"
        },
        {},
        None,
        {
            "username": "valid_user",
            "email": "user@domain.org",
            "password": "abcdefgh"
        },
        {
            "username": "user!name",
            "email": "user@domain.com",
            "password": "Valid1Pass!"
        },
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"--- Test Case {i} ---")
        result = validate_registration(case)
        print(result)
        print()
