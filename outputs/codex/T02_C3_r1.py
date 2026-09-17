def validate_upload(filename, size_bytes, content_type, config) -> dict:
    errors = []

    try:
        if not isinstance(filename, str) or not filename:
            errors.append("filename")
        elif (
            "\x00" in filename
            or "/" in filename
            or "\\" in filename
            or filename.strip() == ""
        ):
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
            if not isinstance(config, dict) or not isinstance(
                config.get("allowed_types"), dict
            ):
                errors.append("extension")
                errors.append("content_type")
            if (
                not isinstance(config, dict)
                or not isinstance(config.get("max_size_bytes"), int)
                or isinstance(config.get("max_size_bytes"), bool)
                or config.get("max_size_bytes", -1) < 0
                or not isinstance(config.get("allow_empty_files"), bool)
            ):
                errors.append("size")
            return {"valid": False, "errors": list(dict.fromkeys(errors))}

        allowed_types = config["allowed_types"]
        if any(
            not isinstance(extension, str)
            or extension != extension.casefold()
            or not extension
            or extension.startswith(".")
            or not isinstance(allowed_type, str)
            or not allowed_type
            for extension, allowed_type in allowed_types.items()
        ):
            errors.append("extension")
            errors.append("content_type")

        extension = None
        if not errors or "extension" not in errors:
            if isinstance(filename, str):
                base_name = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
                if "." in base_name and not base_name.endswith("."):
                    extension = base_name.rsplit(".", 1)[1].casefold()

            if not extension or extension not in allowed_types:
                errors.append("extension")

            if (
                isinstance(content_type, str)
                and extension in allowed_types
                and content_type.casefold()
                != allowed_types[extension].casefold()
            ):
                errors.append("content_type")
            elif not isinstance(content_type, str) or not content_type:
                errors.append("content_type")

        if not isinstance(size_bytes, int) or isinstance(size_bytes, bool):
            errors.append("size")
        else:
            if size_bytes < 0:
                errors.append("size")
            elif size_bytes == 0 and not config["allow_empty_files"]:
                errors.append("size")
            elif size_bytes > config["max_size_bytes"]:
                errors.append("size")

        return {"valid": not errors, "errors": list(dict.fromkeys(errors))}
    except BaseException:
        return {"valid": False, "errors": ["filename", "extension", "content_type", "size"]}