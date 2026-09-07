import re

def validate_registration(username, email, password) -> dict:
    errors = []
    
    # Validate username
    if isinstance(username, str):
        if not (3 <= len(username) <= 20):
            errors.append("username")
    else:
        errors.append("username")
    
    # Validate email
    if isinstance(email, str):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            errors.append("email")
    else:
        errors.append("email")
    
    # Validate password
    password_valid = False
    if isinstance(password, str):
        checks = [
            len(password) >= 8,
            bool(re.search(r'[A-Z]', password)),
            bool(re.search(r'[a-z]', password)),
            bool(re.search(r'\d', password)),
            bool(re.search(r'[^a-zA-Z0-9]', password))
        ]
        password_valid = all(checks)
    
    if not password_valid:
        errors.append("password")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
