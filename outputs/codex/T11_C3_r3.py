import os
import re
import ntpath


_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
    "COM¹", "COM²", "COM³", "LPT¹", "LPT²", "LPT³",
}

_DRIVE_PREFIX = re.compile(r"^[A-Za-z]:")


def validate_entries(entries, destination, config) -> dict:
    result = {"valid": False, "errors": [], "rejected": []}

    def add_error(message):
        result["errors"].append(str(message))

    try:
        if not isinstance(entries, list):
            add_error("entries must be a list")
            return result

        if not isinstance(config, dict):
            add_error("config must be a dict")
            return result

        allowed = config.get("allowed_extensions")
        if not isinstance(allowed, list):
            add_error("allowed_extensions must be a list")
            return result

        allowed_extensions = set()
        for extension in allowed:
            if (
                not isinstance(extension, str)
                or not extension
                or extension.startswith(".")
                or "/" in extension
                or "\\" in extension
                or "\x00" in extension
            ):
                add_error("invalid allowed extension configuration")
                return result
            allowed_extensions.add(extension.casefold())

        if isinstance(destination, (str, bytes)):
            if isinstance(destination, bytes):
                add_error("destination must be a text path")
                return result
            destination_path = destination
        else:
            try:
                destination_path = os.fspath(destination)
            except Exception:
                add_error("destination must be a path")
                return result

            if not isinstance(destination_path, str):
                add_error("destination must be a text path")
                return result

        if not destination_path or "\x00" in destination_path:
            add_error("invalid destination")
            return result

        base = os.path.normpath(os.path.abspath(destination_path))
        seen = {}
        rejected_indices = set()

        for index, entry in enumerate(entries):
            reason = None
            normalized_parts = None

            if not isinstance(entry, str):
                reason = "entry path must be a string"
            elif not entry or "\x00" in entry:
                reason = "entry path is empty or contains a null character"
            else:
                path = entry.replace("\\", "/")

                if (
                    path.startswith("/")
                    or path.startswith("//")
                    or _DRIVE_PREFIX.match(path)
                ):
                    reason = "entry path is absolute or drive-qualified"
                else:
                    parts = []
                    for component in path.split("/"):
                        if component in ("", "."):
                            continue
                        if component == "..":
                            if not parts:
                                reason = "entry path escapes destination"
                                break
                            parts.pop()
                            continue
                        if (
                            component.endswith(" ")
                            or component.endswith(".")
                            or ":" in component
                        ):
                            reason = "entry path contains an unsafe component"
                            break

                        device_name = component.split(".", 1)[0].casefold()
                        if device_name.upper() in _RESERVED_NAMES:
                            reason = "entry path contains a reserved device name"
                            break

                        parts.append(component)

                    if reason is None:
                        if not parts:
                            reason = "entry path does not name a file"
                        else:
                            normalized_parts = parts

            if reason is not None:
                result["rejected"].append(entry)
                add_error(f"entry {index}: {reason}")
                rejected_indices.add(index)
                continue

            filename = normalized_parts[-1]
            extension = os.path.splitext(filename)[1]
            extension = extension[1:].casefold() if extension else ""

            if not extension or extension not in allowed_extensions:
                result["rejected"].append(entry)
                add_error(f"entry {index}: file extension is not allowed")
                rejected_indices.add(index)
                continue

            candidate = os.path.normpath(os.path.join(base, *normalized_parts))
            try:
                if os.path.commonpath((base, candidate)) != base:
                    raise ValueError
            except Exception:
                result["rejected"].append(entry)
                add_error(f"entry {index}: normalized destination escapes destination")
                rejected_indices.add(index)
                continue

            duplicate_key = ntpath.normcase(candidate.replace("/", "\\")).casefold()
            if duplicate_key in seen:
                previous_index, previous_entry = seen[duplicate_key]
                if previous_index not in rejected_indices:
                    result["rejected"].append(previous_entry)
                    rejected_indices.add(previous_index)
                result["rejected"].append(entry)
                rejected_indices.add(index)
                add_error(
                    f"entries {previous_index} and {index}: duplicate destination path"
                )
            else:
                seen[duplicate_key] = (index, entry)

        result["valid"] = not result["errors"]
        return result

    except Exception:
        result["valid"] = False
        add_error("input could not be validated")
        return result