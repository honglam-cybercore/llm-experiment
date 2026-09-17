def validate_upload(filename, size_bytes, content_type, config) -> dict:
    errors = []

    try:
        if type(filename) is not str or not filename or "\x00" in filename:
            errors.append("filename")
        elif "/" in filename or "\\" in filename or filename in (".", ".."):
            errors.append("filename")

        if type(content_type) is not str or not content_type.strip():
            errors.append("content_type")

        extension = None
        if "filename" not in errors:
            name = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
            if "." not in name or name.startswith(".") or name.endswith("."):
                errors.append("extension")
            else:
                extension = name.rsplit(".", 1)[1].casefold()
                if not extension:
                    errors.append("extension")

        if type(config) is not dict:
            for check in ("extension", "content_type", "size"):
                if check not in errors:
                    errors.append(check)
            return {"valid": False, "errors": errors}

        allowed_types = config.get("allowed_types")
        max_size_bytes = config.get("max_size_bytes")
        allow_empty_files = config.get("allow_empty_files")

        if type(allowed_types) is not dict:
            if "extension" not in errors:
                errors.append("extension")
            if "content_type" not in errors:
                errors.append("content_type")
        elif extension is not None and "extension" not in errors:
            expected_type = allowed_types.get(extension)
            if type(expected_type) is not str:
                errors.append("extension")
            elif type(content_type) is str and (
                content_type.casefold() != expected_type.casefold()
            ):
                errors.append("content_type")

        if type(size_bytes) is not int or isinstance(size_bytes, bool):
            errors.append("size")
        elif type(max_size_bytes) is not int or isinstance(max_size_bytes, bool):
            errors.append("size")
        elif type(allow_empty_files) is not bool:
            errors.append("size")
        elif size_bytes < 0 or size_bytes > max_size_bytes:
            errors.append("size")
        elif size_bytes == 0 and not allow_empty_files:
            errors.append("size")

        return {"valid": not errors, "errors": errors}
    except BaseException:
        return {"valid": False, "errors": ["filename", "extension", "content_type", "size"]}