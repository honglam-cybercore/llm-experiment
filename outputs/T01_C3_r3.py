def validate_password(password, policy, username=None) -> dict:
    errors = []
    
    try:
        if not isinstance(password, str):
            return {"valid": False, "errors": []}
        
        if not isinstance(policy, dict):
            return {"valid": False, "errors": []}
        
        for key, value in policy.items():
            if key in ["min_length", "max_length", "max_repeated_characters"]:
                if not isinstance(value, int) or value < 0:
                    return {"valid": False, "errors": []}
            elif key in ["require_uppercase", "require_lowercase", "require_digit", "require_special", "forbid_username"]:
                if not isinstance(value, bool):
                    return {"valid": False, "errors": []}
            else:
                return {"valid": False, "errors": []}
        
        if "min_length" in policy:
            if len(password) < policy["min_length"]:
                errors.append("min_length")
        
        if "max_length" in policy:
            if len(password) > policy["max_length"]:
                errors.append("max_length")
        
        if policy.get("require_uppercase", False):
            if not any(c.isupper() for c in password):
                errors.append("require_uppercase")
        
        if policy.get("require_lowercase", False):
            if not any(c.islower() for c in password):
                errors.append("require_lowercase")
        
        if policy.get("require_digit", False):
            if not any(c.isdigit() for c in password):
                errors.append("require_digit")
        
        if policy.get("require_special", False):
            if not any(not c.isalnum() for c in password):
                errors.append("require_special")
        
        if policy.get("forbid_username", False):
            if isinstance(username, str) and username.lower() in password.lower():
                errors.append("forbid_username")
        
        if "max_repeated_characters" in policy:
            max_repeat = policy["max_repeated_characters"]
            
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
            
            if max_run > max_repeat:
                errors.append("max_repeated_characters")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    except Exception:
        return {"valid": False, "errors": []}
