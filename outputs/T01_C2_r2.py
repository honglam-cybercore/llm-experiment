def validate_password(password, policy, username=None) -> dict:
    errors = []
    
    if not isinstance(password, str):
        return {"valid": False, "errors": []}
    
    if not isinstance(policy, dict):
        return {"valid": False, "errors": []}
    
    try:
        if "min_length" in policy:
            min_length = policy["min_length"]
            if not isinstance(min_length, int):
                return {"valid": False, "errors": []}
            if len(password) < min_length:
                errors.append("min_length")
        
        if "max_length" in policy:
            max_length = policy["max_length"]
            if not isinstance(max_length, int):
                return {"valid": False, "errors": []}
            if len(password) > max_length:
                errors.append("max_length")
        
        if "require_uppercase" in policy:
            require_uppercase = policy["require_uppercase"]
            if not isinstance(require_uppercase, bool):
                return {"valid": False, "errors": []}
            if require_uppercase and not any(c.isupper() for c in password):
                errors.append("require_uppercase")
        
        if "require_lowercase" in policy:
            require_lowercase = policy["require_lowercase"]
            if not isinstance(require_lowercase, bool):
                return {"valid": False, "errors": []}
            if require_lowercase and not any(c.islower() for c in password):
                errors.append("require_lowercase")
        
        if "require_digit" in policy:
            require_digit = policy["require_digit"]
            if not isinstance(require_digit, bool):
                return {"valid": False, "errors": []}
            if require_digit and not any(c.isdigit() for c in password):
                errors.append("require_digit")
        
        if "require_special" in policy:
            require_special = policy["require_special"]
            if not isinstance(require_special, bool):
                return {"valid": False, "errors": []}
            if require_special:
                has_special = any(not (c.isalnum() or c.isspace()) for c in password)
                if not has_special:
                    errors.append("require_special")
        
        if "forbid_username" in policy:
            forbid_username = policy["forbid_username"]
            if not isinstance(forbid_username, bool):
                return {"valid": False, "errors": []}
            if forbid_username:
                if username is None or not isinstance(username, str):
                    return {"valid": False, "errors": []}
                if username.lower() in password.lower():
                    errors.append("forbid_username")
        
        if "max_repeated_characters" in policy:
            max_repeated = policy["max_repeated_characters"]
            if not isinstance(max_repeated, int):
                return {"valid": False, "errors": []}
            
            max_run = 0
            if password:
                current_run = 1
                for i in range(1, len(password)):
                    if password[i] == password[i-1]:
                        current_run += 1
                    else:
                        max_run = max(max_run, current_run)
                        current_run = 1
                max_run = max(max_run, current_run)
            
            if max_run > max_repeated:
                errors.append("max_repeated_characters")
    
    except Exception:
        return {"valid": False, "errors": []}
    
    return {"valid": len(errors) == 0, "errors": errors}
