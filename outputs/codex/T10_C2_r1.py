def validate_patch(document, operations, protected_paths) -> dict:
    errors = []

    def fail(message):
        errors.append(message)
        return False

    def clone_json(value, active=None):
        if active is None:
            active = set()

        if value is None or isinstance(value, (str, bool, int)):
            return value

        if isinstance(value, float):
            import math
            if not math.isfinite(value):
                raise ValueError("non-finite number")
            return value

        if isinstance(value, list):
            identity = id(value)
            if identity in active:
                raise ValueError("cyclic structure")
            active.add(identity)
            try:
                return [clone_json(item, active) for item in value]
            finally:
                active.remove(identity)

        if isinstance(value, dict):
            identity = id(value)
            if identity in active:
                raise ValueError("cyclic structure")
            active.add(identity)
            try:
                result = {}
                for key, item in value.items():
                    if not isinstance(key, str):
                        raise ValueError("non-string object key")
                    result[key] = clone_json(item, active)
                return result
            finally:
                active.remove(identity)

        raise ValueError("non-JSON value")

    def parse_pointer(pointer):
        if not isinstance(pointer, str):
            raise ValueError("pointer must be a string")
        if pointer == "":
            return []
        if not pointer.startswith("/"):
            raise ValueError("pointer must start with '/'")

        tokens = []
        for raw in pointer[1:].split("/"):
            decoded = []
            index = 0
            while index < len(raw):
                char = raw[index]
                if char == "~":
                    if index + 1 >= len(raw) or raw[index + 1] not in ("0", "1"):
                        raise ValueError("invalid pointer escape")
                    decoded.append("~" if raw[index + 1] == "0" else "/")
                    index += 2
                else:
                    decoded.append(char)
                    index += 1
            tokens.append("".join(decoded))
        return tokens

    def array_index(token, allow_end=False):
        if allow_end and token == "-":
            return None
        if token == "0":
            return 0
        if not token or token[0] == "0" or any(c < "0" or c > "9" for c in token):
            raise ValueError("invalid array index")
        index = int(token)
        return index

    def get_existing(root, tokens):
        current = root
        for token in tokens:
            if isinstance(current, dict):
                if token not in current:
                    raise KeyError("missing path")
                current = current[token]
            elif isinstance(current, list):
                index = array_index(token)
                if index >= len(current):
                    raise KeyError("missing path")
                current = current[index]
            else:
                raise KeyError("non-container parent")
        return current

    def protected_conflict(path_tokens, protected_token_lists):
        for protected in protected_token_lists:
            if (
                path_tokens[:len(protected)] == protected
                or protected[:len(path_tokens)] == path_tokens
            ):
                return True
        return False

    try:
        if not isinstance(operations, list):
            return {"valid": False, "errors": ["operations must be a list"]}
        if not isinstance(protected_paths, list):
            return {"valid": False, "errors": ["protected_paths must be a list"]}

        current = clone_json(document)

        protected_tokens = []
        for pointer in protected_paths:
            try:
                protected_tokens.append(parse_pointer(pointer))
            except Exception as exc:
                return {"valid": False, "errors": [f"invalid protected path: {exc}"]}

        for number, operation in enumerate(operations):
            if not isinstance(operation, dict):
                return {
                    "valid": False,
                    "errors": [f"operation {number} must be an object"],
                }

            op = operation.get("op")
            pointer = operation.get("path")

            if op not in ("add", "remove", "replace"):
                return {
                    "valid": False,
                    "errors": [f"operation {number} has an unsupported op"],
                }

            try:
                tokens = parse_pointer(pointer)
            except Exception as exc:
                return {
                    "valid": False,
                    "errors": [f"operation {number} has an invalid path: {exc}"],
                }

            if protected_conflict(tokens, protected_tokens):
                return {
                    "valid": False,
                    "errors": [f"operation {number} targets a protected path"],
                }

            if op in ("add", "replace") and "value" not in operation:
                return {
                    "valid": False,
                    "errors": [f"operation {number} is missing value"],
                }

            if op == "add":
                value = clone_json(operation["value"])

                if not tokens:
                    current = value
                    continue

                parent = get_existing(current, tokens[:-1])
                final_token = tokens[-1]

                if isinstance(parent, dict):
                    parent[final_token] = value
                elif isinstance(parent, list):
                    if final_token == "-":
                        parent.append(value)
                    else:
                        index = array_index(final_token, allow_end=True)
                        if index is None or index > len(parent):
                            raise IndexError("array index out of range")
                        parent.insert(index, value)
                else:
                    raise TypeError("parent is not a container")

            elif op == "remove":
                if not tokens:
                    get_existing(current, [])
                    current = None
                    continue

                parent = get_existing(current, tokens[:-1])
                final_token = tokens[-1]

                if isinstance(parent, dict):
                    if final_token not in parent:
                        raise KeyError("missing path")
                    del parent[final_token]
                elif isinstance(parent, list):
                    index = array_index(final_token)
                    if index >= len(parent):
                        raise KeyError("missing path")
                    del parent[index]
                else:
                    raise TypeError("parent is not a container")

            else:
                value = clone_json(operation["value"])

                if not tokens:
                    get_existing(current, [])
                    current = value
                    continue

                parent = get_existing(current, tokens[:-1])
                final_token = tokens[-1]

                if isinstance(parent, dict):
                    if final_token not in parent:
                        raise KeyError("missing path")
                    parent[final_token] = value
                elif isinstance(parent, list):
                    index = array_index(final_token)
                    if index >= len(parent):
                        raise KeyError("missing path")
                    parent[index] = value
                else:
                    raise TypeError("parent is not a container")

        return {"valid": True, "errors": []}

    except Exception as exc:
        return {"valid": False, "errors": [f"invalid patch: {exc}"]}