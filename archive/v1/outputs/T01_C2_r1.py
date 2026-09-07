import re

def validate_registration(username, email, password) -> dict:
    errors = []
    
    # Validate username: 3 to 20 characters
    if not isinstance(username, str) or not (3 <= len(username) <= 20):
        errors.append("username")
    
    # Validate email
    if not isinstance(email, str) or not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
        errors.append("email")
    
    # Validate password: 8+ chars, uppercase, lowercase, digit, special char
    if not isinstance(password, str):
        errors.append("password")
    else:
        has_uppercase = bool(re.search(r'[A-Z]', password))
        has_lowercase = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'[0-9]', password))
        has_special = bool(re.search(r'[^\w\s]', password))
        
        if not (len(password) >= 8 and has_uppercase and has_lowercase and has_digit and has_special):
            errors.append("password")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
