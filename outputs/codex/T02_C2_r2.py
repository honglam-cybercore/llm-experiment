def validate_upload(filename, size_bytes, content_type, config) -> dict:
    errors = []

    if not isinstance(filename, str) or not filename:
        errors.append("filename")
    elif (
        any(ord(char) < 32 or ord(char) == 127 for char in filename)
        or "/" in filename
        or "\\" in filename
        or ":" in filename
        or filename in {".", ".."}
        or any(part in {".", ".."} for part in filename.replace("\\", "/").split("/"))
    ):
        errors.append("filename")

    allowed_types = None
    max_size_bytes = None
    allow_empty_files = None

    if not isinstance(config, dict):
        errors.extend(["extension", "content_type", "size"])
    else:
        allowed = config.get("allowed_types")
        maximum = config.get("max_size_bytes")
        allow_empty = config.get("allow_empty_files")

        if (
            not isinstance(allowed, dict)
            or any(
                not isinstance(ext, str)
                or not ext
                or ext.startswith(".")
                or not isinstance(mime, str)
                or not mime
                for ext, mime in allowed.items()
            )
        ):
            errors.extend(["extension", "content_type"])
        else:
            allowed_types = {
                ext.lower(): mime
                for ext, mime in allowed.items()
            }

        if isinstance(maximum, bool) or not isinstance(maximum, int) or maximum < 0:
            errors.append("size")
        else:
            max_size_bytes = maximum

        if not isinstance(allow_empty, bool):
            errors.append("size")
        else:
            allow_empty_files = allow_empty

    extension = None
    if "filename" not in errors:
        dot_index = filename.rfind(".")
        if dot_index <= 0 or dot_index == len(filename) - 1:
            errors.append("extension")
        else:
            extension = filename[dot_index + 1:].lower()
            if not extension or allowed_types is None or extension not in allowed_types:
                errors.append("extension")

    if not isinstance(content_type, str) or not content_type:
        errors.append("content_type")
    elif any(ord(char) < 32 or ord(char) == 127 for char in content_type):
        errors.append("content_type")
    elif extension is not None and allowed_types is not None:
        if allowed_types.get(extension) != content_type:
            errors.append("content_type")

    if (
        isinstance(size_bytes, bool)
        or not isinstance(size_bytes, int)
        or size_bytes < 0
        or (
            isinstance(size_bytes, int)
            and max_size_bytes is not None
            and size_bytes > max_size_bytes
        )
        or (
            isinstance(size_bytes, int)
            and size_bytes == 0
            and allow_empty_files is False
        )
    ):
        errors.append("size")

    unique_errors = list(dict.fromkeys(errors))
    return {"valid": not unique_errors, "errors": unique_errors}