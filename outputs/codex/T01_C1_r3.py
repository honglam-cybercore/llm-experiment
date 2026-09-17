def validate_password(password, policy, username=None) -> dict:
    try:
        if not isinstance(password, str) or not isinstance(policy, dict):
            return {"valid": False, "errors": ["policy"]}

        keys = (
            "min_length",
            "max_length",
            "require_uppercase",
            "require_lowercase",
            "require_digit",
            "require_special",
            "forbid_username",
            "max_repeated_characters",
        )

        values = {}
        for key in keys:
            if dict.__contains__(policy, key):
                values[key] = dict.__getitem__(policy, key)

        integer_keys = ("min_length", "max_length", "max_repeated_characters")
        for key in integer_keys:
            if key in values and (
                type(values[key]) is not int or values[key] < 0
            ):
                return {"valid": False, "errors": [key]}

        if (
            "max_repeated_characters" in values
            and values["max_repeated_characters"] < 1
        ):
            return {"valid": False, "errors": ["max_repeated_characters"]}

        boolean_keys = (
            "require_uppercase",
            "require_lowercase",
            "require_digit",
            "require_special",
            "forbid_username",
        )
        for key in boolean_keys:
            if key in values and type(values[key]) is not bool:
                return {"valid": False, "errors": [key]}

        if (
            "min_length" in values
            and "max_length" in values
            and values["min_length"] > values["max_length"]
        ):
            return {"valid": False, "errors": ["min_length", "max_length"]}

        if (
            values.get("forbid_username") is True
            and username is not None
            and not isinstance(username, str)
        ):
            return {"valid": False, "errors": ["forbid_username"]}

        errors = []
        length = len(password)

        if "min_length" in values and length < values["min_length"]:
            errors.append("min_length")

        if "max_length" in values and length > values["max_length"]:
            errors.append("max_length")

        if values.get("require_uppercase") is True and not any(
            str.isupper(char) for char in password
        ):
            errors.append("require_uppercase")

        if values.get("require_lowercase") is True and not any(
            str.islower(char) for char in password
        ):
            errors.append("require_lowercase")

        if values.get("require_digit") is True and not any(
            str.isdigit(char) for char in password
        ):
            errors.append("require_digit")

        if values.get("require_special") is True and not any(
            not str.isalnum(char) for char in password
        ):
            errors.append("require_special")

        if values.get("forbid_username") is True and isinstance(username, str):
            if username and str.casefold(username) in str.casefold(password):
                errors.append("forbid_username")

        if "max_repeated_characters" in values:
            limit = values["max_repeated_characters"]
            run_length = 0
            previous = None
            for char in password:
                if char == previous:
                    run_length += 1
                else:
                    previous = char
                    run_length = 1
                if run_length > limit:
                    errors.append("max_repeated_characters")
                    break

        return {"valid": not errors, "errors": errors}
    except BaseException:
        return {"valid": False, "errors": ["policy"]}