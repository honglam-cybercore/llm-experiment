import re


def redact(data, sensitive_keys, sensitive_patterns) -> object:
    try:
        key_names = {
            key.casefold()
            for key in sensitive_keys
            if isinstance(key, str)
        }

        compiled_patterns = []
        for pattern in sensitive_patterns:
            if isinstance(pattern, str):
                try:
                    compiled_patterns.append(re.compile(pattern))
                except Exception:
                    pass

        def redact_string(value):
            try:
                for pattern in compiled_patterns:
                    value = pattern.sub("[REDACTED]", value)
                return value
            except Exception:
                return value

        if isinstance(data, str):
            return redact_string(data)

        if not isinstance(data, (dict, list)):
            return data

        memo = {}
        if isinstance(data, dict):
            result = {}
            memo[id(data)] = result
        else:
            result = []
            memo[id(data)] = result

        stack = [(data, result)]

        while stack:
            source, target = stack.pop()

            if isinstance(source, dict):
                for key, value in source.items():
                    try:
                        is_sensitive = (
                            isinstance(key, str)
                            and key.casefold() in key_names
                        )
                    except Exception:
                        is_sensitive = False

                    if is_sensitive:
                        target[key] = "[REDACTED]"
                    elif isinstance(value, str):
                        target[key] = redact_string(value)
                    elif isinstance(value, (dict, list)):
                        existing = memo.get(id(value))
                        if existing is None:
                            existing = {} if isinstance(value, dict) else []
                            memo[id(value)] = existing
                            stack.append((value, existing))
                        target[key] = existing
                    else:
                        target[key] = value

            else:
                for value in source:
                    if isinstance(value, str):
                        target.append(redact_string(value))
                    elif isinstance(value, (dict, list)):
                        existing = memo.get(id(value))
                        if existing is None:
                            existing = {} if isinstance(value, dict) else []
                            memo[id(value)] = existing
                            stack.append((value, existing))
                        target.append(existing)
                    else:
                        target.append(value)

        return result
    except Exception:
        return data