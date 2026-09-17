def validate_patch(document, operations, protected_paths) -> dict:
    import math
    import copy

    errors = []

    def is_json_value(value, seen=None):
        if value is None or isinstance(value, (bool, str)):
            return True
        if isinstance(value, int) and not isinstance(value, bool):
            return True
        if isinstance(value, float):
            return math.isfinite(value)

        if seen is None:
            seen = set()

        if isinstance(value, (dict, list)):
            identity = id(value)
            if identity in seen:
                return False
            seen.add(identity)

            if isinstance(value, dict):
                valid = all(
                    isinstance(key, str) and is_json_value(item, seen)
                    for key, item in value.items()
                )
            else:
                valid = all(is_json_value(item, seen) for item in value)

            seen.remove(identity)
            return valid

        return False

    def parse_pointer(pointer):
        if not isinstance(pointer, str):
            return None

        if pointer == "":
            return ()

        if not pointer.startswith("/"):
            return None

        tokens = []
        for token in pointer[1:].split("/"):
            decoded = []
            index = 0
            while index < len(token):
                char = token[index]
                if char != "~":
                    decoded.append(char)
                    index += 1
                    continue

                if index + 1 >= len(token) or token[index + 1] not in ("0", "1"):
                    return None

                decoded.append("~" if token[index + 1] == "0" else "/")
                index += 2

            tokens.append("".join(decoded))

        return tuple(tokens)

    def array_index(token, allow_end=False):
        if not isinstance(token, str) or not token:
            return None
        if token == "0":
            return 0
        if token[0] == "0" or not token.isdigit():
            return None
        try:
            value = int(token)
        except Exception:
            return None
        return value

    try:
        if not is_json_value(document):
            errors.append("document is not valid JSON-like data")
            return {"valid": False, "errors": errors}

        if not isinstance(operations, list):
            errors.append("operations must be a list")
            return {"valid": False, "errors": errors}

        if not isinstance(protected_paths, list):
            errors.append("protected_paths must be a list")
            return {"valid": False, "errors": errors}

        protected = []
        for index, pointer in enumerate(protected_paths):
            parsed = parse_pointer(pointer)
            if parsed is None:
                errors.append(f"protected path at index {index} is not a valid JSON Pointer")
            else:
                protected.append(parsed)

        if errors:
            return {"valid": False, "errors": errors}

        state = copy.deepcopy(document)
        missing = object()
        state = state

        def is_protected(path, operation):
            for protected_path in protected:
                if path[:len(protected_path)] == protected_path:
                    return True
                if operation in ("remove", "replace") and protected_path[:len(path)] == path:
                    return True
            return False

        def resolve_parent(root, path):
            current = root
            for token in path[:-1]:
                if isinstance(current, dict):
                    if token not in current:
                        return None, None
                    current = current[token]
                elif isinstance(current, list):
                    index = array_index(token)
                    if index is None or index >= len(current):
                        return None, None
                    current = current[index]
                else:
                    return None, None
            return current, path[-1]

        for op_index, operation in enumerate(operations):
            prefix = f"operation at index {op_index}"

            if not isinstance(operation, dict):
                errors.append(f"{prefix} must be an object")
                continue

            op = operation.get("op")
            pointer = operation.get("path")

            if op not in ("add", "remove", "replace"):
                errors.append(f"{prefix} has an invalid op")
                continue

            path = parse_pointer(pointer)
            if path is None:
                errors.append(f"{prefix} has an invalid path")
                continue

            if op in ("add", "replace") and "value" not in operation:
                errors.append(f"{prefix} is missing value")
                continue

            if op in ("add", "replace") and not is_json_value(operation["value"]):
                errors.append(f"{prefix} has an invalid value")
                continue

            if is_protected(path, op):
                errors.append(f"{prefix} targets a protected path")
                continue

            if not path:
                if op == "remove":
                    if state is missing:
                        errors.append(f"{prefix} targets a missing path")
                    else:
                        state = missing
                elif op == "replace":
                    if state is missing:
                        errors.append(f"{prefix} targets a missing path")
                    else:
                        state = copy.deepcopy(operation["value"])
                else:
                    state = copy.deepcopy(operation["value"])
                continue

            if state is missing:
                errors.append(f"{prefix} has no existing parent")
                continue

            parent, token = resolve_parent(state, path)
            if parent is None:
                errors.append(f"{prefix} has no existing parent")
                continue

            if isinstance(parent, dict):
                if op == "add":
                    parent[token] = copy.deepcopy(operation["value"])
                elif token not in parent:
                    errors.append(f"{prefix} targets a missing path")
                elif op == "replace":
                    parent[token] = copy.deepcopy(operation["value"])
                else:
                    del parent[token]

            elif isinstance(parent, list):
                if op == "add":
                    if token == "-":
                        parent.append(copy.deepcopy(operation["value"]))
                    else:
                        index = array_index(token)
                        if index is None or index > len(parent):
                            errors.append(f"{prefix} has an invalid array index")
                        else:
                            parent.insert(index, copy.deepcopy(operation["value"]))
                else:
                    index = array_index(token)
                    if index is None or index >= len(parent):
                        errors.append(f"{prefix} targets a missing array element")
                    elif op == "replace":
                        parent[index] = copy.deepcopy(operation["value"])
                    else:
                        del parent[index]
            else:
                errors.append(f"{prefix} has a non-container parent")

        return {"valid": not errors, "errors": errors}

    except Exception:
        return {"valid": False, "errors": ["input could not be validated"]}