import re

def redact(data, sensitive_keys, sensitive_patterns) -> object:
    try:
        keys = {
            key.casefold()
            for key in sensitive_keys
            if isinstance(key, str)
        }

        patterns = []
        for pattern in sensitive_patterns:
            if isinstance(pattern, str):
                try:
                    patterns.append(re.compile(pattern))
                except Exception:
                    continue

        def transform(value):
            if isinstance(value, dict):
                result = {}
                for key, item in value.items():
                    if isinstance(key, str) and key.casefold() in keys:
                        result[key] = "[REDACTED]"
                    else:
                        result[key] = transform(item)
                return result

            if isinstance(value, list):
                return [transform(item) for item in value]

            if isinstance(value, str):
                for pattern in patterns:
                    try:
                        value = pattern.sub("[REDACTED]", value)
                    except Exception:
                        continue
                return value

            return value

        return transform(data)
    except Exception:
        if isinstance(data, dict):
            return {}
        if isinstance(data, list):
            return []
        if isinstance(data, str):
            return data
        return data