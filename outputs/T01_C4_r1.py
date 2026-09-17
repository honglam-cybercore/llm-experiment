def validate_password(password, policy, username=None) -> dict:
    errors = []
    
    # Validate input types
    if not isinstance(password, str):
        return {"valid": False, "errors": []}
    
    if not isinstance(policy, dict):
        return {"valid": False, "errors": []}
    
    if username is not None and not isinstance(username, str):
        return {"valid": False, "errors": []}
    
    # Check min_length
    if "min_length" in policy:
        min_len = policy["min_length"]
        if not isinstance(min_len, int) or min_len < 0:
            return {"valid": False, "errors": []}
        if len(password) < min_len:
            errors.append("min_length")
    
    # Check max_length
    if "max_length" in policy:
        max_len = policy["max_length"]
        if not isinstance(max_len, int) or max_len < 0:
            return {"valid": False, "errors": []}
        if len(password) > max_len:
            errors.append("max_length")
    
    # Check require_uppercase
    if "require_uppercase" in policy:
        if not isinstance(policy["require_uppercase"], bool):
            return {"valid": False, "errors": []}
        if policy["require_uppercase"] and not any(c.isupper() for c in password):
            errors.append("require_uppercase")
    
    # Check require_lowercase
    if "require_lowercase" in policy:
        if not isinstance(policy["require_lowercase"], bool):
            return {"valid": False, "errors": []}
        if policy["require_lowercase"] and not any(c.islower() for c in password):
            errors.append("require_lowercase")
    
    # Check require_digit
    if "require_digit" in policy:
        if not isinstance(policy["require_digit"], bool):
            return {"valid": False, "errors": []}
        if policy["require_digit"] and not any(c.isdigit() for c in password):
            errors.append("require_digit")
    
    # Check require_special
    if "require_special" in policy:
        if not isinstance(policy["require_special"], bool):
            return {"valid": False, "errors": []}
        if policy["require_special"] and not any(not c.isalnum() for c in password):
            errors.append("require_special")
    
    # Check forbid_username
    if "forbid_username" in policy:
        if not isinstance(policy["forbid_username"], bool):
            return {"valid": False, "errors": []}
        if policy["forbid_username"]:
            if username is None:
                return {"valid": False, "errors": []}
            if username.lower() in password.lower():
                errors.append("forbid_username")
    
    # Check max_repeated_characters
    if "max_repeated_characters" in policy:
        max_rep = policy["max_repeated_characters"]
        if not isinstance(max_rep, int) or max_rep < 0:
            return {"valid": False, "errors": []}
        
        max_run = 0
        if len(password) > 0:
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
    
    return {"valid": len(errors) == 0, "errors": errors}
