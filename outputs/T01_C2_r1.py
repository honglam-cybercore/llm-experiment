def validate_password(password, policy, username=None) -> dict:
    if not isinstance(password, str):
        return {"valid": False, "errors": []}
    
    if not isinstance(policy, dict):
        return {"valid": False, "errors": []}
    
    if username is not None and not isinstance(username, str):
        return {"valid": False, "errors": []}
    
    int_keys = {"min_length", "max_length", "max_repeated_characters"}
    bool_keys = {"require_uppercase", "require_lowercase", "require_digit", "require_special", "forbid_username"}
    
    for key in int_keys:
        if key in policy and not isinstance(policy[key], int):
            return {"valid": False, "errors": []}
    
    for key in bool_keys:
        if key in policy and not isinstance(policy[key], bool):
            return {"valid": False, "errors": []}
    
    errors = []
    
    if "min_length" in policy:
        if len(password) < policy["min_length"]:
            errors.append("min_length")
    
    if "max_length" in policy:
        if len(password) > policy["max_length"]:
            errors.append("max_length")
    
    if "require_uppercase" in policy:
        if policy["require_uppercase"] and not any(c.isupper() for c in password):
            errors.append("require_uppercase")
    
    if "require_lowercase" in policy:
        if policy["require_lowercase"] and not any(c.islower() for c in password):
            errors.append("require_lowercase")
    
    if "require_digit" in policy:
        if policy["require_digit"] and not any(c.isdigit() for c in password):
            errors.append("require_digit")
    
    if "require_special" in policy:
        if policy["require_special"] and not any(not c.isalnum() for c in password):
            errors.append("require_special")
    
    if "forbid_username" in policy:
        if policy["forbid_username"] and username is not None:
            if username.lower() in password.lower():
                errors.append("forbid_username")
    
    if "max_repeated_characters" in policy:
        max_repeated = policy["max_repeated_characters"]
        if len(password) > 0:
            max_run = 1
            current_run = 1
            for i in range(1, len(password)):
                if password[i] == password[i-1]:
                    current_run += 1
                    max_run = max(max_run, current_run)
                else:
                    current_run = 1
            if max_run > max_repeated:
                errors.append("max_repeated_characters")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
