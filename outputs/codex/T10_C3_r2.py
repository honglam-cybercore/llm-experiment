import math


def _decode_pointer(pointer):
    if type(pointer) is not str or (pointer and not pointer.startswith("/")):
        return None

    if pointer == "":
        return ()

    tokens = []
    for raw in pointer[1:].split("/"):
        chars = []
        i = 0
        while i < len(raw):
            char = raw[i]
            if char == "~":
                if i + 1 >= len(raw) or raw[i + 1] not in ("0", "1"):
                    return None
                chars.append("~" if raw[i + 1] == "0" else "/")
                i += 2
            else:
                chars.append(char)
                i += 1
        tokens.append("".join(chars))
    return tuple(tokens)


def _clone_json(value, active=None):
    if type(value) in (str, int, bool) or value is None:
        return True, value

    if type(value) is float:
        return (math.isfinite(value), value)

    if active is None:
        active = set()

    value_id = id(value)
    if value_id in active:
        return False, None

    if type(value) is list:
        active.add(value_id)
        result = []
        try:
            for item in value:
                valid, cloned = _clone_json(item, active)
                if not valid:
                    return False, None
                result.append(cloned)
        finally:
            active.remove(value_id)
        return True, result

    if type(value) is dict:
        active.add(value_id)
        result = {}
        try:
            for key, item in value.items():
                if type(key) is not str:
                    return False, None
                valid, cloned = _clone_json(item, active)
                if not valid:
                    return False, None
                result[key] = cloned
        finally:
            active.remove(value_id)
        return True, result

    return False, None


def _is_prefix(prefix, path):
    return len(prefix) <= len(path) and prefix == path[:len(prefix)]


def _array_index(token, length, allow_end=False):
    if type(token) is not str or not token:
        return None

    if token == "0":
        index = 0
    elif token[0] == "0" or any(char < "0" or char > "9" for char in token):
        return None
    else:
        index = int(token)

    if index < 0 or index > length or (not allow_end and index >= length):
        return None
    return index


def _resolve_parent(document, tokens):
    if not tokens:
        return True, None, None

    current = document
    for token in tokens[:-1]:
        if type(current) is dict:
            if token not in current:
                return False, None, None
            current = current[token]
        elif type(current) is list:
            index = _array_index(token, len(current))
            if index is None:
                return False, None, None
            current = current[index]
        else:
            return False, None, None

    return True, current, tokens[-1]


def validate_patch(document, operations, protected_paths) -> dict:
    try:
        valid_document, state = _clone_json(document)
        if not valid_document:
            return {"valid": False, "errors": ["invalid document"]}

        if type(operations) is not list or type(protected_paths) is not list:
            return {"valid": False, "errors": ["invalid input"]}

        protected = []
        for index, pointer in enumerate(protected_paths):
            tokens = _decode_pointer(pointer)
            if tokens is None:
                return {"valid": False, "errors": [f"invalid protected path {index}"]}
            protected.append(tokens)

        errors = []

        for op_index, operation in enumerate(operations):
            error = None

            if type(operation) is not dict:
                error = "operation must be an object"
            else:
                op = operation.get("op")
                path = operation.get("path")

                if type(op) is not str or op not in ("add", "remove", "replace"):
                    error = "unsupported operation"
                elif type(path) is not str:
                    error = "invalid path"
                else:
                    tokens = _decode_pointer(path)
                    if tokens is None:
                        error = "invalid path"
                    elif op in ("add", "replace") and "value" not in operation:
                        error = "missing value"
                    else:
                        if op in ("add", "replace"):
                            value_valid, value = _clone_json(operation.get("value"))
                            if not value_valid:
                                error = "invalid value"

                        if error is None:
                            for protected_tokens in protected:
                                if _is_prefix(protected_tokens, tokens) or _is_prefix(tokens, protected_tokens):
                                    error = "protected path"
                                    break

                        if error is None:
                            if not tokens:
                                if op == "remove":
                                    error = "cannot remove document root"
                                else:
                                    state = value
                            else:
                                resolved, parent, final_token = _resolve_parent(state, tokens)
                                if not resolved:
                                    error = "path does not exist"

                                elif type(parent) is dict:
                                    if op == "remove":
                                        if final_token not in parent:
                                            error = "path does not exist"
                                        else:
                                            del parent[final_token]
                                    elif op == "replace":
                                        if final_token not in parent:
                                            error = "path does not exist"
                                        else:
                                            parent[final_token] = value
                                    else:
                                        parent[final_token] = value

                                elif type(parent) is list:
                                    if op == "add":
                                        if final_token == "-":
                                            parent.append(value)
                                        else:
                                            index = _array_index(
                                                final_token, len(parent), allow_end=True
                                            )
                                            if index is None:
                                                error = "invalid array index"
                                            else:
                                                parent.insert(index, value)
                                    else:
                                        index = _array_index(final_token, len(parent))
                                        if index is None:
                                            error = "path does not exist"
                                        elif op == "remove":
                                            parent.pop(index)
                                        else:
                                            parent[index] = value
                                else:
                                    error = "invalid parent"

            if error is not None:
                errors.append(f"operation {op_index}: {error}")

        return {"valid": not errors, "errors": errors}
    except BaseException:
        return {"valid": False, "errors": ["invalid input"]}