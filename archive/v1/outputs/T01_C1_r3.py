import re

def validate_registration(username, email, password) -> dict:
    errors = []
    
    # Validate username (3 to 20 characters)
    if not username or len(username) < 3 or len(username) > 20:
        errors.append("username")
    
    # Validate email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not email or not re.match(email_pattern, email):
        errors.append("email")
    
    # Validate password (at least 8 chars, uppercase, lowercase, number, special char)
    if not password or len(password) < 8:
        errors.append("password")
    elif not (re.search(r'[A-Z]', password) and re.search(r'[a-z]', password) and 
              re.search(r'[0-9]', password) and re.search(r'[^a-zA-Z0-9]', password)):
        errors.append("password")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
