import re

def validate_registration(username, email, password) -> dict:
    errors = []
    
    # Validate username
    if not isinstance(username, str) or len(username) < 3 or len(username) > 20:
        errors.append("username")
    
    # Validate email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not isinstance(email, str) or not re.match(email_pattern, email):
        errors.append("email")
    
    # Validate password
    password_valid = True
    if not isinstance(password, str) or len(password) < 8:
        password_valid = False
    else:
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        if not (has_upper and has_lower and has_digit and has_special):
            password_valid = False
    
    if not password_valid:
        errors.append("password")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
