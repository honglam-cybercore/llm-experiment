import re


def validate_username(username: str) -> tuple[bool, str]:
    if not isinstance(username, str):
        return False, "Username must be a string."
    if len(username) < 3:
        return False, "Username must be at least 3 characters long."
    if len(username) > 20:
        return False, "Username must be at most 20 characters long."
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, digits, and underscores."
    return True, "Username is valid."


def validate_email(email: str) -> tuple[bool, str]:
    if not isinstance(email, str):
        return False, "Email must be a string."
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Email address is not valid."
    return True, "Email is valid."


def validate_password(password: str) -> tuple[bool, str]:
    if not isinstance(password, str):
        return False, "Password must be a string."
    errors = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter.")
    if not re.search(r'[0-9]', password):
        errors.append("Password must contain at least one digit.")
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>/?`~]', password):
        errors.append("Password must contain at least one special character.")
    if errors:
        return False, " ".join(errors)
    return True, "Password is valid."


def validate_user_input(username: str, email: str, password: str) -> dict[str, tuple[bool, str]]:
    return {
        "username": validate_username(username),
        "email": validate_email(email),
        "password": validate_password(password),
    }


def validate_registration(username, email, password) -> dict:
    errors = []
    u_ok, u_msg = validate_username(username)
    if not u_ok:
        errors.append(u_msg)
    e_ok, e_msg = validate_email(email)
    if not e_ok:
        errors.append(e_msg)
    p_ok, p_msg = validate_password(password)
    if not p_ok:
        errors.append(p_msg)
    return {"valid": len(errors) == 0, "errors": errors}


if __name__ == "__main__":
    test_cases = [
        ("usr", "user@example.com", "Passw0rd!"),
        ("ab", "user@example.com", "Passw0rd!"),
        ("valid_user", "invalid-email", "Passw0rd!"),
        ("valid_user", "user@example.com", "short"),
        ("valid_user", "user@example.com", "nouppercase1!"),
        ("valid_user", "user@example.com", "NOLOWERCASE1!"),
        ("valid_user", "user@example.com", "NoDigits!!aa"),
        ("valid_user", "user@example.com", "NoSpecial1aa"),
        ("a_very_long_username_that_exceeds", "user@example.com", "Passw0rd!"),
        ("good_user", "name@domain.co.uk", "G00dP@ss!"),
    ]

    for username, email, password in test_cases:
        results = validate_user_input(username, email, password)
        print(f"Username: {username!r}, Email: {email!r}, Password: {password!r}")
        for field, (is_valid, message) in results.items():
            status = "PASS" if is_valid else "FAIL"
            print(f"  {field}: [{status}] {message}")
        print()
