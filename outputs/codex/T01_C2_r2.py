def validate_password(password, policy, username=None) -> dict:
    try:
        if type(password) is not str:
            return {"valid": False, "errors": ["password"]}

        if type(policy) is not dict:
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
            if key in policy and type(policy[key]) is not int:
                return {"valid": False, "errors": ["policy"]}

        for key in boolean_keys:
            if key in policy and type(policy[key]) is not bool:
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

        if username is not None and type(username) is not str:
            return {"valid": False, "errors": ["username"]}

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
            if username is None or username == "":
                errors.append("forbid_username")
            elif username.casefold() in password.casefold():
                errors.append("forbid_username")

        if "max_repeated_characters" in policy:
            maximum = policy["max_repeated_characters"]
            run_length = 0
            previous = None

            for character in password:
                if character == previous:
                    run_length += 1
                else:
                    previous = character
                    run_length = 1

                if run_length > maximum:
                    errors.append("max_repeated_characters")
                    break

        return {"valid": not errors, "errors": errors}

    except BaseException:
        return {"valid": False, "errors": ["input"]}