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

    def process(value):
        try:
            if isinstance(value, dict):
                result = {}
                for key, item in value.items():
                    if isinstance(key, str) and key.casefold() in keys:
                        result[key] = "[REDACTED]"
                    else:
                        result[key] = process(item)
                return result

            if isinstance(value, list):
                return [process(item) for item in value]

            if isinstance(value, str):
                for pattern in patterns:
                    try:
                        value = pattern.sub("[REDACTED]", value)
                    except Exception:
                        pass
                return value

            return value
        except Exception:
            return value

    try:
        return process(data)
    except Exception:
        return data