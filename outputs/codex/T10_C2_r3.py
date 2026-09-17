import copy
import math
import re

_ARRAY_INDEX = re.compile(r"(?:0|[1-9][0-9]*)")


def _is_json_value(value, seen=None):
    if seen is None:
        seen = set()

    if value is None or isinstance(value, (str, bool, int)):
        return True

    if isinstance(value, float):
        return math.isfinite(value)

    if isinstance(value, (list, dict)):
        identity = id(value)
        if identity in seen:
            return False
        seen.add(identity)
        try:
            if isinstance(value, list):
                return all(_is_json_value(item, seen) for item in value)
            return all(
                isinstance(key, str) and _is_json_value(item, seen)
                for key, item in value.items()
            )
        finally:
            seen.remove(identity)

    return False


def _parse_pointer(pointer):
    if not isinstance(pointer, str):
        return None

    if pointer == "":
        return ()

    if not pointer.startswith("/"):
        return None

    tokens = []
    for token in pointer[1:].split("/"):
        result = []
        index = 0
        while index < len(token):
            char = token[index]
            if char != "~":
                result.append(char)
                index += 1
                continue
            if index + 1 >= len(token) or token[index + 1] not in "01":
                return None
            result.append("/" if token[index + 1] == "1" else "~")
            index += 2
        tokens.append("".join(result))

    return tuple(tokens)


def _is_related(path, protected):
    length = min(len(path), len(protected))
    return path[:length] == protected[:length]


def _array_index(token, allow_end, length):
    if not isinstance(token, str) or not _ARRAY_INDEX.fullmatch(token):
        return None
    try:
        index = int(token)
    except Exception:
        return None
    if index < 0 or index > length or (not allow_end and index >= length):
        return None
    return index


def _get_parent(root, tokens):
    if not tokens:
        return True, None, None

    current = root
    for token in tokens[:-1]:
        if isinstance(current, dict):
            if token not in current:
                return False, None, None
            current = current[token]
        elif isinstance(current, list):
            index = _array_index(token, False, len(current))
            if index is None:
                return False, None, None
            current = current[index]
        else:
            return False, None, None

    return True, current, tokens[-1]


def validate_patch(document, operations, protected_paths) -> dict:
    try:
        if not _is_json_value(document):
            return {"valid": False, "errors": ["Invalid document"]}

        if not isinstance(operations, list):
            return {"valid": False, "errors": ["Invalid operations"]}

        if not isinstance(protected_paths, list):
            return {"valid": False, "errors": ["Invalid protected paths"]}

        protected = []
        for pointer in protected_paths:
            parsed = _parse_pointer(pointer)
            if parsed is None:
                return {"valid": False, "errors": ["Invalid protected path"]}
            protected.append(parsed)

        current = copy.deepcopy(document)
        missing = object()

        for operation in operations:
            if not isinstance(operation, dict):
                return {"valid": False, "errors": ["Malformed operation"]}

            op = operation.get("op", missing)
            pointer = operation.get("path", missing)

            if op not in ("add", "remove", "replace"):
                return {"valid": False, "errors": ["Unsupported operation"]}

            tokens = _parse_pointer(pointer)
            if tokens is None:
                return {"valid": False, "errors": ["Invalid JSON Pointer"]}

            if op in ("add", "replace") and "value" not in operation:
                return {"valid": False, "errors": ["Missing operation value"]}

            if op in ("add", "replace") and not _is_json_value(operation["value"]):
                return {"valid": False, "errors": ["Invalid operation value"]}

            if any(_is_related(tokens, protected_path) for protected_path in protected):
                return {"valid": False, "errors": ["Protected path"]}

            if not tokens:
                if op == "remove":
                    current = missing
                else:
                    current = copy.deepcopy(operation["value"])
                continue

            if current is missing:
                return {"valid": False, "errors": ["Path does not exist"]}

            ok, parent, token = _get_parent(current, tokens)
            if not ok:
                return {"valid": False, "errors": ["Invalid parent path"]}

            if isinstance(parent, dict):
                if op == "add":
                    parent[token] = copy.deepcopy(operation["value"])
                elif op == "replace":
                    if token not in parent:
                        return {"valid": False, "errors": ["Path does not exist"]}
                    parent[token] = copy.deepcopy(operation["value"])
                else:
                    if token not in parent:
                        return {"valid": False, "errors": ["Path does not exist"]}
                    del parent[token]

            elif isinstance(parent, list):
                if op == "add" and token == "-":
                    parent.append(copy.deepcopy(operation["value"]))
                    continue

                index = _array_index(token, op == "add", len(parent))
                if index is None:
                    return {"valid": False, "errors": ["Invalid array index"]}

                if op == "add":
                    parent.insert(index, copy.deepcopy(operation["value"]))
                elif op == "replace":
                    parent[index] = copy.deepcopy(operation["value"])
                else:
                    parent.pop(index)

            else:
                return {"valid": False, "errors": ["Invalid parent path"]}

        return {"valid": True, "errors": []}

    except Exception:
        return {"valid": False, "errors": ["Invalid input"]}