import copy
import math


def validate_patch(document, operations, protected_paths) -> dict:
    def result(valid, errors=None):
        return {"valid": valid, "errors": errors or []}

    def is_json_like(value, seen=None):
        if seen is None:
            seen = set()

        value_type = type(value)

        if value is None or value_type is bool or value_type is int or value_type is str:
            return True

        if value_type is float:
            return math.isfinite(value)

        if value_type is list:
            identity = id(value)
            if identity in seen:
                return False
            seen.add(identity)
            try:
                return all(is_json_like(item, seen) for item in value)
            finally:
                seen.remove(identity)

        if value_type is dict:
            identity = id(value)
            if identity in seen:
                return False
            seen.add(identity)
            try:
                return all(
                    type(key) is str and is_json_like(item, seen)
                    for key, item in value.items()
                )
            finally:
                seen.remove(identity)

        return False

    def parse_pointer(pointer):
        if type(pointer) is not str:
            raise ValueError("path must be a string")
        if pointer == "":
            return ()
        if not pointer.startswith("/"):
            raise ValueError("invalid JSON Pointer")
        tokens = []
        for token in pointer[1:].split("/"):
            decoded = []
            index = 0
            while index < len(token):
                if token[index] != "~":
                    decoded.append(token[index])
                    index += 1
                    continue
                if index + 1 >= len(token) or token[index + 1] not in "01":
                    raise ValueError("invalid JSON Pointer escape")
                decoded.append("/" if token[index + 1] == "1" else "~")
                index += 2
            tokens.append("".join(decoded))
        return tuple(tokens)

    def array_index(token, length, allow_end=False):
        if token == "-" or token == "":
            raise ValueError("invalid array index")
        if len(token) > 1 and token[0] == "0":
            raise ValueError("invalid array index")
        if not token.isdigit():
            raise ValueError("invalid array index")
        index = int(token)
        if index > length or (not allow_end and index >= length):
            raise ValueError("array index out of range")
        return index

    def protected(path, protected_tuples):
        for protected_path in protected_tuples:
            if (
                len(path) >= len(protected_path)
                and path[:len(protected_path)] == protected_path
            ):
                return True
            if (
                len(path) < len(protected_path)
                and protected_path[:len(path)] == path
            ):
                return True
        return False

    try:
        if not is_json_like(document):
            return result(False, ["document is not valid JSON-like data"])

        if type(operations) is not list:
            return result(False, ["operations must be a list"])

        if type(protected_paths) is not list:
            return result(False, ["protected_paths must be a list"])

        protected_tuples = []
        for pointer in protected_paths:
            try:
                protected_tuples.append(parse_pointer(pointer))
            except Exception as exc:
                return result(False, [f"invalid protected path: {exc}"])

        working = copy.deepcopy(document)

        for operation_number, operation in enumerate(operations):
            if type(operation) is not dict:
                return result(False, [f"operation {operation_number} must be an object"])

            op = operation.get("op")
            path_value = operation.get("path")

            if op not in ("add", "remove", "replace"):
                return result(False, [f"operation {operation_number} has an invalid op"])

            try:
                path = parse_pointer(path_value)
            except Exception as exc:
                return result(False, [f"operation {operation_number}: {exc}"])

            if op in ("add", "replace") and "value" not in operation:
                return result(False, [f"operation {operation_number} is missing value"])

            if op in ("add", "replace") and not is_json_like(operation["value"]):
                return result(False, [f"operation {operation_number} has an invalid value"])

            if protected(path, protected_tuples):
                return result(False, [f"operation {operation_number} targets a protected path"])

            if not path:
                if op == "remove":
                    return result(False, [f"operation {operation_number} cannot remove the document"])
                working = copy.deepcopy(operation["value"])
                continue

            parent_path = path[:-1]
            token = path[-1]
            parent = working

            try:
                for part in parent_path:
                    if type(parent) is dict:
                        if part not in parent:
                            raise ValueError("path does not exist")
                        parent = parent[part]
                    elif type(parent) is list:
                        index = array_index(part, len(parent))
                        parent = parent[index]
                    else:
                        raise ValueError("path traverses a scalar")

                if type(parent) is dict:
                    if op == "replace" and token not in parent:
                        raise ValueError("path does not exist")
                    if op == "remove" and token not in parent:
                        raise ValueError("path does not exist")

                    if op == "remove":
                        del parent[token]
                    else:
                        parent[token] = copy.deepcopy(operation["value"])

                elif type(parent) is list:
                    if op == "add":
                        if token == "-":
                            parent.append(copy.deepcopy(operation["value"]))
                        else:
                            index = array_index(token, len(parent), allow_end=True)
                            parent.insert(index, copy.deepcopy(operation["value"]))
                    else:
                        index = array_index(token, len(parent))
                        if op == "remove":
                            del parent[index]
                        else:
                            parent[index] = copy.deepcopy(operation["value"])
                else:
                    raise ValueError("path parent is not a container")

            except Exception as exc:
                return result(False, [f"operation {operation_number}: {exc}"])

        return result(True)

    except Exception as exc:
        return result(False, [f"unable to validate patch: {exc}"])