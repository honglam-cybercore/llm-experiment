import re

def validate_registration(username, email, password) -> dict:
    errors = []
    
    # Validate username: 3 to 20 characters
    if not isinstance(username, str) or not (3 <= len(username) <= 20):
        errors.append("username")
    
    # Validate email format
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not isinstance(email, str) or not re.match(email_pattern, email):
        errors.append("email")
    
    # Validate password: at least 8 chars, uppercase, lowercase, number, special char
    if not isinstance(password, str):
        errors.append("password")
    else:
        has_uppercase = re.search(r'[A-Z]', password)
        has_lowercase = re.search(r'[a-z]', password)
        has_number = re.search(r'\d', password)
        has_special = re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password)
        
        if not (len(password) >= 8 and has_uppercase and has_lowercase and has_number and has_special):
            errors.append("password")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
