import re

def validate_registration(username, email, password) -> dict:
    errors = []
    
    # Validate username: 3 to 20 characters
    if not isinstance(username, str) or not (3 <= len(username) <= 20):
        errors.append("username")
    
    # Validate email: basic email format validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not isinstance(email, str) or not re.match(email_pattern, email):
        errors.append("email")
    
    # Validate password: at least 8 characters with uppercase, lowercase, digit, and special character
    if not isinstance(password, str) or len(password) < 8:
        errors.append("password")
    else:
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        if not (has_upper and has_lower and has_digit and has_special):
            errors.append("password")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
