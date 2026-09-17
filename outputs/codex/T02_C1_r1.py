def validate_upload(filename, size_bytes, content_type, config) -> dict:
    errors = []

    try:
        if not isinstance(filename, str) or not filename:
            errors.append("filename")

        if not isinstance(content_type, str) or not content_type:
            errors.append("content_type")

        if not isinstance(config, dict):
            return {"valid": False, "errors": ["filename", "extension", "content_type", "size"]}

        allowed_types = config.get("allowed_types")
        max_size_bytes = config.get("max_size_bytes")
        allow_empty_files = config.get("allow_empty_files")

        if not isinstance(allowed_types, dict):
            allowed_types = None

        extension = None
        if isinstance(filename, str) and filename:
            dot_index = filename.rfind(".")
            if dot_index > 0 and dot_index < len(filename) - 1:
                extension = filename[dot_index + 1:].lower()

        if (
            extension is None
            or allowed_types is None
            or extension not in allowed_types
        ):
            errors.append("extension")
        else:
            expected_content_type = allowed_types[extension]
            if (
                not isinstance(content_type, str)
                or not isinstance(expected_content_type, str)
                or content_type != expected_content_type
            ):
                errors.append("content_type")

        if (
            isinstance(size_bytes, bool)
            or not isinstance(size_bytes, int)
            or size_bytes < 0
        ):
            errors.append("size")
        else:
            if not isinstance(allow_empty_files, bool):
                errors.append("size")
            elif size_bytes == 0 and not allow_empty_files:
                errors.append("size")

            if (
                isinstance(max_size_bytes, bool)
                or not isinstance(max_size_bytes, int)
                or max_size_bytes < 0
                or size_bytes > max_size_bytes
            ):
                errors.append("size")

    except Exception:
        return {"valid": False, "errors": errors or ["filename", "extension", "content_type", "size"]}

    unique_errors = list(dict.fromkeys(errors))
    return {"valid": not unique_errors, "errors": unique_errors}