def validate_password(password, policy, username=None) -> dict:
    errors = []

    try:
        if not isinstance(password, str):
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

        for key in policy:
            if key not in allowed_keys:
                errors.append("policy")

        int_keys = {"min_length", "max_length", "max_repeated_characters"}
        bool_keys = {
            "require_uppercase",
            "require_lowercase",
            "require_digit",
            "require_special",
            "forbid_username",
        }

        for key in int_keys:
            if key in policy:
                value = policy[key]
                if isinstance(value, bool) or not isinstance(value, int):
                    errors.append(key)
                elif value < 0 or (
                    key == "max_repeated_characters" and value < 1
                ):
                    errors.append(key)

        for key in bool_keys:
            if key in policy and not isinstance(policy[key], bool):
                errors.append(key)

        if "min_length" in policy and "max_length" in policy:
            if (
                isinstance(policy["min_length"], int)
                and not isinstance(policy["min_length"], bool)
                and isinstance(policy["max_length"], int)
                and not isinstance(policy["max_length"], bool)
                and policy["min_length"] > policy["max_length"]
            ):
                errors.extend(["min_length", "max_length"])

        if username is not None and not isinstance(username, str):
            return {"valid": False, "errors": ["username"]}

        if errors:
            return {"valid": False, "errors": list(dict.fromkeys(errors))}

        if "min_length" in policy and len(password) < policy["min_length"]:
            errors.append("min_length")

        if "max_length" in policy and len(password) > policy["max_length"]:
            errors.append("max_length")

        if policy.get("require_uppercase", False) and not any(
            character.isupper() for character in password
        ):
            errors.append("require_uppercase")

        if policy.get("require_lowercase", False) and not any(
            character.islower() for character in password
        ):
            errors.append("require_lowercase")

        if policy.get("require_digit", False) and not any(
            character.isdigit() for character in password
        ):
            errors.append("require_digit")

        if policy.get("require_special", False) and not any(
            not character.isalnum() for character in password
        ):
            errors.append("require_special")

        if policy.get("forbid_username", False) and username:
            if username.casefold() in password.casefold():
                errors.append("forbid_username")

        if "max_repeated_characters" in policy:
            maximum = policy["max_repeated_characters"]
            longest = 0
            current = 0
            previous = None

            for character in password:
                if character == previous:
                    current += 1
                else:
                    previous = character
                    current = 1
                longest = max(longest, current)

            if longest > maximum:
                errors.append("max_repeated_characters")

        errors = list(dict.fromkeys(errors))
        return {"valid": not errors, "errors": errors}

    except Exception:
        return {"valid": False, "errors": ["policy"]}