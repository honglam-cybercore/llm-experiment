import re

_REDACTED = "[REDACTED]"


def redact(data, sensitive_keys, sensitive_patterns) -> object:
    try:
        keys = {
            key.casefold()
            for key in sensitive_keys
            if isinstance(key, str)
        } if isinstance(sensitive_keys, list) else set()

        compiled_patterns = []
        if isinstance(sensitive_patterns, list):
            for pattern in sensitive_patterns:
                if isinstance(pattern, str):
                    try:
                        compiled_patterns.append(re.compile(pattern))
                    except Exception:
                        continue

        memo = {}

        def redact_string(value):
            result = value
            for pattern in compiled_patterns:
                try:
                    result = pattern.sub(_REDACTED, result)
                except Exception:
                    continue
            return result

        def transform(value):
            value_id = id(value)

            if isinstance(value, dict):
                if value_id in memo:
                    return memo[value_id]

                result = {}
                memo[value_id] = result

                for key, item in value.items():
                    try:
                        is_sensitive = (
                            isinstance(key, str)
                            and key.casefold() in keys
                        )
                        result[key] = _REDACTED if is_sensitive else transform(item)
                    except Exception:
                        try:
                            result[key] = item
                        except Exception:
                            continue
                return result

            if isinstance(value, list):
                if value_id in memo:
                    return memo[value_id]

                result = []
                memo[value_id] = result

                for item in value:
                    try:
                        result.append(transform(item))
                    except Exception:
                        result.append(item)
                return result

            if isinstance(value, str):
                return redact_string(value)

            return value

        return transform(data)
    except Exception:
        if isinstance(data, (dict, list)):
            return {} if isinstance(data, dict) else []
        return data