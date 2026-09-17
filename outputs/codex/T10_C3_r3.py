import copy
import math


class _ValidationError(Exception):
    pass


def validate_patch(document, operations, protected_paths) -> dict:
    try:
        _validate_json_value(document)
        if type(operations) is not list:
            raise _ValidationError("operations must be a list")
        if type(protected_paths) is not list:
            raise _ValidationError("protected_paths must be a list")

        protected = []
        for path in protected_paths:
            if type(path) is not str:
                raise _ValidationError("protected path must be a string")
            protected.append(_parse_pointer(path))

        current = copy.deepcopy(document)

        for index, operation in enumerate(operations):
            if type(operation) is not dict:
                raise _ValidationError(f"operation {index} must be an object")

            op = operation.get("op")
            path = operation.get("path")

            if type(op) is not str or op not in {"add", "remove", "replace"}:
                raise _ValidationError(f"invalid operation at index {index}")
            if type(path) is not str:
                raise _ValidationError(f"invalid path at index {index}")

            tokens = _parse_pointer(path)

            if op in {"add", "replace"}:
                if "value" not in operation:
                    raise _ValidationError(f"missing value at index {index}")
                _validate_json_value(operation["value"])

            if any(
                _is_prefix(tokens, protected_path)
                or _is_prefix(protected_path, tokens)
                for protected_path in protected
            ):
                raise _ValidationError(f"protected path at index {index}")

            if op == "add":
                current = _apply_add(current, tokens, operation["value"])
            elif op == "replace":
                current = _apply_replace(current, tokens, operation["value"])
            else:
                current = _apply_remove(current, tokens)

        return {"valid": True, "errors": []}

    except BaseException as exc:
        message = str(exc)
        if not message:
            message = "invalid patch"
        return {"valid": False, "errors": [message]}


def _validate_json_value(value, active=None):
    if active is None:
        active = set()

    value_type = type(value)

    if value is None or value_type is bool or value_type is str or value_type is int:
        return

    if value_type is float:
        if not math.isfinite(value):
            raise _ValidationError("non-finite number")
        return

    if value_type in (dict, list):
        object_id = id(value)
        if object_id in active:
            raise _ValidationError("cyclic JSON value")

        active.add(object_id)
        try:
            if value_type is dict:
                for key, item in value.items():
                    if type(key) is not str:
                        raise _ValidationError("object keys must be strings")
                    _validate_json_value(item, active)
            else:
                for item in value:
                    _validate_json_value(item, active)
        finally:
            active.remove(object_id)
        return

    raise _ValidationError("invalid JSON value")


def _parse_pointer(pointer):
    if pointer == "":
        return []

    if not pointer.startswith("/"):
        raise _ValidationError("invalid JSON Pointer")

    tokens = []
    for raw_token in pointer[1:].split("/"):
        token = []
        i = 0
        while i < len(raw_token):
            char = raw_token[i]
            if char != "~":
                token.append(char)
                i += 1
                continue

            if i + 1 >= len(raw_token) or raw_token[i + 1] not in {"0", "1"}:
                raise _ValidationError("invalid JSON Pointer escape")

            token.append("~" if raw_token[i + 1] == "0" else "/")
            i += 2

        tokens.append("".join(token))

    return tokens


def _is_prefix(prefix, value):
    return len(prefix) <= len(value) and prefix == value[:len(prefix)]


def _parse_array_index(token, length, allow_append=False):
    if allow_append and token == "-":
        return length

    if token == "" or (len(token) > 1 and token[0] == "0"):
        raise _ValidationError("invalid array index")
    if any(char < "0" or char > "9" for char in token):
        raise _ValidationError("invalid array index")

    index = int(token)
    if index >= length:
        raise _ValidationError("array index out of bounds")
    return index


def _get_parent(document, tokens):
    if not tokens:
        raise _ValidationError("root has no parent")

    current = document
    for token in tokens[:-1]:
        if type(current) is dict:
            if token not in current:
                raise _ValidationError("path does not exist")
            current = current[token]
        elif type(current) is list:
            index = _parse_array_index(token, len(current))
            current = current[index]
        else:
            raise _ValidationError("path does not exist")

    return current, tokens[-1]


def _apply_add(document, tokens, value):
    copied_value = copy.deepcopy(value)

    if not tokens:
        return copied_value

    parent, token = _get_parent(document, tokens)

    if type(parent) is dict:
        parent[token] = copied_value
        return document

    if type(parent) is list:
        if token == "-":
            parent.append(copied_value)
        else:
            if token == "" or (len(token) > 1 and token[0] == "0"):
                raise _ValidationError("invalid array index")
            if any(char < "0" or char > "9" for char in token):
                raise _ValidationError("invalid array index")
            index = int(token)
            if index > len(parent):
                raise _ValidationError("array index out of bounds")
            parent.insert(index, copied_value)
        return document

    raise _ValidationError("path does not exist")


def _apply_replace(document, tokens, value):
    copied_value = copy.deepcopy(value)

    if not tokens:
        return copied_value

    parent, token = _get_parent(document, tokens)

    if type(parent) is dict:
        if token not in parent:
            raise _ValidationError("path does not exist")
        parent[token] = copied_value
        return document

    if type(parent) is list:
        index = _parse_array_index(token, len(parent))
        parent[index] = copied_value
        return document

    raise _ValidationError("path does not exist")


def _apply_remove(document, tokens):
    if not tokens:
        raise _ValidationError("cannot remove document root")

    parent, token = _get_parent(document, tokens)

    if type(parent) is dict:
        if token not in parent:
            raise _ValidationError("path does not exist")
        del parent[token]
        return document

    if type(parent) is list:
        index = _parse_array_index(token, len(parent))
        del parent[index]
        return document

    raise _ValidationError("path does not exist")