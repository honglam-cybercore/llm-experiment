def validate_password(password, policy, username=None) -> dict:
    try:
        if not isinstance(password, str) or not isinstance(policy, dict):
            return {"valid": False, "errors": ["password" if not isinstance(password, str) else "policy"]}

        errors = []
        integer_keys = {"min_length", "max_length", "max_repeated_characters"}
        boolean_keys = {
            "require_uppercase",
            "require_lowercase",
            "require_digit",
            "require_special",
            "forbid_username",
        }

        for key in integer_keys:
            if key in policy and (
                isinstance(policy[key], bool) or not isinstance(policy[key], int)
            ):
                return {"valid": False, "errors": ["policy"]}

        for key in boolean_keys:
            if key in policy and not isinstance(policy[key], bool):
                return {"valid": False, "errors": ["policy"]}

        min_length = policy.get("min_length")
        max_length = policy.get("max_length")
        max_repeated = policy.get("max_repeated_characters")

        if min_length is not None and min_length < 0:
            return {"valid": False, "errors": ["policy"]}
        if max_length is not None and max_length < 0:
            return {"valid": False, "errors": ["policy"]}
        if (
            min_length is not None
            and max_length is not None
            and min_length > max_length
        ):
            return {"valid": False, "errors": ["policy"]}
        if max_repeated is not None and max_repeated < 1:
            return {"valid": False, "errors": ["policy"]}

        if "min_length" in policy and len(password) < min_length:
            errors.append("min_length")
        if "max_length" in policy and len(password) > max_length:
            errors.append("max_length")
        if policy.get("require_uppercase") and not any(c.isupper() for c in password):
            errors.append("require_uppercase")
        if policy.get("require_lowercase") and not any(c.islower() for c in password):
            errors.append("require_lowercase")
        if policy.get("require_digit") and not any(c.isdigit() for c in password):
            errors.append("require_digit")
        if policy.get("require_special") and not any(not c.isalnum() for c in password):
            errors.append("require_special")

        if policy.get("forbid_username"):
            if not isinstance(username, str) or not username:
                errors.append("forbid_username")
            elif username.casefold() in password.casefold():
                errors.append("forbid_username")

        if "max_repeated_characters" in policy:
            longest_run = 0
            current_run = 0
            previous = object()

            for character in password:
                if character == previous:
                    current_run += 1
                else:
                    previous = character
                    current_run = 1
                longest_run = max(longest_run, current_run)

            if longest_run > max_repeated:
                errors.append("max_repeated_characters")

        return {"valid": not errors, "errors": errors}
    except Exception:
        return {"valid": False, "errors": ["policy"]}