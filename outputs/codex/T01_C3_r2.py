def validate_password(password, policy, username=None) -> dict:
    try:
        if not isinstance(password, str) or not isinstance(policy, dict):
            return {"valid": False, "errors": ["policy"]}

        if username is not None and not isinstance(username, str):
            return {"valid": False, "errors": ["forbid_username"]}

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

        integer_keys = {
            "min_length",
            "max_length",
            "max_repeated_characters",
        }
        boolean_keys = {
            "require_uppercase",
            "require_lowercase",
            "require_digit",
            "require_special",
            "forbid_username",
        }

        for key in integer_keys:
            if key in policy and (
                type(policy[key]) is not int or policy[key] < 0
            ):
                return {"valid": False, "errors": [key]}

        for key in boolean_keys:
            if key in policy and type(policy[key]) is not bool:
                return {"valid": False, "errors": [key]}

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
            return {"valid": False, "errors": ["max_repeated_characters"]}

        errors = []
        password_length = len(password)

        if "min_length" in policy and password_length < policy["min_length"]:
            errors.append("min_length")

        if "max_length" in policy and password_length > policy["max_length"]:
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

        if policy.get("forbid_username") and username:
            if username.casefold() in password.casefold():
                errors.append("forbid_username")

        if "max_repeated_characters" in policy:
            limit = policy["max_repeated_characters"]
            run_length = 0
            previous = None

            for character in password:
                if character == previous:
                    run_length += 1
                else:
                    previous = character
                    run_length = 1

                if run_length > limit:
                    errors.append("max_repeated_characters")
                    break

        return {"valid": not errors, "errors": errors}
    except BaseException:
        return {"valid": False, "errors": ["policy"]}