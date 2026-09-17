def validate_upload(filename, size_bytes, content_type, config) -> dict:
    errors = []

    try:
        if not isinstance(filename, str) or not filename:
            errors.append("filename")

        if not isinstance(config, dict):
            return {"valid": False, "errors": ["extension", "size"]}

        allowed_types = config.get("allowed_types")
        max_size_bytes = config.get("max_size_bytes")
        allow_empty_files = config.get("allow_empty_files")

        extension = None
        extension_valid = False

        if isinstance(filename, str) and filename:
            if "." in filename:
                extension = filename.rsplit(".", 1)[1].lower()
            if (
                extension
                and isinstance(allowed_types, dict)
                and extension in allowed_types
                and isinstance(allowed_types[extension], str)
            ):
                extension_valid = True

        if not extension_valid:
            errors.append("extension")

        if not isinstance(content_type, str):
            errors.append("content_type")
        elif extension_valid and content_type != allowed_types[extension]:
            errors.append("content_type")

        size_valid = (
            isinstance(size_bytes, int)
            and not isinstance(size_bytes, bool)
            and size_bytes >= 0
            and isinstance(max_size_bytes, int)
            and not isinstance(max_size_bytes, bool)
            and max_size_bytes >= 0
            and isinstance(allow_empty_files, bool)
        )

        if not size_valid:
            errors.append("size")
        elif size_bytes == 0 and not allow_empty_files:
            errors.append("size")
        elif size_bytes > max_size_bytes:
            errors.append("size")

    except Exception:
        return {"valid": False, "errors": ["filename", "extension", "content_type", "size"]}

    return {"valid": not errors, "errors": errors}