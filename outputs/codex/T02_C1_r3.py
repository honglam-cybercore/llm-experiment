def validate_upload(filename, size_bytes, content_type, config) -> dict:
    errors = []

    try:
        if not isinstance(config, dict):
            return {
                "valid": False,
                "errors": ["filename", "extension", "content_type", "size"],
            }

        allowed_types = config.get("allowed_types")
        max_size_bytes = config.get("max_size_bytes")
        allow_empty_files = config.get("allow_empty_files")

        config_extension_error = (
            not isinstance(allowed_types, dict)
            or any(
                not isinstance(ext, str)
                or ext != ext.lower()
                or not ext
                or "." in ext
                or not isinstance(content, str)
                for ext, content in allowed_types.items()
            )
        )
        config_size_error = (
            isinstance(max_size_bytes, bool)
            or not isinstance(max_size_bytes, int)
            or max_size_bytes < 0
            or not isinstance(allow_empty_files, bool)
        )

        filename_valid = (
            isinstance(filename, str)
            and bool(filename)
            and "\x00" not in filename
            and not any(ord(char) < 32 for char in filename)
            and "/" not in filename
            and "\\" not in filename
            and filename not in (".", "..")
        )

        extension = None
        if filename_valid:
            dot_index = filename.rfind(".")
            if dot_index > 0 and dot_index < len(filename) - 1:
                extension = filename[dot_index + 1 :].lower()

        if not filename_valid:
            errors.append("filename")

        if (
            not filename_valid
            or extension is None
            or config_extension_error
            or extension not in allowed_types
        ):
            errors.append("extension")

        if not isinstance(content_type, str):
            errors.append("content_type")
        elif (
            not config_extension_error
            and extension in allowed_types
            and content_type != allowed_types[extension]
        ):
            errors.append("content_type")

        if (
            isinstance(size_bytes, bool)
            or not isinstance(size_bytes, int)
            or size_bytes < 0
            or config_size_error
            or (size_bytes == 0 and not allow_empty_files)
            or (
                not config_size_error
                and size_bytes > max_size_bytes
            )
        ):
            errors.append("size")

        return {"valid": not errors, "errors": errors}
    except Exception:
        return {
            "valid": False,
            "errors": ["filename", "extension", "content_type", "size"],
        }