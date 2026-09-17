import copy
import math


def validate_patch(document, operations, protected_paths) -> dict:
    errors = []

    def invalid(message):
        errors.append(message)
        return {"valid": False, "errors": errors}

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

        if value_type not in (dict, list):
            return False

        object_id = id(value)
        if object_id in seen:
            return False
        seen.add(object_id)

        try:
            if value_type is dict:
                for key, item in value.items():
                    if type(key) is not str or not is_json_value(item, seen):
                        return False
            else:
                for item in value:
                    if not is_json_value(item, seen):
                        return False
            return True
        finally:
            seen.remove(object_id)

    def decode_pointer(pointer):
        if type(pointer) is not str:
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

    def is_prefix(prefix, path):
        return len(prefix) <= len(path) and path[:len(prefix)] == prefix

    def parse_array_index(token, length, allow_end=False):
        if token == "0":
            index = 0
        elif token and token[0] != "0" and token.isdigit():
            if len(token) > 1000:
                return None
            try:
                index = int(token)
            except BaseException:
                return None
        else:
            return None

        upper_bound = length if allow_end else length - 1
        if index < 0 or index > upper_bound:
            return None
        return index

    try:
        if not is_json_value(document):
            return invalid("document is not valid JSON data")

        if type(operations) is not list:
            return invalid("operations must be a list")

        if type(protected_paths) is not list:
            return invalid("protected_paths must be a list")

        protected = []
        for pointer in protected_paths:
            decoded = decode_pointer(pointer)
            if decoded is None:
                return invalid("protected_paths contains an invalid JSON Pointer")
            protected.append(decoded)

        current = copy.deepcopy(document)
        missing = object()

        for operation_number, operation in enumerate(operations):
            if type(operation) is not dict:
                return invalid(f"operation {operation_number} is malformed")

            op = operation.get("op")
            path_pointer = operation.get("path")

            if op not in ("add", "remove", "replace"):
                return invalid(f"operation {operation_number} has an unsupported operation")

            path = decode_pointer(path_pointer)
            if path is None:
                return invalid(f"operation {operation_number} has an invalid JSON Pointer")

            if op in ("add", "replace") and "value" not in operation:
                return invalid(f"operation {operation_number} is missing a value")

            if op in ("add", "replace") and not is_json_value(operation["value"]):
                return invalid(f"operation {operation_number} has an invalid value")

            if any(is_prefix(protected_path, path) for protected_path in protected):
                return invalid(f"operation {operation_number} targets a protected path")

            if op in ("remove", "replace") and any(
                is_prefix(path, protected_path) for protected_path in protected
            ):
                return invalid(f"operation {operation_number} affects a protected path")

            if path == ():
                if op == "remove":
                    if current is missing:
                        return invalid(f"operation {operation_number} references a missing value")
                    current = missing
                else:
                    current = copy.deepcopy(operation["value"])
                continue

            if current is missing:
                return invalid(f"operation {operation_number} has a missing parent")

            parent = current
            for token in path[:-1]:
                if type(parent) is dict:
                    if token not in parent:
                        parent = missing
                        break
                    parent = parent[token]
                elif type(parent) is list:
                    index = parse_array_index(token, len(parent))
                    if index is None:
                        parent = missing
                        break
                    parent = parent[index]
                else:
                    parent = missing
                    break

            if parent is missing or type(parent) not in (dict, list):
                return invalid(f"operation {operation_number} has an invalid parent path")

            token = path[-1]

            if type(parent) is dict:
                exists = token in parent

                if op in ("remove", "replace") and not exists:
                    return invalid(f"operation {operation_number} references a missing value")

                if op == "add":
                    parent[token] = copy.deepcopy(operation["value"])
                elif op == "replace":
                    parent[token] = copy.deepcopy(operation["value"])
                else:
                    del parent[token]

            else:
                if op == "add":
                    if token == "-":
                        index = len(parent)
                    else:
                        index = parse_array_index(token, len(parent), allow_end=True)
                        if index is None:
                            return invalid(f"operation {operation_number} has an invalid array index")

                    for protected_path in protected:
                        if (
                            len(protected_path) > len(path)
                            and protected_path[:len(path)] == path
                        ):
                            protected_index_token = protected_path[len(path)]
                            protected_index = parse_array_index(
                                protected_index_token, len(parent)
                            )
                            if protected_index is not None and index <= protected_index:
                                return invalid(
                                    f"operation {operation_number} affects a protected path"
                                )

                    parent.insert(index, copy.deepcopy(operation["value"]))

                else:
                    index = parse_array_index(token, len(parent))
                    if index is None:
                        return invalid(f"operation {operation_number} references a missing value")

                    if op == "remove":
                        for protected_path in protected:
                            if (
                                len(protected_path) > len(path)
                                and protected_path[:len(path)] == path
                            ):
                                protected_index_token = protected_path[len(path)]
                                protected_index = parse_array_index(
                                    protected_index_token, len(parent)
                                )
                                if protected_index is not None and index <= protected_index:
                                    return invalid(
                                        f"operation {operation_number} affects a protected path"
                                    )
                        del parent[index]
                    else:
                        parent[index] = copy.deepcopy(operation["value"])

        return {"valid": True, "errors": []}

    except BaseException:
        return {"valid": False, "errors": ["input could not be validated"]}