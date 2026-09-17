import math


def validate_patch(document, operations, protected_paths) -> dict:
    try:
        def is_json_value(value, seen=None):
            if seen is None:
                seen = set()

            value_type = type(value)

            if value is None or value_type is bool or value_type is str:
                return True

            if value_type is int:
                return True

            if value_type is float:
                return math.isfinite(value)

            if value_type not in (list, dict):
                return False

            identity = id(value)
            if identity in seen:
                return False

            seen.add(identity)
            try:
                if value_type is list:
                    return all(is_json_value(item, seen) for item in value)

                return all(
                    type(key) is str and is_json_value(item, seen)
                    for key, item in value.items()
                )
            finally:
                seen.remove(identity)

        def clone_json(value):
            value_type = type(value)
            if value_type in (type(None), bool, int, float, str):
                return value
            if value_type is list:
                return [clone_json(item) for item in value]
            if value_type is dict:
                return {key: clone_json(item) for key, item in value.items()}
            raise ValueError

        def parse_pointer(pointer):
            if type(pointer) is not str:
                raise ValueError

            if pointer == "":
                return []

            if not pointer.startswith("/"):
                raise ValueError

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
                        raise ValueError

                    result.append("/" if token[index + 1] == "1" else "~")
                    index += 2

                tokens.append("".join(result))
            return tokens

        def is_array_index(token, allow_end=False, length=None):
            if token == "-" and allow_end:
                return length

            if not token or (len(token) > 1 and token[0] == "0"):
                raise ValueError

            if not token.isdigit():
                raise ValueError

            index = int(token)
            if length is not None and index > length:
                raise ValueError
            return index

        def prefix(left, right):
            return len(left) <= len(right) and left == right[:len(left)]

        def protected_violation(path_tokens, operation, current_document):
            for protected_tokens in protected_token_lists:
                if prefix(protected_tokens, path_tokens) or prefix(path_tokens, protected_tokens):
                    return True

                if not path_tokens or not protected_tokens:
                    continue

                if path_tokens[:-1] != protected_tokens[:-1]:
                    continue

                operation_token = path_tokens[-1]
                protected_token = protected_tokens[-1]

                try:
                    protected_index = int(protected_token)
                    if str(protected_index) != protected_token:
                        continue
                except Exception:
                    continue

                if operation in ("add", "remove"):
                    if operation_token == "-":
                        continue
                    try:
                        operation_index = int(operation_token)
                        if str(operation_index) != operation_token:
                            continue
                    except Exception:
                        continue

                    if operation == "add" and operation_index <= protected_index:
                        return True
                    if operation == "remove" and operation_index < protected_index:
                        return True

            return False

        def resolve_parent(root, tokens):
            current = root
            for token in tokens:
                if type(current) is dict:
                    if token not in current:
                        raise KeyError
                    current = current[token]
                elif type(current) is list:
                    index = is_array_index(token, allow_end=False, length=len(current))
                    current = current[index]
                else:
                    raise KeyError
            return current

        def apply_operation(root, operation, path_tokens):
            op = operation["op"]

            if not path_tokens:
                if op == "remove":
                    return missing
                return clone_json(operation["value"])

            parent = resolve_parent(root, path_tokens[:-1])
            token = path_tokens[-1]

            if type(parent) is dict:
                if op == "add":
                    parent[token] = clone_json(operation["value"])
                elif op == "replace":
                    if token not in parent:
                        raise KeyError
                    parent[token] = clone_json(operation["value"])
                else:
                    if token not in parent:
                        raise KeyError
                    del parent[token]
                return root

            if type(parent) is list:
                if op == "add":
                    index = is_array_index(token, allow_end=True, length=len(parent))
                    if index == len(parent):
                        parent.append(clone_json(operation["value"]))
                    else:
                        parent.insert(index, clone_json(operation["value"]))
                elif op == "replace":
                    index = is_array_index(token, allow_end=False, length=len(parent) - 1)
                    parent[index] = clone_json(operation["value"])
                else:
                    index = is_array_index(token, allow_end=False, length=len(parent) - 1)
                    del parent[index]
                return root

            raise KeyError

        if not is_json_value(document):
            return {"valid": False, "errors": ["invalid document"]}

        if type(operations) is not list:
            return {"valid": False, "errors": ["invalid operations"]}

        if type(protected_paths) is not list:
            return {"valid": False, "errors": ["invalid protected paths"]}

        protected_token_lists = []
        for protected_path in protected_paths:
            try:
                protected_token_lists.append(parse_pointer(protected_path))
            except Exception:
                return {"valid": False, "errors": ["invalid protected path"]}

        for operation in operations:
            if type(operation) is not dict:
                return {"valid": False, "errors": ["invalid operation"]}

            if type(operation.get("op")) is not str:
                return {"valid": False, "errors": ["invalid operation"]}

            op = operation["op"]
            if op not in ("add", "remove", "replace"):
                return {"valid": False, "errors": ["unsupported operation"]}

            if type(operation.get("path")) is not str:
                return {"valid": False, "errors": ["invalid path"]}

            try:
                path_tokens = parse_pointer(operation["path"])
            except Exception:
                return {"valid": False, "errors": ["invalid path"]}

            if op in ("add", "replace"):
                if "value" not in operation or not is_json_value(operation["value"]):
                    return {"valid": False, "errors": ["invalid value"]}

            if protected_violation(path_tokens, op, document):
                return {"valid": False, "errors": ["protected path"]}

            if "current_document" not in locals():
                current_document = clone_json(document)

            if current_document is missing:
                if not (op == "add" and not path_tokens):
                    return {"valid": False, "errors": ["invalid operation sequence"]}
            else:
                try:
                    current_document = apply_operation(
                        current_document, operation, path_tokens
                    )
                except Exception:
                    return {"valid": False, "errors": ["invalid path or document structure"]}

        return {"valid": True, "errors": []}

    except Exception:
        return {"valid": False, "errors": ["invalid input"]}