import re

_CONTENT_TYPE_RE = re.compile(
    r"^[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+$"
)
_EXTENSION_RE = re.compile(r"^[a-z0-9][a-z0-9+_-]*$")


def validate_upload(filename, size_bytes, content_type, config) -> dict:
    errors = []

    try:
        filename_valid = (
            type(filename) is str
            and bool(filename)
            and len(filename) <= 255
            and "\x00" not in filename
            and "/" not in filename
            and "\\" not in filename
            and ":" not in filename
            and ".." not in filename
            and not filename.endswith((" ", "."))
            and not any(
                ord(char) < 32 or ord(char) == 127 or char in "\u2028\u2029"
                for char in filename
            )
        )

        if not filename_valid:
            errors.append("filename")

        extension = None
        if filename_valid and "." in filename:
            extension = filename.rsplit(".", 1)[1].lower()

        if (
            extension is None
            or not extension
            or not _EXTENSION_RE.fullmatch(extension)
        ):
            errors.append("extension")

        content_type_valid = (
            type(content_type) is str
            and bool(content_type)
            and len(content_type) <= 255
            and _CONTENT_TYPE_RE.fullmatch(content_type) is not None
        )

        if not content_type_valid:
            errors.append("content_type")

        allowed_types_valid = False
        allowed_type = None

        if type(config) is dict and type(config.get("allowed_types")) is dict:
            allowed_types = config["allowed_types"]
            allowed_types_valid = True

            for configured_extension, configured_content_type in allowed_types.items():
                if (
                    type(configured_extension) is not str
                    or configured_extension != configured_extension.lower()
                    or not _EXTENSION_RE.fullmatch(configured_extension)
                    or type(configured_content_type) is not str
                    or _CONTENT_TYPE_RE.fullmatch(configured_content_type) is None
                ):
                    allowed_types_valid = False
                    break

            if extension is not None:
                allowed_type = allowed_types.get(extension)

        if not allowed_types_valid or allowed_type is None:
            if "extension" not in errors:
                errors.append("extension")
        elif (
            not content_type_valid
            or content_type.casefold() != allowed_type.casefold()
        ):
            if "content_type" not in errors:
                errors.append("content_type")

        size_valid = False
        if (
            type(config) is dict
            and type(config.get("max_size_bytes")) is int
            and type(config.get("allow_empty_files")) is bool
        ):
            max_size = config["max_size_bytes"]
            allow_empty = config["allow_empty_files"]

            if (
                max_size >= 0
                and type(size_bytes) is int
                and size_bytes >= 0
                and size_bytes <= max_size
                and (allow_empty or size_bytes != 0)
            ):
                size_valid = True

        if not size_valid:
            errors.append("size")

    except Exception:
        return {"valid": False, "errors": ["filename", "extension", "content_type", "size"]}

    return {"valid": not errors, "errors": errors}