import math


_MISSING = object()


def validate_patch(document, operations, protected_paths) -> dict:
    errors = []

    def error(message):
        errors.append(message)

    def clone_json(value, seen=None):
        if seen is None:
            seen = set()

        if value is None or isinstance(value, (str, bool, int)):
            return value

        if isinstance(value, float):
            if not math.isfinite(value):
                raise ValueError
            return value

        if isinstance(value, list):
            identity = id(value)
            if identity in seen:
                raise ValueError
            seen.add(identity)
            result = [clone_json(item, seen) for item in value]
            seen.remove(identity)
            return result

        if isinstance(value, dict):
            identity = id(value)
            if identity in seen:
                raise ValueError
            seen.add(identity)
            result = {}
            for key, item in value.items():
                if not isinstance(key, str):
                    raise ValueError
                result[key] = clone_json(item, seen)
            seen.remove(identity)
            return result

        raise ValueError

    def parse_pointer(pointer):
        if not isinstance(pointer, str):
            raise ValueError
        if pointer == "":
            return ()
        if not pointer.startswith("/"):
            raise ValueError

        tokens = []
        for raw in pointer[1:].split("/"):
            decoded = []
            i = 0
            while i < len(raw):
                char = raw[i]
                if char == "~":
                    if i + 1 >= len(raw) or raw[i + 1] not in ("0", "1"):
                        raise ValueError
                    decoded.append("~" if raw[i + 1] == "0" else "/")
                    i += 2
                else:
                    decoded.append(char)
                    i += 1
            tokens.append("".join(decoded))
        return tuple(tokens)

    def valid_json_number(value):
        return not isinstance(value, float) or math.isfinite(value)

    def array_index(token, upper_bound, allow_end=False):
        if not isinstance(token, str) or not token:
            return None
        if token == "0":
            return 0
        if token[0] == "0" or not token.isdigit():
            return None

        limit = upper_bound if allow_end else upper_bound - 1
        if limit < 0:
            return None
        if len(token) > len(str(limit)):
            return None
        try:
            index = int(token)
        except Exception:
            return None
        return index if 0 <= index <= limit else None

    def get_value(root, tokens):
        current = root
        for token in tokens:
            if isinstance(current, dict):
                if token not in current:
                    return _MISSING
                current = current[token]
            elif isinstance(current, list):
                index = array_index(token, len(current))
                if index is None:
                    return _MISSING
                current = current[index]
            else:
                return _MISSING
        return current

    def get_parent(root, tokens):
        if not tokens:
            return _MISSING, None
        parent = get_value(root, tokens[:-1])
        if parent is _MISSING:
            return _MISSING, None
        return parent, tokens[-1]

    def protected(tokens):
        for protected_tokens in protected_token_paths:
            shorter = min(len(tokens), len(protected_tokens))
            if tokens[:shorter] == protected_tokens[:shorter]:
                return True
        return False

    try:
        state = clone_json(document)

        if not isinstance(operations, list):
            return {"valid": False, "errors": ["operations must be a list"]}

        if not isinstance(protected_paths, list):
            return {"valid": False, "errors": ["protected_paths must be a list"]}

        protected_token_paths = []
        for path in protected_paths:
            try:
                protected_token_paths.append(parse_pointer(path))
            except Exception:
                error("invalid protected path")

        if errors:
            return {"valid": False, "errors": errors}

        for position, operation in enumerate(operations):
            if not isinstance(operation, dict):
                error("operation %d must be an object" % position)
                continue

            op = operation.get("op")
            path = operation.get("path")

            if op not in ("add", "remove", "replace"):
                error("operation %d has an invalid op" % position)
                continue

            try:
                tokens = parse_pointer(path)
            except Exception:
                error("operation %d has an invalid path" % position)
                continue

            if op in ("add", "replace") and "value" not in operation:
                error("operation %d is missing value" % position)
                continue

            value = None
            if op in ("add", "replace"):
                try:
                    value = clone_json(operation["value"])
                except Exception:
                    error("operation %d has an invalid value" % position)
                    continue

            if protected(tokens):
                error("operation %d targets a protected path" % position)
                continue

            if op == "add":
                if not tokens:
                    state = value
                    continue

                parent, token = get_parent(state, tokens)
                if parent is _MISSING:
                    error("operation %d has a missing parent" % position)
                elif isinstance(parent, dict):
                    parent[token] = value
                elif isinstance(parent, list):
                    if token == "-":
                        parent.append(value)
                    else:
                        index = array_index(token, len(parent), allow_end=True)
                        if index is None:
                            error("operation %d has an invalid array index" % position)
                        else:
                            parent.insert(index, value)
                else:
                    error("operation %d has an invalid parent" % position)

            elif op == "replace":
                if not tokens:
                    state = value
                    continue

                parent, token = get_parent(state, tokens)
                if parent is _MISSING:
                    error("operation %d targets a missing path" % position)
                elif isinstance(parent, dict):
                    if token not in parent:
                        error("operation %d targets a missing path" % position)
                    else:
                        parent[token] = value
                elif isinstance(parent, list):
                    index = array_index(token, len(parent))
                    if index is None:
                        error("operation %d targets a missing path" % position)
                    else:
                        parent[index] = value
                else:
                    error("operation %d has an invalid parent" % position)

            else:
                if not tokens:
                    state = _MISSING
                    continue

                parent, token = get_parent(state, tokens)
                if parent is _MISSING:
                    error("operation %d targets a missing path" % position)
                elif isinstance(parent, dict):
                    if token not in parent:
                        error("operation %d targets a missing path" % position)
                    else:
                        del parent[token]
                elif isinstance(parent, list):
                    index = array_index(token, len(parent))
                    if index is None:
                        error("operation %d targets a missing path" % position)
                    else:
                        del parent[index]
                else:
                    error("operation %d has an invalid parent" % position)

        return {"valid": not errors, "errors": errors}

    except Exception:
        return {"valid": False, "errors": ["input cannot be validated"]}