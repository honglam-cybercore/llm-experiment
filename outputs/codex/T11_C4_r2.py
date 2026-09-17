import os
import re


_RESERVED_NAMES = {
    "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
    "com¹", "com²", "com³",
    "lpt¹", "lpt²", "lpt³",
}


def _error(index, reason):
    return f"entry {index}: {reason}"


def _is_reserved_windows_component(component):
    if ":" in component:
        return True

    cleaned = component.rstrip(" .")
    if not cleaned:
        return False

    base = cleaned.split(".", 1)[0].casefold()
    return base in _RESERVED_NAMES


def validate_entries(entries, destination, config) -> dict:
    try:
        if type(entries) is not list:
            return {
                "valid": False,
                "errors": ["entries must be a list"],
                "rejected": [],
            }

        if type(config) is not dict:
            return {
                "valid": False,
                "errors": ["config must be a dictionary"],
                "rejected": list(entries),
            }

        allowed_extensions = config.get("allowed_extensions")
        if type(allowed_extensions) is not list:
            return {
                "valid": False,
                "errors": ["allowed_extensions must be a list"],
                "rejected": list(entries),
            }

        normalized_extensions = set()
        for extension in allowed_extensions:
            if (
                type(extension) is not str
                or not extension
                or extension.startswith(".")
                or "/" in extension
                or "\\" in extension
                or "\x00" in extension
            ):
                return {
                    "valid": False,
                    "errors": ["config contains an invalid extension"],
                    "rejected": list(entries),
                }
            normalized_extensions.add(extension.casefold())

        if type(destination) is not str or not destination or "\x00" in destination:
            return {
                "valid": False,
                "errors": ["destination is invalid"],
                "rejected": list(entries),
            }

        destination_path = os.path.normpath(os.path.abspath(destination))
        destination_key = os.path.normcase(destination_path)

        errors = []
        rejected = []
        seen_destinations = set()

        for index, entry in enumerate(entries):
            reason = None

            if type(entry) is not str:
                reason = "path is not a string"
            elif not entry or "\x00" in entry:
                reason = "path is empty or contains a null character"
            elif entry.endswith(("/", "\\")):
                reason = "path must identify a file"
            elif "/" in entry and "\\" in entry:
                reason = "mixed path separators are not allowed"
            elif (
                entry.startswith(("/", "\\"))
                or re.match(r"^[A-Za-z]:", entry)
            ):
                reason = "absolute or drive-qualified path is not allowed"
            else:
                portable_entry = entry.replace("\\", "/")
                components = portable_entry.split("/")

                if any(component == ".." for component in components):
                    reason = "parent-directory traversal is not allowed"
                elif any(
                    _is_reserved_windows_component(component)
                    for component in components
                    if component not in ("", ".")
                ):
                    reason = "unsafe Windows path component"
                else:
                    normalized_entry = os.path.normpath(
                        portable_entry.replace("/", os.sep)
                    )
                    candidate = os.path.normpath(
                        os.path.join(destination_path, normalized_entry)
                    )

                    try:
                        common = os.path.commonpath(
                            [destination_path, candidate]
                        )
                    except BaseException:
                        common = None

                    if common is None or os.path.normcase(common) != destination_key:
                        reason = "normalized path escapes destination"
                    else:
                        filename = os.path.basename(normalized_entry)
                        if "." not in filename or filename.startswith("."):
                            reason = "file extension is not allowed"
                        else:
                            suffix = filename.rsplit(".", 1)[1].casefold()
                            if suffix not in normalized_extensions:
                                reason = "file extension is not allowed"
                            else:
                                candidate_key = os.path.normcase(candidate)
                                if candidate_key in seen_destinations:
                                    reason = "duplicate normalized destination"
                                else:
                                    seen_destinations.add(candidate_key)

            if reason is not None:
                errors.append(_error(index, reason))
                rejected.append(entry)

        return {
            "valid": not errors,
            "errors": errors,
            "rejected": rejected,
        }

    except BaseException:
        return {
            "valid": False,
            "errors": ["input could not be validated"],
            "rejected": [],
        }