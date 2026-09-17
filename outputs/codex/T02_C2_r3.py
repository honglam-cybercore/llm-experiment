def validate_upload(filename, size_bytes, content_type, config) -> dict:
    errors = []

    try:
        if not isinstance(config, dict):
            return {"valid": False, "errors": ["extension", "size"]}

        allowed_types = config.get("allowed_types")
        max_size_bytes = config.get("max_size_bytes")
        allow_empty_files = config.get("allow_empty_files")

        config_types_valid = isinstance(allowed_types, dict)
        if config_types_valid:
            for extension, allowed_content_type in allowed_types.items():
                if (
                    not isinstance(extension, str)
                    or not extension
                    or extension != extension.lower()
                    or extension.startswith(".")
                    or not extension.isalnum()
                    or not isinstance(allowed_content_type, str)
                    or not allowed_content_type
                ):
                    config_types_valid = False
                    break

        if not isinstance(max_size_bytes, int) or isinstance(max_size_bytes, bool):
            max_size_valid = False
        else:
            max_size_valid = max_size_bytes >= 0

        if not isinstance(allow_empty_files, bool):
            allow_empty_valid = False
        else:
            allow_empty_valid = True

        filename_valid = (
            isinstance(filename, str)
            and bool(filename)
            and filename not in (".", "..")
            and not any(
                character in filename or ord(character) < 32 or ord(character) == 127
                for character in ("/", "\\", ":")
            )
            and not filename.isspace()
        )

        if not filename_valid:
            errors.append("filename")

        extension = None
        if filename_valid:
            dot_position = filename.rfind(".")
            if dot_position <= 0 or dot_position == len(filename) - 1:
                errors.append("extension")
            else:
                extension = filename[dot_position + 1:].lower()
                if (
                    not config_types_valid
                    or extension not in allowed_types
                ):
                    errors.append("extension")
        else:
            errors.append("extension")

        content_type_valid = (
            isinstance(content_type, str)
            and bool(content_type)
            and not any(ord(character) < 32 or ord(character) == 127 for character in content_type)
        )

        if (
            not content_type_valid
            or not config_types_valid
            or extension is None
            or extension not in allowed_types
            or content_type != allowed_types[extension]
        ):
            errors.append("content_type")

        size_valid = (
            isinstance(size_bytes, int)
            and not isinstance(size_bytes, bool)
            and size_bytes >= 0
            and max_size_valid
            and size_bytes <= max_size_bytes
            and allow_empty_valid
            and (allow_empty_files or size_bytes > 0)
        )

        if not size_valid:
            errors.append("size")

        unique_errors = list(dict.fromkeys(errors))
        return {"valid": not unique_errors, "errors": unique_errors}

    except BaseException:
        return {"valid": False, "errors": ["filename", "extension", "content_type", "size"]}