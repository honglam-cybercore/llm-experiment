import re
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
    PASSWORD_MAX_LENGTH = 128

    EMAIL_MAX_LENGTH = 254

    _USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]+$")

    _EMAIL_PATTERN = re.compile(
        r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+"
        r"@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
        r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
    )

    _SPECIAL_CHARACTERS = set(string.punctuation)

    @classmethod
    def validate_username(cls, username: str) -> list[str]:
        """Validate a username and return a list of error messages (empty if valid)."""
        errors: list[str] = []

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

        if length > 0 and not cls._USERNAME_PATTERN.match(username):
            errors.append(
                "Username may only contain letters, digits, underscores, hyphens, and dots."
            )

        return errors

    @classmethod
    def validate_email(cls, email: str) -> list[str]:
        """Validate an email address and return a list of error messages (empty if valid)."""
        errors: list[str] = []

        if not isinstance(email, str):
            return ["Email must be a string."]

        if len(email) == 0:
            errors.append("Email must not be empty.")
            return errors

        if len(email) > cls.EMAIL_MAX_LENGTH:
            errors.append(
                f"Email must be at most {cls.EMAIL_MAX_LENGTH} characters long."
            )

        if not cls._EMAIL_PATTERN.match(email):
            errors.append("Email format is invalid.")

        parts = email.split("@")
        if len(parts) == 2:
            local_part, domain_part = parts
            if len(local_part) > 64:
                errors.append("Email local part must be at most 64 characters long.")
            if not domain_part or "." not in domain_part:
                if "Email format is invalid." not in errors:
                    errors.append("Email domain must contain at least one dot.")

        return errors

    @classmethod
    def validate_password(cls, password: str) -> list[str]:
        """Validate a password and return a list of error messages (empty if valid).

        Password requirements:
        - At least 8 characters long
        - Contains at least one uppercase letter
        - Contains at least one lowercase letter
        - Contains at least one digit
        - Contains at least one special character
        """
        errors: list[str] = []

        if not isinstance(password, str):
            return ["Password must be a string."]

        if len(password) < cls.PASSWORD_MIN_LENGTH:
            errors.append(
                f"Password must be at least {cls.PASSWORD_MIN_LENGTH} characters long."
            )

        if len(password) > cls.PASSWORD_MAX_LENGTH:
            errors.append(
                f"Password must be at most {cls.PASSWORD_MAX_LENGTH} characters long."
            )

        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter.")

        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter.")

        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit.")

        if not any(c in cls._SPECIAL_CHARACTERS for c in password):
            errors.append("Password must contain at least one special character.")

        return errors

    @classmethod
    def validate_all(
        cls, username: str, email: str, password: str
    ) -> dict[str, list[str]]:
        """Validate username, email, and password together.

        Returns a dictionary mapping field names to lists of error messages.
        Fields with no errors are omitted from the result.
        """
        result: dict[str, list[str]] = {}

        username_errors = cls.validate_username(username)
        if username_errors:
            result["username"] = username_errors

        email_errors = cls.validate_email(email)
        if email_errors:
            result["email"] = email_errors

        password_errors = cls.validate_password(password)
        if password_errors:
            result["password"] = password_errors

        return result

    @classmethod
    def validate_all_or_raise(
        cls, username: str, email: str, password: str
    ) -> None:
        """Validate username, email, and password; raise ValidationError on failure.

        Raises:
            ValidationError: If any validation check fails. The exception's
                ``errors`` attribute contains all individual error messages.
        """
        all_errors = cls.validate_all(username, email, password)
        if all_errors:
            flat_errors = [
                msg for field_errors in all_errors.values() for msg in field_errors
            ]
            raise ValidationError(flat_errors)


def validate_username(username: str) -> tuple[bool, list[str]]:
    """Convenience function to validate a username.

    Returns:
        A tuple of (is_valid, error_messages).
    """
    errors = InputValidator.validate_username(username)
    return (len(errors) == 0, errors)


def validate_email(email: str) -> tuple[bool, list[str]]:
    """Convenience function to validate an email address.

    Returns:
        A tuple of (is_valid, error_messages).
    """
    errors = InputValidator.validate_email(email)
    return (len(errors) == 0, errors)


def validate_password(password: str) -> tuple[bool, list[str]]:
    """Convenience function to validate a password.

    Returns:
        A tuple of (is_valid, error_messages).
    """
    errors = InputValidator.validate_password(password)
    return (len(errors) == 0, errors)


def validate_user_input(
    username: str, email: str, password: str
) -> tuple[bool, dict[str, list[str]]]:
    """Validate all user registration inputs at once.

    Returns:
        A tuple of (all_valid, errors_by_field). ``errors_by_field`` maps
        field names to their respective error lists; fields with no errors
        are omitted.
    """
    errors = InputValidator.validate_all(username, email, password)
    return (len(errors) == 0, errors)


def validate_registration(username, email, password) -> dict:
    result = InputValidator.validate_all(username, email, password)
    errors = []
    for msgs in result.values():
        errors.extend(msgs)
    return {"valid": len(errors) == 0, "errors": errors}


if __name__ == "__main__":
    test_cases = [
        ("validuser", "user@example.com", "Str0ng!Pass"),
        ("ab", "bad-email", "weak"),
        ("good_user", "test@domain.co", "NoSpecial1"),
        ("a" * 21, "toolong@" + "x" * 250 + ".com", "Short1!"),
        ("valid.user-name", "name@sub.domain.org", "C0mpl3x!Passw0rd"),
    ]

    for username, email, password in test_cases:
        is_valid, errors = validate_user_input(username, email, password)
        status = "PASS" if is_valid else "FAIL"
        print(f"[{status}] username={username!r}, email={email!r}")
        if errors:
            for field, messages in errors.items():
                for msg in messages:
                    print(f"  {field}: {msg}")
        print()
