def validate_password(password, policy, username=None) -> dict:
    try:
        allowed = {
            "min_length",
            "max_length",
            "require_uppercase",
            "require_lowercase",
            "require_digit",
            "require_special",
            "forbid_username",
            "max_repeated_characters",
        }

        if type(password) is not str or type(policy) is not dict:
            return {"valid": False, "errors": ["policy"]}

        if username is not None and type(username) is not str:
            return {"valid": False, "errors": ["policy"]}

        keys = list(policy.keys())
        if any(type(key) is not str or key not in allowed for key in keys):
            return {"valid": False, "errors": ["policy"]}

        integer_rules = {"min_length", "max_length", "max_repeated_characters"}
        boolean_rules = {
            "require_uppercase",
            "require_lowercase",
            "require_digit",
            "require_special",
            "forbid_username",
        }

        for key in integer_rules:
            if key in policy and (
                type(policy[key]) is not int or policy[key] < 0
            ):
                return {"valid": False, "errors": [key]}

        for key in boolean_rules:
            if key in policy and type(policy[key]) is not bool:
                return {"valid": False, "errors": [key]}

        if (
            "max_repeated_characters" in policy
            and policy["max_repeated_characters"] < 1
        ):
            return {"valid": False, "errors": ["max_repeated_characters"]}

        if (
            "min_length" in policy
            and "max_length" in policy
            and policy["min_length"] > policy["max_length"]
        ):
            return {"valid": False, "errors": ["min_length", "max_length"]}

        errors = []
        password_length = len(password)

        if "min_length" in policy and password_length < policy["min_length"]:
            errors.append("min_length")

        if "max_length" in policy and password_length > policy["max_length"]:
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
            longest_run = 0
            current_run = 0
            previous = None

            for character in password:
                if current_run and character == previous:
                    current_run += 1
                else:
                    current_run = 1
                    previous = character
                if current_run > longest_run:
                    longest_run = current_run

            if longest_run > maximum:
                errors.append("max_repeated_characters")

        return {"valid": not errors, "errors": errors}
    except Exception:
        return {"valid": False, "errors": ["policy"]}