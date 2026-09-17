import re

def redact(data, sensitive_keys, sensitive_patterns) -> object:
    try:
        keys = {
            key.casefold()
            for key in sensitive_keys
            if isinstance(key, str)
        }
    except Exception:
        keys = set()

    patterns = []
    try:
        for pattern in sensitive_patterns:
            if isinstance(pattern, str):
                try:
                    patterns.append(re.compile(pattern))
                except Exception:
                    pass
    except Exception:
        pass

    memo = {}

    def transform(value):
        try:
            if isinstance(value, str):
                result = value
                for pattern in patterns:
                    try:
                        result = pattern.sub("[REDACTED]", result)
                    except Exception:
                        pass
                return result

            if isinstance(value, dict):
                identifier = id(value)
                if identifier in memo:
                    return memo[identifier]

                result = {}
                memo[identifier] = result

                for key, item in value.items():
                    try:
                        sensitive = isinstance(key, str) and key.casefold() in keys
                    except Exception:
                        sensitive = False
                    result[key] = "[REDACTED]" if sensitive else transform(item)

                return result

            if isinstance(value, list):
                identifier = id(value)
                if identifier in memo:
                    return memo[identifier]

                result = []
                memo[identifier] = result
                result.extend(transform(item) for item in value)
                return result

            return value
        except Exception:
            return value

    try:
        return transform(data)
    except Exception:
        return data