def validate_password(password, policy, username=None) -> dict:
    try:
        if not isinstance(password, str):
            return {"valid": False, "errors": []}
        
        if not isinstance(policy, dict):
            return {"valid": False, "errors": []}
        
        if username is not None and not isinstance(username, str):
            return {"valid": False, "errors": []}
        
        errors = []
        
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
            if policy["require_special"] and not any(not c.isalnum() for c in password):
                errors.append("require_special")
        
        if "forbid_username" in policy:
            if not isinstance(policy["forbid_username"], bool):
                return {"valid": False, "errors": []}
            if policy["forbid_username"] and username:
                if username.lower() in password.lower():
                    errors.append("forbid_username")
        
        if "max_repeated_characters" in policy:
            max_repeated = policy["max_repeated_characters"]
            if not isinstance(max_repeated, int):
                return {"valid": False, "errors": []}
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
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    except:
        return {"valid": False, "errors": []}
