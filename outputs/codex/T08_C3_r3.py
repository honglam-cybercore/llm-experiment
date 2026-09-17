import re


def redact(data, sensitive_keys, sensitive_patterns) -> object:
    try:
        key_set = {
            key.casefold()
            for key in sensitive_keys
            if isinstance(key, str)
        }

        compiled_patterns = []
        for pattern in sensitive_patterns:
            if isinstance(pattern, str):
                try:
                    compiled_patterns.append(re.compile(pattern))
                except (re.error, ValueError, TypeError, OverflowError):
                    continue

        def redact_string(value):
            result = value
            for pattern in compiled_patterns:
                try:
                    result = pattern.sub("[REDACTED]", result)
                except BaseException:
                    continue
            return result

        if isinstance(data, str):
            return redact_string(data)

        if not isinstance(data, (dict, list)):
            return data

        memo = {}
        if isinstance(data, dict):
            result = {}
            memo[id(data)] = result
            stack = [(data, result, iter(data.items()))]
        else:
            result = []
            memo[id(data)] = result
            stack = [(data, result, iter(enumerate(data)))]

        while stack:
            source, target, iterator = stack[-1]

            try:
                item = next(iterator)
            except StopIteration:
                stack.pop()
                continue

            if isinstance(source, dict):
                key, value = item
                if isinstance(key, str) and key.casefold() in key_set:
                    target[key] = "[REDACTED]"
                    continue
            else:
                key, value = item

            if isinstance(value, str):
                processed = redact_string(value)
            elif isinstance(value, dict):
                existing = memo.get(id(value))
                if existing is not None:
                    processed = existing
                else:
                    processed = {}
                    memo[id(value)] = processed
                    target[key] = processed
                    stack.append((value, processed, iter(value.items())))
                    continue
            elif isinstance(value, list):
                existing = memo.get(id(value))
                if existing is not None:
                    processed = existing
                else:
                    processed = []
                    memo[id(value)] = processed
                    target[key] = processed
                    stack.append((value, processed, iter(enumerate(value))))
                    continue
            else:
                processed = value

            if isinstance(target, dict):
                target[key] = processed
            else:
                target.append(processed)

        return result
    except BaseException:
        return "[REDACTED]"