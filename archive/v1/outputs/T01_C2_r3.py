import re

def validate_registration(username, email, password) -> dict:
    errors = []
    
    if not is_valid_username(username):
        errors.append("username")
    
    if not is_valid_email(email):
        errors.append("email")
    
    if not is_valid_password(password):
        errors.append("password")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

def is_valid_username(username):
    if not isinstance(username, str):
        return False
    return 3 <= len(username) <= 20

def is_valid_email(email):
    if not isinstance(email, str):
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def is_valid_password(password):
    if not isinstance(password, str):
        return False
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
        return False
    return True
