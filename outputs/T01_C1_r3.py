import string

def validate_password(password, policy, username=None) -> dict:
    # Validate inputs
    if not isinstance(password, str):
        return {"valid": False, "errors": []}
    
    if not isinstance(policy, dict):
        return {"valid": False, "errors": []}
    
    # Validate policy structure
    valid_keys = {"min_length", "max_length", "require_uppercase", "require_lowercase", 
                  "require_digit", "require_special", "forbid_username", "max_repeated_characters"}
    
    bool_keys = {"require_uppercase", "require_lowercase", "require_digit", "require_special", "forbid_username"}
    int_keys = {"min_length", "max_length", "max_repeated_characters"}
    
    for key, value in policy.items():
        if key not in valid_keys:
            return {"valid": False, "errors": []}
        
        if key in bool_keys:
            if not isinstance(value, bool):
                return {"valid": False, "errors": []}
        elif key in int_keys:
            if type(value) is not int:
                return {"valid": False, "errors": []}
    
    # Check rules
    errors = []
    
    # min_length
    if "min_length" in policy:
        if len(password) < policy["min_length"]:
            errors.append("min_length")
    
    # max_length
    if "max_length" in policy:
        if len(password) > policy["max_length"]:
            errors.append("max_length")
    
    # require_uppercase
    if "require_uppercase" in policy and policy["require_uppercase"]:
        if not any(c.isupper() for c in password):
            errors.append("require_uppercase")
    
    # require_lowercase
    if "require_lowercase" in policy and policy["require_lowercase"]:
        if not any(c.islower() for c in password):
            errors.append("require_lowercase")
    
    # require_digit
    if "require_digit" in policy and policy["require_digit"]:
        if not any(c.isdigit() for c in password):
            errors.append("require_digit")
    
    # require_special
    if "require_special" in policy and policy["require_special"]:
        if not any(c in string.punctuation for c in password):
            errors.append("require_special")
    
    # forbid_username
    if "forbid_username" in policy and policy["forbid_username"]:
        if username is not None:
            if not isinstance(username, str):
                return {"valid": False, "errors": []}
            if username.lower() in password.lower():
                errors.append("forbid_username")
    
    # max_repeated_characters
    if "max_repeated_characters" in policy:
        max_rep = policy["max_repeated_characters"]
        if password:
            max_run = 1
            current_run = 1
            for i in range(1, len(password)):
                if password[i] == password[i-1]:
                    current_run += 1
                    max_run = max(max_run, current_run)
                else:
                    current_run = 1
            
            if max_run > max_rep:
                errors.append("max_repeated_characters")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
