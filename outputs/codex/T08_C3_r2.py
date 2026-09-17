import re

_REDACTED = "[REDACTED]"


def redact(data, sensitive_keys, sensitive_patterns) -> object:
    try:
        key_names = set()
        try:
            for key in sensitive_keys:
                if isinstance(key, str):
                    key_names.add(key.casefold())
        except BaseException:
            key_names = set()

        compiled_patterns = []
        try:
            for pattern in sensitive_patterns:
                if isinstance(pattern, str):
                    try:
                        compiled_patterns.append(re.compile(pattern))
                    except BaseException:
                        continue
        except BaseException:
            compiled_patterns = []

        def redact_string(value):
            result = value
            for pattern in compiled_patterns:
                try:
                    result = pattern.sub(_REDACTED, result)
                except BaseException:
                    return _REDACTED
            return result

        def is_sensitive_key(key):
            try:
                return isinstance(key, str) and key.casefold() in key_names
            except BaseException:
                return False

        def make_container(value):
            if isinstance(value, list):
                return []
            if isinstance(value, dict):
                return {}
            return None

        if isinstance(data, str):
            return redact_string(data)

        if not isinstance(data, (list, dict)):
            return data

        memo = {}
        root_output = make_container(data)
        memo[id(data)] = root_output

        if isinstance(data, list):
            stack = [(data, root_output, iter(enumerate(data)), False)]
        else:
            stack = [(data, root_output, iter(data.items()), True)]

        while stack:
            source, output, iterator, is_dict = stack[-1]

            try:
                key, value = next(iterator)
            except StopIteration:
                stack.pop()
                continue

            if is_dict and is_sensitive_key(key):
                output[key] = _REDACTED
                continue

            if isinstance(value, str):
                transformed = redact_string(value)
                if is_dict:
                    output[key] = transformed
                else:
                    output.append(transformed)
                continue

            if isinstance(value, (list, dict)):
                existing = memo.get(id(value))
                if existing is not None:
                    transformed = existing
                    if is_dict:
                        output[key] = transformed
                    else:
                        output.append(transformed)
                    continue

                transformed = make_container(value)
                memo[id(value)] = transformed

                if is_dict:
                    output[key] = transformed
                else:
                    output.append(transformed)

                if isinstance(value, list):
                    stack.append((value, transformed, iter(enumerate(value)), False))
                else:
                    stack.append((value, transformed, iter(value.items()), True))
                continue

            if is_dict:
                output[key] = value
            else:
                output.append(value)

        return root_output

    except BaseException:
        return _REDACTED