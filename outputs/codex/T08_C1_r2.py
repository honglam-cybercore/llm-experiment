import re

def redact(data, sensitive_keys, sensitive_patterns) -> object:
    try:
        sensitive = set()
        try:
            for key in sensitive_keys:
                if isinstance(key, str):
                    sensitive.add(key.casefold())
        except Exception:
            pass

        compiled = []
        try:
            for pattern in sensitive_patterns:
                if isinstance(pattern, str):
                    try:
                        compiled.append(re.compile(pattern))
                    except Exception:
                        pass
        except Exception:
            pass

        def redact_string(value):
            result = value
            for pattern in compiled:
                try:
                    result = pattern.sub("[REDACTED]", result)
                except Exception:
                    continue
            return result

        if isinstance(data, str):
            return redact_string(data)

        if not isinstance(data, (dict, list)):
            return data

        root = [None]
        memo = {}
        stack = [(data, root, 0, False)]

        while stack:
            value, parent, slot, sensitive_value = stack.pop()

            if sensitive_value:
                parent[slot] = "[REDACTED]"
                continue

            if isinstance(value, str):
                parent[slot] = redact_string(value)
            elif isinstance(value, list):
                identifier = id(value)
                if identifier in memo:
                    parent[slot] = memo[identifier]
                    continue

                result = []
                memo[identifier] = result
                parent[slot] = result

                for index in range(len(value) - 1, -1, -1):
                    stack.append((value[index], result, index, False))
            elif isinstance(value, dict):
                identifier = id(value)
                if identifier in memo:
                    parent[slot] = memo[identifier]
                    continue

                result = {}
                memo[identifier] = result
                parent[slot] = result

                items = list(value.items())
                for key, item in reversed(items):
                    is_sensitive = (
                        isinstance(key, str) and key.casefold() in sensitive
                    )
                    result[key] = None
                    stack.append((item, result, key, is_sensitive))
            else:
                parent[slot] = value

        return root[0]
    except Exception:
        return data