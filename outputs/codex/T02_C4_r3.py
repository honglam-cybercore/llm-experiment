def validate_upload(filename, size_bytes, content_type, config) -> dict:
    errors = []

    try:
        filename_valid = True
        if not isinstance(filename, str) or not filename:
            filename_valid = False
        else:
            if len(filename) > 255 or "\x00" in filename:
                filename_valid = False
            if any(ord(char) < 32 or ord(char) == 127 for char in filename):
                filename_valid = False
            if "/" in filename or "\\" in filename or ":" in filename:
                filename_valid = False
            if any(part in (".", "..") for part in filename.replace("\\", "/").split("/")):
                filename_valid = False
            if filename in (".", "..") or filename.endswith("."):
                filename_valid = False

        if not filename_valid:
            errors.append("filename")

        config_valid = (
            isinstance(config, dict)
            and isinstance(config.get("allowed_types"), dict)
            and isinstance(config.get("max_size_bytes"), int)
            and not isinstance(config.get("max_size_bytes"), bool)
            and config.get("max_size_bytes") >= 0
            and isinstance(config.get("allow_empty_files"), bool)
        )

        if not config_valid:
            errors.extend(["extension", "content_type", "size"])
            return {"valid": False, "errors": list(dict.fromkeys(errors))}

        allowed_types = config["allowed_types"]
        max_size = config["max_size_bytes"]
        allow_empty = config["allow_empty_files"]

        normalized_allowed = {}
        allowed_types_valid = True
        for extension, allowed_content_type in allowed_types.items():
            if (
                not isinstance(extension, str)
                or not extension
                or extension != extension.lower()
                or extension.startswith(".")
                or "." in extension
                or "/" in extension
                or "\\" in extension
                or not isinstance(allowed_content_type, str)
                or not allowed_content_type
            ):
                allowed_types_valid = False
                continue
            normalized_allowed[extension] = allowed_content_type

        extension = None
        if filename_valid:
            extension = filename.rsplit(".", 1)[-1].lower()
            if not extension or extension not in normalized_allowed:
                errors.append("extension")
        else:
            errors.append("extension")

        if (
            not isinstance(content_type, str)
            or not content_type
            or any(ord(char) < 32 or ord(char) == 127 for char in content_type)
            or content_type != content_type.strip()
            or any(char.isspace() for char in content_type)
        ):
            errors.append("content_type")
        elif (
            extension is None
            or extension not in normalized_allowed
            or content_type != normalized_allowed[extension]
        ):
            errors.append("content_type")

        if (
            not isinstance(size_bytes, int)
            or isinstance(size_bytes, bool)
            or size_bytes < 0
            or (size_bytes == 0 and not allow_empty)
            or size_bytes > max_size
        ):
            errors.append("size")

        if not allowed_types_valid:
            errors.extend(["extension", "content_type"])

        errors = list(dict.fromkeys(errors))
        return {"valid": not errors, "errors": errors}
    except Exception:
        return {
            "valid": False,
            "errors": list(dict.fromkeys(errors + ["filename", "extension", "content_type", "size"])),
        }