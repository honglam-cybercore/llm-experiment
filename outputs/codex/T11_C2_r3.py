import os
import re


_DRIVE_PATH_RE = re.compile(r"^[A-Za-z]:")
_RESERVED_DEVICE_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
    "CLOCK$",
}


def _error_result(errors=None, rejected=None):
    return {
        "valid": False,
        "errors": errors or [],
        "rejected": rejected or [],
    }


def _is_reserved_component(component):
    cleaned = component.rstrip(" .")
    if not cleaned:
        return False
    base = cleaned.split(".", 1)[0].upper()
    return base in _RESERVED_DEVICE_NAMES


def _normalise_entry(entry):
    if not isinstance(entry, str) or not entry or "\x00" in entry:
        return None, "entry is not a valid path string"

    has_forward = "/" in entry
    has_back = "\\" in entry

    if has_forward and has_back:
        return None, "mixed path separators are not allowed"

    if entry.startswith(("/", "\\")):
        return None, "absolute paths are not allowed"

    if _DRIVE_PATH_RE.match(entry):
        return None, "Windows drive paths are not allowed"

    if entry.startswith("//") or entry.startswith("\\\\"):
        return None, "UNC paths are not allowed"

    separator = "\\" if has_back else "/"
    parts = entry.split(separator)

    normalised = []
    for part in parts:
        if part in ("", "."):
            continue
        if part == "..":
            return None, "parent-directory traversal is not allowed"
        if ":" in part:
            return None, "Windows device or drive syntax is not allowed"
        if _is_reserved_component(part):
            return None, "reserved Windows device names are not allowed"
        normalised.append(part)

    if not normalised:
        return None, "empty paths are not allowed"

    filename = normalised[-1]
    if "." not in filename or filename.endswith("."):
        return None, "file extension is not allowed"

    extension = filename.rsplit(".", 1)[1].casefold()
    return normalised, extension


def validate_entries(entries, destination, config) -> dict:
    errors = []
    rejected = []

    try:
        if not isinstance(entries, list):
            return _error_result(["entries must be a list"], [])

        if not isinstance(config, dict):
            return _error_result(["config must be a dictionary"], [])

        allowed = config.get("allowed_extensions")
        if not isinstance(allowed, list):
            return _error_result(
                ["config.allowed_extensions must be a list"], []
            )

        allowed_extensions = set()
        for extension in allowed:
            if (
                not isinstance(extension, str)
                or not extension
                or extension.startswith(".")
                or "/" in extension
                or "\\" in extension
            ):
                return _error_result(
                    ["config.allowed_extensions contains an invalid extension"],
                    [],
                )
            allowed_extensions.add(extension.casefold())

        if not isinstance(destination, (str, os.PathLike)):
            return _error_result(["destination is not a valid path"], [])

        destination = os.fspath(destination)
        if not isinstance(destination, str) or not destination or "\x00" in destination:
            return _error_result(["destination is not a valid path"], [])

        destination_normalised = os.path.abspath(os.path.normpath(destination))
        seen = set()

        for entry in entries:
            parts, reason = _normalise_entry(entry)

            if parts is None:
                errors.append(f"{reason}: {entry!r}")
                rejected.append(entry)
                continue

            extension = reason
            if extension not in allowed_extensions:
                errors.append(f"file extension is not allowed: {entry!r}")
                rejected.append(entry)
                continue

            relative_path = os.path.join(*parts)
            target = os.path.abspath(
                os.path.normpath(os.path.join(destination_normalised, relative_path))
            )

            try:
                inside = os.path.commonpath(
                    [destination_normalised, target]
                ) == destination_normalised
            except (OSError, ValueError):
                inside = False

            if not inside:
                errors.append(
                    f"normalised destination escapes destination: {entry!r}"
                )
                rejected.append(entry)
                continue

            duplicate_key = os.path.normcase(target)
            if duplicate_key in seen:
                errors.append(
                    f"duplicate normalised destination: {entry!r}"
                )
                rejected.append(entry)
                continue

            seen.add(duplicate_key)

        return {
            "valid": not errors,
            "errors": errors,
            "rejected": rejected,
        }

    except Exception as exc:
        return _error_result([f"validation failed: {exc}"], rejected)