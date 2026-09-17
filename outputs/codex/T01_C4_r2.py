def validate_password(password, policy, username=None) -> dict:
    try:
        if not isinstance(password, str) or not password:
            return {"valid": False, "errors": ["password"]}

        if not isinstance(policy, dict):
            return {"valid": False, "errors": ["policy"]}

        allowed_keys = {
            "min_length",
            "max_length",
            "require_uppercase",
            "require_lowercase",
            "require_digit",
            "require_special",
            "forbid_username",
            "max_repeated_characters",
        }

        if any(key not in allowed_keys for key in policy):
            return {"valid": False, "errors": ["policy"]}

        for key in policy:
            value = policy[key]
            if key in {
                "require_uppercase",
                "require_lowercase",
                "require_digit",
                "require_special",
                "forbid_username",
            }:
                if type(value) is not bool:
                    return {"valid": False, "errors": ["policy"]}
            elif key in {
                "min_length",
                "max_length",
                "max_repeated_characters",
            }:
                if type(value) is not int:
                    return {"valid": False, "errors": ["policy"]}

        if "min_length" in policy and policy["min_length"] < 0:
            return {"valid": False, "errors": ["policy"]}
        if "max_length" in policy and policy["max_length"] < 0:
            return {"valid": False, "errors": ["policy"]}
        if (
            "min_length" in policy
            and "max_length" in policy
            and policy["min_length"] > policy["max_length"]
        ):
            return {"valid": False, "errors": ["policy"]}
        if (
            "max_repeated_characters" in policy
            and policy["max_repeated_characters"] < 1
        ):
            return {"valid": False, "errors": ["policy"]}

        errors = []

        if "min_length" in policy and len(password) < policy["min_length"]:
            errors.append("min_length")

        if "max_length" in policy and len(password) > policy["max_length"]:
            errors.append("max_length")

        if policy.get("require_uppercase") and not any(
            character.isupper() for character in password
        ):
            errors.append("require_uppercase")

        if policy.get("require_lowercase") and not any(
            character.islower() for character in password
        ):
            errors.append("require_lowercase")

        if policy.get("require_digit") and not any(
            character.isdigit() for character in password
        ):
            errors.append("require_digit")

        if policy.get("require_special") and not any(
            not character.isalnum() for character in password
        ):
            errors.append("require_special")

        if policy.get("forbid_username"):
            if not isinstance(username, str) or not username:
                errors.append("forbid_username")
            elif username.casefold() in password.casefold():
                errors.append("forbid_username")

        if "max_repeated_characters" in policy:
            maximum = policy["max_repeated_characters"]
            longest_run = 1
            current_run = 1

            for index in range(1, len(password)):
                if password[index] == password[index - 1]:
                    current_run += 1
                    if current_run > longest_run:
                        longest_run = current_run
                else:
                    current_run = 1

            if longest_run > maximum:
                errors.append("max_repeated_characters")

        return {"valid": not errors, "errors": errors}
    except BaseException:
        return {"valid": False, "errors": ["input"]}