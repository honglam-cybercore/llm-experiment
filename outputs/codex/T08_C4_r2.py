import re

_REDACTED = "[REDACTED]"


def redact(data, sensitive_keys, sensitive_patterns) -> object:
    try:
        key_names = set()
        for key in sensitive_keys:
            if isinstance(key, str):
                key_names.add(key.casefold())

        patterns = []
        for pattern in sensitive_patterns:
            if isinstance(pattern, str):
                try:
                    patterns.append(re.compile(pattern))
                except Exception:
                    continue

        def transform(value):
            if isinstance(value, str):
                result = value
                for pattern in patterns:
                    try:
                        result = pattern.sub(_REDACTED, result)
                    except Exception:
                        continue
                return result

            if isinstance(value, list):
                result = []
                for item in value:
                    try:
                        result.append(transform(item))
                    except Exception:
                        result.append(item)
                return result

            if isinstance(value, dict):
                result = {}
                for key, item in value.items():
                    try:
                        if isinstance(key, str) and key.casefold() in key_names:
                            result[key] = _REDACTED
                        else:
                            result[key] = transform(item)
                    except Exception:
                        try:
                            result[key] = item
                        except Exception:
                            continue
                return result

            return value

        return transform(data)
    except Exception:
        return data