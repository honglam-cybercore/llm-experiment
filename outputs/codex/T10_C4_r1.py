import math

_MISSING = object()


def validate_patch(document, operations, protected_paths) -> dict:
    errors = []

    def is_json_value(value, active=None):
        if active is None:
            active = set()

        value_type = type(value)
        if value is None or value_type in (bool, int, str):
            return True
        if value_type is float:
            return math.isfinite(value)
        if value_type not in (list, dict):
            return False

        identity = id(value)
        if identity in active:
            return False

        active.add(identity)
        try:
            if value_type is list:
                return all(is_json_value(item, active) for item in value)
            return all(
                type(key) is str and is_json_value(item, active)
                for key, item in value.items()
            )
        finally:
            active.remove(identity)

    def clone(value, active=None):
        if active is None:
            active = set()

        value_type = type(value)
        if value is None or value_type in (bool, int, float, str):
            return value

        identity = id(value)
        if identity in active:
            raise ValueError

        active.add(identity)
        try:
            if value_type is list:
                return [clone(item, active) for item in value]
            if value_type is dict:
                return {key: clone(item, active) for key, item in value.items()}
            raise ValueError
        finally:
            active.remove(identity)

    def parse_pointer(pointer):
        if type(pointer) is not str or (pointer and not pointer.startswith("/")):
            raise ValueError

        if pointer == "":
            return []

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

                if index + 1 >= len(token) or token[index + 1] not in ("0", "1"):
                    raise ValueError
                result.append("~" if token[index + 1] == "0" else "/")
                index += 2
            tokens.append("".join(result))
        return tokens

    def is_array_index(token, allow_end=False):
        if token == "0":
            return True
        if not token or token[0] == "0" or not token.isdigit():
            return False
        return True

    def protected_conflict(path_tokens, operation, protected):
        if not protected:
            return False

        for protected_tokens in protected:
            shorter = min(len(path_tokens), len(protected_tokens))
            if path_tokens[:shorter] == protected_tokens[:shorter]:
                if (
                    len(path_tokens) <= len(protected_tokens)
                    or len(protected_tokens) <= len(path_tokens)
                ):
                    return True

        if operation == "add" and path_tokens:
            parent = path_tokens[:-1]
            token = path_tokens[-1]
            if is_array_index(token):
                try:
                    index = int(token)
                except Exception:
                    return True

                for protected_tokens in protected:
                    if (
                        len(protected_tokens) > len(parent)
                        and protected_tokens[:len(parent)] == parent
                        and is_array_index(protected_tokens[len(parent)])
                    ):
                        if index <= int(protected_tokens[len(parent)]):
                            return True

        if operation == "remove" and path_tokens:
            parent = path_tokens[:-1]
            token = path_tokens[-1]
            if is_array_index(token):
                try:
                    index = int(token)
                except Exception:
                    return True

                for protected_tokens in protected:
                    if (
                        len(protected_tokens) > len(parent)
                        and protected_tokens[:len(parent)] == parent
                        and is_array_index(protected_tokens[len(parent)])
                        and index < int(protected_tokens[len(parent)])
                    ):
                        return True

        return False

    try:
        if not is_json_value(document):
            return {"valid": False, "errors": ["document is not valid JSON data"]}

        if type(operations) is not list:
            return {"valid": False, "errors": ["operations must be a list"]}

        if type(protected_paths) is not list:
            return {"valid": False, "errors": ["protected_paths must be a list"]}

        protected = []
        for index, pointer in enumerate(protected_paths):
            try:
                protected.append(parse_pointer(pointer))
            except Exception:
                errors.append(f"protected path {index} is invalid")

        if errors:
            return {"valid": False, "errors": errors}

        current = clone(document)

        for index, operation in enumerate(operations):
            prefix = f"operation {index}"

            if type(operation) is not dict:
                errors.append(f"{prefix} must be an object")
                continue

            op = operation.get("op", _MISSING)
            path = operation.get("path", _MISSING)

            if op not in ("add", "remove", "replace"):
                errors.append(f"{prefix} has an unsupported operation")
                continue

            try:
                path_tokens = parse_pointer(path)
            except Exception:
                errors.append(f"{prefix} has an invalid path")
                continue

            if op in ("add", "replace") and "value" not in operation:
                errors.append(f"{prefix} is missing its value")
                continue

            if protected_conflict(path_tokens, op, protected):
                errors.append(f"{prefix} targets a protected path")
                continue

            value = operation.get("value", _MISSING)

            if not path_tokens:
                if op == "remove":
                    current = _MISSING
                elif op == "replace":
                    if current is _MISSING:
                        errors.append(f"{prefix} targets a missing value")
                    else:
                        current = clone(value)
                else:
                    current = clone(value)
                continue

            if current is _MISSING:
                errors.append(f"{prefix} has no valid parent")
                continue

            parent = current
            try:
                for token in path_tokens[:-1]:
                    if type(parent) is dict:
                        if token not in parent:
                            raise KeyError
                        parent = parent[token]
                    elif type(parent) is list:
                        if not is_array_index(token):
                            raise KeyError
                        child_index = int(token)
                        if child_index >= len(parent):
                            raise KeyError
                        parent = parent[child_index]
                    else:
                        raise KeyError

                token = path_tokens[-1]

                if type(parent) is dict:
                    exists = token in parent
                    if op == "add":
                        parent[token] = clone(value)
                    elif not exists:
                        errors.append(f"{prefix} targets a missing value")
                    elif op == "replace":
                        parent[token] = clone(value)
                    else:
                        del parent[token]

                elif type(parent) is list:
                    if op == "add" and token == "-":
                        parent.append(clone(value))
                    else:
                        if not is_array_index(token):
                            raise KeyError
                        target_index = int(token)

                        if op == "add":
                            if target_index > len(parent):
                                raise KeyError
                            parent.insert(target_index, clone(value))
                        elif target_index >= len(parent):
                            errors.append(f"{prefix} targets a missing value")
                        elif op == "replace":
                            parent[target_index] = clone(value)
                        else:
                            del parent[target_index]
                else:
                    raise KeyError

            except Exception:
                errors.append(f"{prefix} has an invalid parent or target")

        return {"valid": not errors, "errors": errors if errors else []}

    except Exception:
        return {"valid": False, "errors": ["input could not be validated"]}