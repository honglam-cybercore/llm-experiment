import re

def validate_registration(username, email, password) -> dict:
    errors = []
    
    # Validate username: 3-20 characters
    if not isinstance(username, str) or not (3 <= len(username) <= 20):
        errors.append("username")
    
    # Validate email: basic email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not isinstance(email, str) or not re.match(email_pattern, email):
        errors.append("email")
    
    # Validate password: at least 8 chars with uppercase, lowercase, number, special char
    password_valid = (
        isinstance(password, str)
        and len(password) >= 8
        and re.search(r'[A-Z]', password)
        and re.search(r'[a-z]', password)
        and re.search(r'[0-9]', password)
        and re.search(r'[^a-zA-Z0-9]', password)
    )
    if not password_valid:
        errors.append("password")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
