def validate_upload(filename, size_bytes, content_type, config) -> dict:
    try:
        errors = []

        def add_error(name):
            if name not in errors:
                errors.append(name)

        if not isinstance(filename, str) or not filename:
            add_error("filename")
            filename_ok = False
        else:
            filename_ok = (
                "\x00" not in filename
                and not any(ord(ch) < 32 or ord(ch) == 127 for ch in filename)
                and "/" not in filename
                and "\\" not in filename
                and filename not in (".", "..")
            )
            if not filename_ok:
                add_error("filename")

        if (
            not isinstance(config, dict)
            or not isinstance(config.get("allowed_types"), dict)
            or not isinstance(config.get("max_size_bytes"), int)
            or isinstance(config.get("max_size_bytes"), bool)
            or config.get("max_size_bytes") < 0
            or not isinstance(config.get("allow_empty_files"), bool)
        ):
            allowed_types_ok = False
            max_size_ok = False
            add_error("extension")
            add_error("size")
        else:
            allowed_types = config["allowed_types"]
            allowed_types_ok = True
            for extension, allowed_content_type in allowed_types.items():
                if (
                    not isinstance(extension, str)
                    or not extension
                    or extension != extension.lower()
                    or "." in extension
                    or not isinstance(allowed_content_type, str)
                    or not allowed_content_type
                ):
                    allowed_types_ok = False
                    break

            max_size_ok = True

            if not allowed_types_ok:
                add_error("extension")

        extension = None
        if filename_ok:
            last_dot = filename.rfind(".")
            if last_dot > 0 and last_dot < len(filename) - 1:
                extension = filename[last_dot + 1 :].lower()

        if filename_ok and allowed_types_ok:
            if extension is None or extension not in allowed_types:
                add_error("extension")

        if not isinstance(content_type, str) or not content_type:
            add_error("content_type")
        elif filename_ok and allowed_types_ok and extension in allowed_types:
            if content_type != allowed_types[extension]:
                add_error("content_type")

        if (
            not isinstance(size_bytes, int)
            or isinstance(size_bytes, bool)
            or size_bytes < 0
        ):
            add_error("size")
        elif max_size_ok:
            if size_bytes == 0 and not config["allow_empty_files"]:
                add_error("size")
            elif size_bytes > config["max_size_bytes"]:
                add_error("size")

        return {"valid": not errors, "errors": errors}
    except BaseException:
        return {
            "valid": False,
            "errors": ["filename", "extension", "content_type", "size"],
        }