import re

def redact(data, sensitive_keys, sensitive_patterns) -> object:
    redacted = "[REDACTED]"

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
                except BaseException:
                    continue

        def redact_string(value):
            result = value
            for pattern in compiled_patterns:
                try:
                    result = pattern.sub(redacted, result)
                except BaseException:
                    continue
            return result

        def is_sensitive_key(key):
            try:
                return isinstance(key, str) and key.casefold() in key_names
            except BaseException:
                return False

        if isinstance(data, str):
            return redact_string(data)

        if not isinstance(data, (dict, list)):
            return data

        memo = {}

        if isinstance(data, dict):
            result = {}
        else:
            result = []

        memo[id(data)] = result
        stack = [(data, result)]

        while stack:
            source, destination = stack.pop()

            if isinstance(source, dict):
                for key, value in source.items():
                    if is_sensitive_key(key):
                        destination[key] = redacted
                    elif isinstance(value, str):
                        destination[key] = redact_string(value)
                    elif isinstance(value, (dict, list)):
                        existing = memo.get(id(value))
                        if existing is not None:
                            destination[key] = existing
                        else:
                            child = {} if isinstance(value, dict) else []
                            memo[id(value)] = child
                            destination[key] = child
                            stack.append((value, child))
                    else:
                        destination[key] = value

            else:
                for value in source:
                    if isinstance(value, str):
                        destination.append(redact_string(value))
                    elif isinstance(value, (dict, list)):
                        existing = memo.get(id(value))
                        if existing is not None:
                            destination.append(existing)
                        else:
                            child = {} if isinstance(value, dict) else []
                            memo[id(value)] = child
                            destination.append(child)
                            stack.append((value, child))
                    else:
                        destination.append(value)

        return result

    except BaseException:
        return redacted