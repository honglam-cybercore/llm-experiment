def validate_password(password, policy, username=None) -> dict:
    errors = []
    
    try:
        if not isinstance(password, str):
            return {"valid": False, "errors": []}
        
        if not isinstance(policy, dict):
            return {"valid": False, "errors": []}
        
        if "min_length" in policy:
            min_len = policy["min_length"]
            if not isinstance(min_len, int) or min_len < 0:
                errors.append("min_length")
            elif len(password) < min_len:
                errors.append("min_length")
        
        if "max_length" in policy:
            max_len = policy["max_length"]
            if not isinstance(max_len, int) or max_len < 0:
                errors.append("max_length")
            elif len(password) > max_len:
                errors.append("max_length")
        
        if "require_uppercase" in policy:
            val = policy["require_uppercase"]
            if not isinstance(val, bool):
                errors.append("require_uppercase")
            elif val and not any(c.isupper() for c in password):
                errors.append("require_uppercase")
        
        if "require_lowercase" in policy:
            val = policy["require_lowercase"]
            if not isinstance(val, bool):
                errors.append("require_lowercase")
            elif val and not any(c.islower() for c in password):
                errors.append("require_lowercase")
        
        if "require_digit" in policy:
            val = policy["require_digit"]
            if not isinstance(val, bool):
                errors.append("require_digit")
            elif val and not any(c.isdigit() for c in password):
                errors.append("require_digit")
        
        if "require_special" in policy:
            val = policy["require_special"]
            if not isinstance(val, bool):
                errors.append("require_special")
            elif val and not any(not c.isalnum() for c in password):
                errors.append("require_special")
        
        if "forbid_username" in policy:
            val = policy["forbid_username"]
            if not isinstance(val, bool):
                errors.append("forbid_username")
            elif val and username is not None:
                if not isinstance(username, str):
                    errors.append("forbid_username")
                elif username.lower() in password.lower():
                    errors.append("forbid_username")
        
        if "max_repeated_characters" in policy:
            max_rep = policy["max_repeated_characters"]
            if not isinstance(max_rep, int) or max_rep < 0:
                errors.append("max_repeated_characters")
            else:
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
    
    except:
        return {"valid": False, "errors": []}
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
