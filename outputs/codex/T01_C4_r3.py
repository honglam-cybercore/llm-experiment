def validate_password(password, policy, username=None) -> dict:
    errors = []

    try:
        if type(password) is not str or not password:
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

        if any(type(key) is not str or key not in allowed_keys for key in policy):
            return {"valid": False, "errors": ["policy"]}

        for key, value in policy.items():
            if key in {"min_length", "max_length", "max_repeated_characters"}:
                if type(value) is not int or value < 0:
                    errors.append(key)
            elif type(value) is not bool:
                errors.append(key)

        if errors:
            return {"valid": False, "errors": errors}

        min_length = policy.get("min_length")
        max_length = policy.get("max_length")
        max_repeated = policy.get("max_repeated_characters")

        if min_length is not None and max_length is not None and min_length > max_length:
            return {"valid": False, "errors": ["min_length", "max_length"]}

        if max_repeated is not None and max_repeated < 1:
            return {"valid": False, "errors": ["max_repeated_characters"]}

        password_length = len(password)

        if min_length is not None and password_length < min_length:
            errors.append("min_length")

        if max_length is not None and password_length > max_length:
            errors.append("max_length")

        if policy.get("require_uppercase") and not any(char.isupper() for char in password):
            errors.append("require_uppercase")

        if policy.get("require_lowercase") and not any(char.islower() for char in password):
            errors.append("require_lowercase")

        if policy.get("require_digit") and not any(char.isdigit() for char in password):
            errors.append("require_digit")

        if policy.get("require_special") and not any(
            not char.isalnum() for char in password
        ):
            errors.append("require_special")

        if policy.get("forbid_username"):
            if type(username) is not str or not username:
                errors.append("forbid_username")
            elif username.casefold() in password.casefold():
                errors.append("forbid_username")

        if max_repeated is not None:
            run_length = 1
            for index in range(1, password_length):
                if password[index] == password[index - 1]:
                    run_length += 1
                    if run_length > max_repeated:
                        errors.append("max_repeated_characters")
                        break
                else:
                    run_length = 1

        return {"valid": not errors, "errors": errors}
    except Exception:
        return {"valid": False, "errors": ["validation"]}