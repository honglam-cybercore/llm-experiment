def validate_password(password, policy, username=None) -> dict:
    errors = []
    
    if not isinstance(password, str):
        return {"valid": False, "errors": []}
    
    if not isinstance(policy, dict):
        return {"valid": False, "errors": []}
    
    if "min_length" in policy:
        if not isinstance(policy["min_length"], int) or isinstance(policy["min_length"], bool):
            return {"valid": False, "errors": []}
        if len(password) < policy["min_length"]:
            errors.append("min_length")
    
    if "max_length" in policy:
        if not isinstance(policy["max_length"], int) or isinstance(policy["max_length"], bool):
            return {"valid": False, "errors": []}
        if len(password) > policy["max_length"]:
            errors.append("max_length")
    
    if "require_uppercase" in policy:
        if not isinstance(policy["require_uppercase"], bool):
            return {"valid": False, "errors": []}
        if policy["require_uppercase"] and not any(c.isupper() for c in password):
            errors.append("require_uppercase")
    
    if "require_lowercase" in policy:
        if not isinstance(policy["require_lowercase"], bool):
            return {"valid": False, "errors": []}
        if policy["require_lowercase"] and not any(c.islower() for c in password):
            errors.append("require_lowercase")
    
    if "require_digit" in policy:
        if not isinstance(policy["require_digit"], bool):
            return {"valid": False, "errors": []}
        if policy["require_digit"] and not any(c.isdigit() for c in password):
            errors.append("require_digit")
    
    if "require_special" in policy:
        if not isinstance(policy["require_special"], bool):
            return {"valid": False, "errors": []}
        if policy["require_special"]:
            if not any(not c.isalnum() for c in password):
                errors.append("require_special")
    
    if "forbid_username" in policy:
        if not isinstance(policy["forbid_username"], bool):
            return {"valid": False, "errors": []}
        if policy["forbid_username"]:
            if username is None or not isinstance(username, str) or len(username) == 0:
                return {"valid": False, "errors": []}
            if username.lower() in password.lower():
                errors.append("forbid_username")
    
    if "max_repeated_characters" in policy:
        if not isinstance(policy["max_repeated_characters"], int) or isinstance(policy["max_repeated_characters"], bool):
            return {"valid": False, "errors": []}
        
        max_allowed = policy["max_repeated_characters"]
        if max_allowed < 1:
            return {"valid": False, "errors": []}
        
        max_run = 0
        if len(password) > 0:
            current_run = 1
            for i in range(1, len(password)):
                if password[i] == password[i-1]:
                    current_run += 1
                else:
                    max_run = max(max_run, current_run)
                    current_run = 1
            max_run = max(max_run, current_run)
        
        if max_run > max_allowed:
            errors.append("max_repeated_characters")
    
    return {"valid": len(errors) == 0, "errors": errors}
