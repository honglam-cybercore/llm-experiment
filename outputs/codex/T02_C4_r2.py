import re
import unicodedata


_MIME_RE = re.compile(
    r"^[A-Za-z0-9!#$&^_.+\-]+/[A-Za-z0-9!#$&^_.+\-]+(?:;[^\r\n]*)?$"
)
_EXTENSION_RE = re.compile(r"^[A-Za-z0-9]+$")
_RESERVED_NAMES = {
    "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}


def _invalid() -> dict:
    return {"valid": False, "errors": ["filename", "extension", "content_type", "size"]}


def validate_upload(filename, size_bytes, content_type, config) -> dict:
    try:
        errors = []

        config_ok = type(config) is dict
        allowed_types = None
        max_size = None
        allow_empty = None

        if config_ok:
            try:
                allowed_types = config["allowed_types"]
                max_size = config["max_size_bytes"]
                allow_empty = config["allow_empty_files"]
                config_ok = (
                    type(allowed_types) is dict
                    and type(max_size) is int
                    and max_size >= 0
                    and type(allow_empty) is bool
                )
            except BaseException:
                config_ok = False

        valid_filename = type(filename) is str and bool(filename)
        if valid_filename:
            if filename != filename.strip() or len(filename) > 255:
                valid_filename = False
            if any(
                ch in filename or unicodedata.category(ch).startswith("C")
                for ch in ("/", "\\", "\x00")
            ):
                valid_filename = False
            if any(ch in ':*?"<>|' for ch in filename):
                valid_filename = False
            if filename in {".", ".."} or filename.endswith((".", " ")):
                valid_filename = False
            if any(unicodedata.bidirectional(ch) in {"RLO", "LRO", "RLE", "LRE", "PDF", "RLI", "LRI", "FSI", "PDI"}
                   for ch in filename):
                valid_filename = False
            if filename.casefold().split(".", 1)[0] in _RESERVED_NAMES:
                valid_filename = False

        if not valid_filename:
            errors.append("filename")

        extension = None
        if valid_filename:
            dot = filename.rfind(".")
            if dot <= 0 or dot == len(filename) - 1:
                extension = None
            else:
                extension = filename[dot + 1:].casefold()

        valid_extension = (
            config_ok
            and extension is not None
            and bool(_EXTENSION_RE.fullmatch(extension))
            and extension in allowed_types
            and type(allowed_types[extension]) is str
        )
        if not valid_extension:
            errors.append("extension")

        valid_content_type = (
            type(content_type) is str
            and bool(content_type)
            and content_type == content_type.strip()
            and bool(_MIME_RE.fullmatch(content_type))
            and valid_extension
            and content_type == allowed_types[extension]
        )
        if not valid_content_type:
            errors.append("content_type")

        valid_size = (
            config_ok
            and type(size_bytes) is int
            and size_bytes >= 0
            and size_bytes <= max_size
            and (allow_empty or size_bytes > 0)
        )
        if not valid_size:
            errors.append("size")

        return {"valid": not errors, "errors": errors}
    except BaseException:
        return _invalid()