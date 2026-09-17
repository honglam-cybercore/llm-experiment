def validate_password(password, policy, username=None) -> dict:
    errors = []
    
    if not isinstance(password, str):
        return {"valid": False, "errors": []}
    
    if not isinstance(policy, dict):
        return {"valid": False, "errors": []}
    
    try:
        if "min_length" in policy:
            min_len = policy["min_length"]
            if not isinstance(min_len, int):
                return {"valid": False, "errors": []}
            if len(password) < min_len:
                errors.append("min_length")
        
        if "max_length" in policy:
            max_len = policy["max_length"]
            if not isinstance(max_len, int):
                return {"valid": False, "errors": []}
            if len(password) > max_len:
                errors.append("max_length")
        
        if "require_uppercase" in policy:
            req = policy["require_uppercase"]
            if not isinstance(req, bool):
                return {"valid": False, "errors": []}
            if req and not any(c.isupper() for c in password):
                errors.append("require_uppercase")
        
        if "require_lowercase" in policy:
            req = policy["require_lowercase"]
            if not isinstance(req, bool):
                return {"valid": False, "errors": []}
            if req and not any(c.islower() for c in password):
                errors.append("require_lowercase")
        
        if "require_digit" in policy:
            req = policy["require_digit"]
            if not isinstance(req, bool):
                return {"valid": False, "errors": []}
            if req and not any(c.isdigit() for c in password):
                errors.append("require_digit")
        
        if "require_special" in policy:
            req = policy["require_special"]
            if not isinstance(req, bool):
                return {"valid": False, "errors": []}
            if req:
                special_chars = set("!@#$%^&*()_+-=[]{}|;:,.<>?/~`")
                if not any(c in special_chars for c in password):
                    errors.append("require_special")
        
        if "forbid_username" in policy:
            req = policy["forbid_username"]
            if not isinstance(req, bool):
                return {"valid": False, "errors": []}
            if req:
                if username is not None and not isinstance(username, str):
                    return {"valid": False, "errors": []}
                if isinstance(username, str) and password.lower().find(username.lower()) != -1:
                    errors.append("forbid_username")
        
        if "max_repeated_characters" in policy:
            max_repeated = policy["max_repeated_characters"]
            if not isinstance(max_repeated, int):
                return {"valid": False, "errors": []}
            
            max_run = 0
            if len(password) > 0:
                max_run = 1
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
    
    except:
        return {"valid": False, "errors": []}
    
    return {"valid": len(errors) == 0, "errors": errors}
