import re

def validate_registration(username, email, password) -> dict:
    errors = []
    
    # Validate username (3 to 20 characters)
    if not isinstance(username, str) or len(username) < 3 or len(username) > 20:
        errors.append("username")
    
    # Validate email
    if not isinstance(email, str) or not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        errors.append("email")
    
    # Validate password (at least 8 chars with uppercase, lowercase, number, special char)
    if not isinstance(password, str) or not (
        len(password) >= 8 and
        re.search(r'[A-Z]', password) and
        re.search(r'[a-z]', password) and
        re.search(r'[0-9]', password) and
        re.search(r'[^a-zA-Z0-9]', password)
    ):
        errors.append("password")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
