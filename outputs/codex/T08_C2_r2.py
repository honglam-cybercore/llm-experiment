import re


def redact(data, sensitive_keys, sensitive_patterns) -> object:
    try:
        key_names = {
            key.casefold()
            for key in sensitive_keys
            if isinstance(key, str)
        }
    except Exception:
        key_names = set()

    compiled_patterns = []
    try:
        for pattern in sensitive_patterns:
            if isinstance(pattern, str):
                try:
                    compiled_patterns.append(re.compile(pattern))
                except Exception:
                    continue
    except Exception:
        pass

    def process(value):
        try:
            if isinstance(value, dict):
                result = {}
                for key, item in value.items():
                    if isinstance(key, str) and key.casefold() in key_names:
                        result[key] = "[REDACTED]"
                    else:
                        result[key] = process(item)
                return result

            if isinstance(value, list):
                return [process(item) for item in value]

            if isinstance(value, str):
                result = value
                for pattern in compiled_patterns:
                    try:
                        result = pattern.sub("[REDACTED]", result)
                    except Exception:
                        continue
                return result

            return value
        except Exception:
            return value

    try:
        return process(data)
    except Exception:
        return data