def validate_upload(filename, size_bytes, content_type, config) -> dict:
    errors = []

    try:
        if type(filename) is not str or not filename:
            errors.append("filename")
            filename_valid = False
        else:
            filename_valid = True
            if (
                "\x00" in filename
                or any(ord(char) < 32 or ord(char) == 127 for char in filename)
                or "/" in filename
                or "\\" in filename
            ):
                errors.append("filename")
                filename_valid = False

            parts = filename.replace("\\", "/").split("/")
            if any(part in ("", ".", "..") for part in parts):
                errors.append("filename")
                filename_valid = False

        extension = ""
        if filename_valid:
            basename = filename.rsplit("/", 1)[-1]
            if "." not in basename or basename.startswith(".") or basename.endswith("."):
                errors.append("extension")
            else:
                extension = basename.rsplit(".", 1)[1].lower()
                if not extension or not extension.isalnum():
                    errors.append("extension")

        if type(config) is not dict:
            config = {}
            errors.extend(["extension", "size"])
            allowed_types = {}
            max_size = None
            allow_empty = None
        else:
            allowed_types = config.get("allowed_types")
            max_size = config.get("max_size_bytes")
            allow_empty = config.get("allow_empty_files")

            if type(allowed_types) is not dict:
                errors.append("extension")
                allowed_types = {}

            if type(max_size) is not int or isinstance(max_size, bool) or max_size < 0:
                errors.append("size")
                max_size = None

            if type(allow_empty) is not bool:
                errors.append("size")
                allow_empty = None

        normalized_types = {}
        if type(allowed_types) is dict:
            for key, value in allowed_types.items():
                if (
                    type(key) is not str
                    or type(value) is not str
                    or not key
                    or key != key.lower()
                    or "." in key
                    or not key.isalnum()
                    or not value
                    or any(ord(char) < 32 or ord(char) == 127 for char in value)
                ):
                    errors.append("extension")
                    continue
                normalized_types[key] = value

        expected_content_type = normalized_types.get(extension)
        if filename_valid and extension:
            if expected_content_type is None:
                errors.append("extension")

        if (
            type(content_type) is not str
            or not content_type
            or "\x00" in content_type
            or any(ord(char) < 32 or ord(char) == 127 for char in content_type)
            or expected_content_type is None
            or content_type != expected_content_type
        ):
            errors.append("content_type")

        if (
            type(size_bytes) is not int
            or isinstance(size_bytes, bool)
            or size_bytes < 0
            or max_size is None
            or allow_empty is None
            or size_bytes > max_size
            or (size_bytes == 0 and not allow_empty)
        ):
            errors.append("size")

    except Exception:
        return {"valid": False, "errors": ["filename", "extension", "content_type", "size"]}

    unique_errors = []
    for error in errors:
        if error not in unique_errors:
            unique_errors.append(error)

    return {"valid": not unique_errors, "errors": unique_errors}