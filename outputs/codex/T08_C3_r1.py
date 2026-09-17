import re

_REDACTED = "[REDACTED]"


def redact(data, sensitive_keys, sensitive_patterns) -> object:
    try:
        sensitive_key_set = set()
        try:
            for key in sensitive_keys:
                if isinstance(key, str):
                    sensitive_key_set.add(key.casefold())
        except BaseException:
            pass

        compiled_patterns = []
        try:
            for pattern in sensitive_patterns:
                if isinstance(pattern, str):
                    try:
                        compiled_patterns.append(re.compile(pattern))
                    except BaseException:
                        continue
        except BaseException:
            pass

        def redact_string(value):
            result = value
            for pattern in compiled_patterns:
                try:
                    result = pattern.sub(_REDACTED, result)
                except BaseException:
                    continue
            return result

        memo = {}
        stack = []

        def clone(value, force_redaction=False):
            if force_redaction:
                return _REDACTED

            if isinstance(value, str):
                return redact_string(value)

            if isinstance(value, dict):
                identity = id(value)
                if identity in memo:
                    return memo[identity]
                result = {}
                memo[identity] = result
                stack.append((value, result, iter(value.items()), True))
                return result

            if isinstance(value, list):
                identity = id(value)
                if identity in memo:
                    return memo[identity]
                result = []
                memo[identity] = result
                stack.append((value, result, iter(value), False))
                return result

            return value

        result = clone(data)

        while stack:
            source, target, iterator, is_dict = stack[-1]
            try:
                item = next(iterator)
            except StopIteration:
                stack.pop()
                continue
            except BaseException:
                stack.pop()
                continue

            if is_dict:
                try:
                    key, value = item
                    sensitive = (
                        isinstance(key, str)
                        and key.casefold() in sensitive_key_set
                    )
                    target[key] = clone(value, sensitive)
                except BaseException:
                    continue
            else:
                try:
                    target.append(clone(item))
                except BaseException:
                    continue

        return result
    except BaseException:
        return _REDACTED