import math
from copy import deepcopy


def validate_patch(document, operations, protected_paths) -> dict:
    try:
        def validate_json(value, seen=None):
            if seen is None:
                seen = set()

            value_type = type(value)

            if value is None or value_type is bool or value_type is str:
                return True

            if value_type is int:
                return True

            if value_type is float:
                return math.isfinite(value)

            if value_type is list:
                identity = id(value)
                if identity in seen:
                    return False
                seen.add(identity)
                try:
                    return all(validate_json(item, seen) for item in value)
                finally:
                    seen.remove(identity)

            if value_type is dict:
                identity = id(value)
                if identity in seen:
                    return False
                seen.add(identity)
                try:
                    return all(
                        type(key) is str and validate_json(item, seen)
                        for key, item in value.items()
                    )
                finally:
                    seen.remove(identity)

            return False

        def parse_pointer(pointer):
            if type(pointer) is not str:
                return None

            if pointer == "":
                return ()

            if not pointer.startswith("/"):
                return None

            tokens = []
            for raw_token in pointer[1:].split("/"):
                decoded = []
                index = 0
                while index < len(raw_token):
                    char = raw_token[index]
                    if char != "~":
                        decoded.append(char)
                        index += 1
                        continue

                    if index + 1 >= len(raw_token):
                        return None

                    escape = raw_token[index + 1]
                    if escape == "0":
                        decoded.append("~")
                    elif escape == "1":
                        decoded.append("/")
                    else:
                        return None
                    index += 2

                tokens.append("".join(decoded))

            return tuple(tokens)

        def is_prefix(left, right):
            return len(left) <= len(right) and left == right[:len(left)]

        def array_index(token, length, allow_append=False):
            if allow_append and token == "-":
                return length

            if not token or (len(token) > 1 and token[0] == "0"):
                return None

            if not token.isdigit():
                return None

            try:
                index = int(token)
            except Exception:
                return None

            return index if 0 <= index < length else None

        if not validate_json(document):
            return {"valid": False, "errors": ["Invalid document"]}

        if type(operations) is not list:
            return {"valid": False, "errors": ["Invalid operations"]}

        if type(protected_paths) is not list:
            return {"valid": False, "errors": ["Invalid protected paths"]}

        protected = []
        for pointer in protected_paths:
            parsed = parse_pointer(pointer)
            if parsed is None:
                return {"valid": False, "errors": ["Invalid protected path"]}
            protected.append(parsed)

        current = deepcopy(document)

        def is_protected(path):
            for protected_path in protected:
                if is_prefix(protected_path, path) or is_prefix(path, protected_path):
                    return True
            return False

        def get_parent(root, tokens):
            parent = root
            for token in tokens:
                if type(parent) is dict:
                    if token not in parent:
                        return None
                    parent = parent[token]
                elif type(parent) is list:
                    index = array_index(token, len(parent))
                    if index is None:
                        return None
                    parent = parent[index]
                else:
                    return None
            return parent

        for operation in operations:
            if type(operation) is not dict:
                return {"valid": False, "errors": ["Malformed operation"]}

            op = operation.get("op")
            path_text = operation.get("path")

            if op not in ("add", "remove", "replace"):
                return {"valid": False, "errors": ["Unsupported operation"]}

            path = parse_pointer(path_text)
            if path is None:
                return {"valid": False, "errors": ["Invalid path"]}

            if op in ("add", "replace") and "value" not in operation:
                return {"valid": False, "errors": ["Missing value"]}

            if op in ("add", "replace") and not validate_json(operation["value"]):
                return {"valid": False, "errors": ["Invalid value"]}

            if is_protected(path):
                return {"valid": False, "errors": ["Protected path"]}

            if current is None:
                if not (op == "add" and len(path) == 0):
                    return {"valid": False, "errors": ["Path does not exist"]}

            if len(path) == 0:
                if op == "remove":
                    current = None
                else:
                    current = deepcopy(operation["value"])
                continue

            parent = get_parent(current, path[:-1])
            if parent is None:
                return {"valid": False, "errors": ["Invalid parent path"]}

            token = path[-1]
            value = deepcopy(operation.get("value"))

            if type(parent) is dict:
                if op == "add":
                    parent[token] = value
                elif op == "replace":
                    if token not in parent:
                        return {"valid": False, "errors": ["Path does not exist"]}
                    parent[token] = value
                else:
                    if token not in parent:
                        return {"valid": False, "errors": ["Path does not exist"]}
                    del parent[token]

            elif type(parent) is list:
                if op == "add":
                    index = array_index(token, len(parent), allow_append=True)
                    if index is None or index > len(parent):
                        return {"valid": False, "errors": ["Invalid array index"]}
                    parent.insert(index, value)
                else:
                    index = array_index(token, len(parent))
                    if index is None:
                        return {"valid": False, "errors": ["Path does not exist"]}
                    if op == "replace":
                        parent[index] = value
                    else:
                        del parent[index]
            else:
                return {"valid": False, "errors": ["Invalid parent path"]}

        return {"valid": True, "errors": []}

    except Exception:
        return {"valid": False, "errors": ["Invalid input"]}