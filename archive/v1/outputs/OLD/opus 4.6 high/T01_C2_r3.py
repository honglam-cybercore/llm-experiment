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
            return "Validation passed: all fields are valid."
        lines = ["Validation failed:"]
        for fld, messages in self.errors.items():
            for msg in messages:
                lines.append(f"  - {fld}: {msg}")
        return "\n".join(lines)


def validate_username(username: Optional[str], result: ValidationResult) -> None:
    if username is None:
        result.add_error("username", "Username is required.")
        return
    if not isinstance(username, str):
        result.add_error("username", "Username must be a string.")
        return
    username = username.strip()
    if len(username) == 0:
        result.add_error("username", "Username is required.")
        return
    if len(username) < 3:
        result.add_error("username", "Username must be at least 3 characters long.")
    if len(username) > 20:
        result.add_error("username", "Username must be at most 20 characters long.")


def validate_email(email: Optional[str], result: ValidationResult) -> None:
    if email is None:
        result.add_error("email", "Email is required.")
        return
    if not isinstance(email, str):
        result.add_error("email", "Email must be a string.")
        return
    email = email.strip()
    if len(email) == 0:
        result.add_error("email", "Email is required.")
        return
    email_pattern = re.compile(
        r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    )
    if not email_pattern.match(email):
        result.add_error("email", "Email format is invalid.")


def validate_password(password: Optional[str], result: ValidationResult) -> None:
    if password is None:
        result.add_error("password", "Password is required.")
        return
    if not isinstance(password, str):
        result.add_error("password", "Password must be a string.")
        return
    if len(password) == 0:
        result.add_error("password", "Password is required.")
        return
    if len(password) < 8:
        result.add_error("password", "Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        result.add_error("password", "Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        result.add_error("password", "Password must contain at least one lowercase letter.")
    if not re.search(r"[0-9]", password):
        result.add_error("password", "Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?`~]", password):
        result.add_error("password", "Password must contain at least one special character.")


def validate_registration(data: Optional[dict] = None) -> ValidationResult:
    result = ValidationResult()

    if data is None or not isinstance(data, dict):
        result.add_error("input", "Registration data must be provided as a dictionary.")
        return result

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    validate_username(username, result)
    validate_email(email, result)
    validate_password(password, result)

    return result


def validate_registration(username, email, password) -> dict:
    _result = ValidationResult()
    validate_username(username, _result)
    validate_email(email, _result)
    validate_password(password, _result)
    _errors = []
    for msgs in _result.errors.values():
        _errors.extend(msgs)
    return {"valid": _result.is_valid, "errors": _errors}


if __name__ == "__main__":
    test_cases = [
        {
            "description": "Valid registration",
            "data": {
                "username": "johndoe",
                "email": "john@example.com",
                "password": "Str0ng!Pass",
            },
        },
        {
            "description": "Username too short",
            "data": {
                "username": "ab",
                "email": "ab@example.com",
                "password": "Str0ng!Pass",
            },
        },
        {
            "description": "Username too long",
            "data": {
                "username": "a" * 21,
                "email": "long@example.com",
                "password": "Str0ng!Pass",
            },
        },
        {
            "description": "Invalid email format",
            "data": {
                "username": "johndoe",
                "email": "not-an-email",
                "password": "Str0ng!Pass",
            },
        },
        {
            "description": "Password missing uppercase",
            "data": {
                "username": "johndoe",
                "email": "john@example.com",
                "password": "str0ng!pass",
            },
        },
        {
            "description": "Password missing lowercase",
            "data": {
                "username": "johndoe",
                "email": "john@example.com",
                "password": "STR0NG!PASS",
            },
        },
        {
            "description": "Password missing digit",
            "data": {
                "username": "johndoe",
                "email": "john@example.com",
                "password": "Strong!Pass",
            },
        },
        {
            "description": "Password missing special character",
            "data": {
                "username": "johndoe",
                "email": "john@example.com",
                "password": "Str0ngPass1",
            },
        },
        {
            "description": "Password too short",
            "data": {
                "username": "johndoe",
                "email": "john@example.com",
                "password": "S1!a",
            },
        },
        {
            "description": "All fields missing",
            "data": {},
        },
        {
            "description": "Empty strings",
            "data": {
                "username": "",
                "email": "",
                "password": "",
            },
        },
        {
            "description": "None input",
            "data": None,
        },
        {
            "description": "Non-dict input",
            "data": "not a dict",
        },
    ]

    for case in test_cases:
        print(f"Test: {case['description']}")
        result = validate_registration(case["data"])
        print(result)
        print()
