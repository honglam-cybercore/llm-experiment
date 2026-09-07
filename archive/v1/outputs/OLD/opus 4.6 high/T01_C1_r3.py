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
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number."
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>/?`~]', password):
        return False, "Password must contain at least one special character."
    return True, "Password is valid."


def validate_user(username: str, email: str, password: str) -> dict[str, tuple[bool, str]]:
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
        ("ab", "bad-email", "short"),
        ("valid_user", "alice@domain.org", "Str0ng!Pass"),
        ("this_username_is_way_too_long_for_validation", "x@y.z", "noSpecial1A"),
        ("ok_user", "test@test.com", "alllowercase1!"),
    ]

    for username, email, password in test_cases:
        print(f"Input: username={username!r}, email={email!r}, password={password!r}")
        results = validate_user(username, email, password)
        for field, (is_valid, message) in results.items():
            status = "PASS" if is_valid else "FAIL"
            print(f"  {field}: [{status}] {message}")
        print()
