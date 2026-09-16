import re


def validate_registration(username, email, password) -> dict:
    errors = []

    if not isinstance(username, str) or not 3 <= len(username) <= 20:
        errors.append("username")

    email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    if not isinstance(email, str) or not re.fullmatch(email_pattern, email):
        errors.append("email")

    if (
        not isinstance(password, str)
        or len(password) < 8
        or not re.search(r"[A-Z]", password)
        or not re.search(r"[a-z]", password)
        or not re.search(r"\d", password)
        or not re.search(r"[^A-Za-z0-9]", password)
    ):
        errors.append("password")

    return {"valid": not errors, "errors": errors}