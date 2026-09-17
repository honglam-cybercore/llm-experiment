import os
import ntpath
import re


_RESERVED_DEVICE_RE = re.compile(
    r"^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?$",
    re.IGNORECASE,
)


def validate_entries(entries, destination, config) -> dict:
    errors = []
    rejected = []

    def reject(entry, message):
        rejected.append(entry)
        errors.append(message)

    if not isinstance(entries, list):
        return {
            "valid": False,
            "errors": ["entries must be a list"],
            "rejected": [],
        }

    if not isinstance(config, dict):
        return {
            "valid": False,
            "errors": ["config must be a dictionary"],
            "rejected": [],
        }

    allowed = config.get("allowed_extensions")
    if not isinstance(allowed, list):
        return {
            "valid": False,
            "errors": ["allowed_extensions must be a list"],
            "rejected": [],
        }

    allowed_extensions = set()
    for extension in allowed:
        if (
            not isinstance(extension, str)
            or not extension
            or "." in extension
            or "/" in extension
            or "\\" in extension
            or "\x00" in extension
        ):
            return {
                "valid": False,
                "errors": ["invalid allowed extension configuration"],
                "rejected": [],
            }
        allowed_extensions.add(extension.casefold())

    if not isinstance(destination, (str, os.PathLike)):
        return {
            "valid": False,
            "errors": ["destination must be a path"],
            "rejected": [],
        }

    try:
        destination_path = os.path.abspath(os.path.normpath(os.fspath(destination)))
    except Exception:
        return {
            "valid": False,
            "errors": ["destination cannot be validated"],
            "rejected": [],
        }

    seen = set()

    for entry in entries:
        if not isinstance(entry, str):
            reject(entry, "entry path must be a string")
            continue

        if not entry or "\x00" in entry:
            reject(entry, "entry path is empty or contains a null byte")
            continue

        if "/" in entry and "\\" in entry:
            reject(entry, "entry path uses mixed separators")
            continue

        if ntpath.splitdrive(entry)[0]:
            reject(entry, "entry path contains a Windows drive path")
            continue

        if ntpath.isabs(entry) or entry.startswith(("/", "\\")):
            reject(entry, "entry path is absolute")
            continue

        normalized_input = entry.replace("\\", "/")
        parts = normalized_input.split("/")

        if any(part == ".." for part in parts):
            reject(entry, "entry path contains parent-directory traversal")
            continue

        if any(
            _RESERVED_DEVICE_RE.match(part.rstrip(" ."))
            for part in parts
            if part not in ("", ".")
        ):
            reject(entry, "entry path contains a reserved Windows device name")
            continue

        normalized_relative = os.path.normpath(normalized_input)
        if normalized_relative in ("", ".") or normalized_relative == os.pardir:
            reject(entry, "entry path is not a file")
            continue

        basename = normalized_relative.replace("\\", "/").rsplit("/", 1)[-1]
        if "." not in basename or basename.startswith(".") and basename.count(".") == 1:
            reject(entry, "entry extension is not allowed")
            continue

        extension = basename.rsplit(".", 1)[1].casefold()
        if extension not in allowed_extensions:
            reject(entry, "entry extension is not allowed")
            continue

        try:
            candidate = os.path.abspath(
                os.path.normpath(os.path.join(destination_path, normalized_relative))
            )
            if os.path.commonpath((destination_path, candidate)) != destination_path:
                reject(entry, "normalized destination escapes destination")
                continue
        except Exception:
            reject(entry, "entry destination cannot be validated")
            continue

        destination_key = os.path.normcase(candidate)
        if destination_key in seen:
            reject(entry, "duplicate normalized destination")
            continue

        seen.add(destination_key)

    return {
        "valid": not errors,
        "errors": errors,
        "rejected": rejected,
    }