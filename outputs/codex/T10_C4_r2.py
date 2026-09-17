import math


_MISSING = object()


def validate_patch(document, operations, protected_paths) -> dict:
    errors = []

    def clone_json(value, seen=None):
        if seen is None:
            seen = set()

        value_type = type(value)

        if value is None or value_type is bool or value_type is str:
            return value

        if value_type is int:
            return value

        if value_type is float:
            if not math.isfinite(value):
                raise ValueError
            return value

        if value_type in (list, dict):
            value_id = id(value)
            if value_id in seen:
                raise ValueError

            seen.add(value_id)
            try:
                if value_type is list:
                    return [clone_json(item, seen) for item in value]

                result = {}
                for key, item in value.items():
                    if type(key) is not str:
                        raise ValueError
                    result[key] = clone_json(item, seen)
                return result
            finally:
                seen.remove(value_id)

        raise ValueError

    def parse_pointer(pointer):
        if type(pointer) is not str:
            raise ValueError

        if pointer == "":
            return ()

        if not pointer.startswith("/"):
            raise ValueError

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
                    raise ValueError

                decoded.append("~" if token[index + 1] == "0" else "/")
                index += 2

            tokens.append("".join(decoded))

        return tuple(tokens)

    def array_index(token, allow_end=False, length=0):
        if token == "-" and allow_end:
            return length

        if token == "" or (len(token) > 1 and token[0] == "0"):
            raise ValueError

        if not token.isdigit():
            raise ValueError

        index = int(token)
        if index < 0 or index > length or (not allow_end and index == length):
            raise ValueError

        return index

    def get_value(root, tokens):
        current = root

        for token in tokens:
            if current is _MISSING:
                raise KeyError

            if type(current) is dict:
                if token not in current:
                    raise KeyError
                current = current[token]
            elif type(current) is list:
                index = array_index(token, allow_end=False, length=len(current))
                current = current[index]
            else:
                raise KeyError

        return current

    def is_protected(path, protected):
        for protected_path in protected:
            if (
                path[:len(protected_path)] == protected_path
                or protected_path[:len(path)] == path
            ):
                return True
        return False

    try:
        try:
            current = clone_json(document)
        except Exception:
            return {"valid": False, "errors": ["Invalid document"]}

        if type(operations) is not list:
            return {"valid": False, "errors": ["Operations must be a list"]}

        if type(protected_paths) is not list:
            return {"valid": False, "errors": ["Protected paths must be a list"]}

        parsed_protected = []
        for protected_path in protected_paths:
            try:
                parsed_protected.append(parse_pointer(protected_path))
            except Exception:
                errors.append("Invalid protected path")

        if errors:
            return {"valid": False, "errors": errors}

        for operation in operations:
            if type(operation) is not dict:
                errors.append("Malformed operation")
                continue

            op = operation.get("op")
            path = operation.get("path")

            if type(op) is not str or op not in ("add", "remove", "replace"):
                errors.append("Unsupported operation")
                continue

            try:
                tokens = parse_pointer(path)
            except Exception:
                errors.append("Invalid path")
                continue

            if is_protected(tokens, parsed_protected):
                errors.append("Protected path")
                continue

            if op in ("add", "replace") and "value" not in operation:
                errors.append("Missing value")
                continue

            if op == "add":
                try:
                    new_value = clone_json(operation["value"])

                    if not tokens:
                        current = new_value
                        continue

                    parent = get_value(current, tokens[:-1])
                    final_token = tokens[-1]

                    if type(parent) is dict:
                        parent[final_token] = new_value
                    elif type(parent) is list:
                        index = array_index(
                            final_token,
                            allow_end=True,
                            length=len(parent),
                        )
                        parent.insert(index, new_value)
                    else:
                        raise KeyError
                except Exception:
                    errors.append("Invalid add path")
                continue

            if op == "replace":
                try:
                    new_value = clone_json(operation["value"])

                    if not tokens:
                        if current is _MISSING:
                            raise KeyError
                        current = new_value
                        continue

                    parent = get_value(current, tokens[:-1])
                    final_token = tokens[-1]

                    if type(parent) is dict:
                        if final_token not in parent:
                            raise KeyError
                        parent[final_token] = new_value
                    elif type(parent) is list:
                        index = array_index(
                            final_token,
                            allow_end=False,
                            length=len(parent),
                        )
                        parent[index] = new_value
                    else:
                        raise KeyError
                except Exception:
                    errors.append("Invalid replace path")
                continue

            try:
                if not tokens:
                    if current is _MISSING:
                        raise KeyError
                    current = _MISSING
                    continue

                parent = get_value(current, tokens[:-1])
                final_token = tokens[-1]

                if type(parent) is dict:
                    if final_token not in parent:
                        raise KeyError
                    del parent[final_token]
                elif type(parent) is list:
                    index = array_index(
                        final_token,
                        allow_end=False,
                        length=len(parent),
                    )
                    del parent[index]
                else:
                    raise KeyError
            except Exception:
                errors.append("Invalid remove path")

        return {"valid": not errors, "errors": errors}
    except Exception:
        return {"valid": False, "errors": ["Invalid input"]}