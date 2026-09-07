import re
import secrets
import string


class ValidationError(Exception):
    """Raised when input validation fails."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


class InputValidator:
    """Validates username, email, and password with secure defaults."""

    USERNAME_MIN_LENGTH = 3
    USERNAME_MAX_LENGTH = 20
    PASSWORD_MIN_LENGTH = 8
    USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")
    EMAIL_PATTERN = re.compile(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )
    SPECIAL_CHARACTERS = re.compile(r"[!@#$%^&*()_+\-=\[\]{}|;':\",./<>?\\`~]")

    @classmethod
    def validate_username(cls, username: str) -> list[str]:
        """Validate username: 3-20 characters, alphanumeric with . _ - allowed."""
        errors = []
        if not isinstance(username, str):
            return ["Username must be a string."]

        length = len(username)
        if length < cls.USERNAME_MIN_LENGTH:
            errors.append(
                f"Username must be at least {cls.USERNAME_MIN_LENGTH} characters long."
            )
        if length > cls.USERNAME_MAX_LENGTH:
            errors.append(
                f"Username must be at most {cls.USERNAME_MAX_LENGTH} characters long."
            )
        if length > 0 and not cls.USERNAME_PATTERN.match(username):
            errors.append(
                "Username may only contain letters, digits, dots, underscores, and hyphens."
            )
        return errors

    @classmethod
    def validate_email(cls, email: str) -> list[str]:
        """Validate email format using a standard regex pattern."""
        errors = []
        if not isinstance(email, str):
            return ["Email must be a string."]

        if not email:
            errors.append("Email must not be empty.")
        elif len(email) > 254:
            errors.append("Email must not exceed 254 characters.")
        elif not cls.EMAIL_PATTERN.match(email):
            errors.append("Email format is invalid.")

        local_part = email.split("@")[0] if "@" in email else email
        if len(local_part) > 64:
            errors.append("Email local part must not exceed 64 characters.")

        return errors

    @classmethod
    def validate_password(cls, password: str) -> list[str]:
        """Validate password: min 8 chars, must contain uppercase, lowercase, digit, special char."""
        errors = []
        if not isinstance(password, str):
            return ["Password must be a string."]

        if len(password) < cls.PASSWORD_MIN_LENGTH:
            errors.append(
                f"Password must be at least {cls.PASSWORD_MIN_LENGTH} characters long."
            )
        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter.")
        if not re.search(r"[0-9]", password):
            errors.append("Password must contain at least one digit.")
        if not cls.SPECIAL_CHARACTERS.search(password):
            errors.append("Password must contain at least one special character.")
        return errors

    @classmethod
    def validate_all(
        cls, username: str, email: str, password: str
    ) -> dict[str, list[str]]:
        """Validate all fields and return a dict of field-name to error lists."""
        results = {
            "username": cls.validate_username(username),
            "email": cls.validate_email(email),
            "password": cls.validate_password(password),
        }
        return results

    @classmethod
    def validate_all_or_raise(
        cls, username: str, email: str, password: str
    ) -> None:
        """Validate all fields; raise ValidationError if any fail."""
        results = cls.validate_all(username, email, password)
        all_errors = []
        for field, errors in results.items():
            for error in errors:
                all_errors.append(f"[{field}] {error}")
        if all_errors:
            raise ValidationError(all_errors)


def generate_secure_password(length: int = 16) -> str:
    """Generate a cryptographically secure random password meeting all requirements."""
    if length < 8:
        length = 8

    required = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*()_+-=[]{}|;:',.<>?"),
    ]

    remaining_length = length - len(required)
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:',.<>?"
    remaining = [secrets.choice(alphabet) for _ in range(remaining_length)]

    password_chars = required + remaining
    # Securely shuffle using Fisher-Yates with secrets
    for i in range(len(password_chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        password_chars[i], password_chars[j] = password_chars[j], password_chars[i]

    return "".join(password_chars)


def _sanitize_for_log(value: str, max_display: int = 3) -> str:
    """Redact sensitive values for safe logging. Never log full passwords or emails."""
    if not value:
        return "<empty>"
    if len(value) <= max_display:
        return "*" * len(value)
    return value[:max_display] + "*" * (len(value) - max_display)


def validate_registration(username, email, password) -> dict:
    result = InputValidator.validate_all(username, email, password)
    errors = []
    for msgs in result.values():
        errors.extend(msgs)
    return {"valid": len(errors) == 0, "errors": errors}


if __name__ == "__main__":
    test_cases = [
        ("usr", "user@example.com", "Str0ng!Pass"),
        ("ab", "invalid-email", "weak"),
        ("valid_user", "test@domain.org", "NoSpecial1"),
        ("valid_user", "test@domain.org", "Ab1!efgh"),
        ("a" * 21, "a@b.c" * 60, "short"),
    ]

    for username, email, password in test_cases:
        safe_user = _sanitize_for_log(username)
        safe_email = _sanitize_for_log(email)
        print(f"\nValidating user={safe_user}, email={safe_email}")
        results = InputValidator.validate_all(username, email, password)
        has_errors = False
        for field, errors in results.items():
            if errors:
                has_errors = True
                for error in errors:
                    print(f"  [{field}] {error}")
        if not has_errors:
            print("  All validations passed.")

    print(f"\nGenerated secure password: {generate_secure_password()}")
