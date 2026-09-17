import os
import re


_RESERVED_DEVICE_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "CLOCK$",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def validate_entries(entries, destination, config) -> dict:
    errors = []
    rejected = []

    def invalid(message):
        return {"valid": False, "errors": [message], "rejected": []}

    try:
        if not isinstance(entries, list):
            return invalid("entries must be a list")

        if not isinstance(destination, (str, os.PathLike)):
            return invalid("destination must be a path")

        if not isinstance(config, dict):
            return invalid("config must be a dictionary")

        allowed = config.get("allowed_extensions")
        if not isinstance(allowed, list):
            return invalid("allowed_extensions must be a list")

        allowed_extensions = set()
        for extension in allowed:
            if not isinstance(extension, str) or not extension or extension.startswith("."):
                return invalid("allowed_extensions contains an invalid extension")
            allowed_extensions.add(extension.casefold())

        destination_path = os.path.abspath(os.fspath(destination))
        destination_path = os.path.normpath(destination_path)

        normalized_paths = []
        rejected_indexes = set()

        for index, entry in enumerate(entries):
            if not isinstance(entry, str):
                errors.append("entry is not a string")
                rejected.append(entry)
                rejected_indexes.add(index)
                normalized_paths.append(None)
                continue

            reason = None
            raw_path = entry.replace("\\", "/")

            if not raw_path or "\x00" in raw_path:
                reason = "entry is empty or contains a null character"
            elif raw_path.startswith("/") or raw_path.startswith("//"):
                reason = "entry is an absolute or UNC path"
            elif re.match(r"^[A-Za-z]:", raw_path):
                reason = "entry contains a drive letter"
            else:
                parts = []
                for part in raw_path.split("/"):
                    if part in ("", "."):
                        continue
                    if part == "..":
                        if not parts:
                            reason = "entry escapes the destination"
                            break
                        parts.pop()
                        continue

                    if ":" in part:
                        reason = "entry contains an unsafe colon"
                        break

                    if part.endswith((" ", ".")):
                        reason = "entry contains an unsafe trailing character"
                        break

                    device_name = part.split(".", 1)[0].upper()
                    if device_name in _RESERVED_DEVICE_NAMES:
                        reason = "entry contains a reserved device name"
                        break

                    parts.append(part)

                if reason is None:
                    if not parts:
                        reason = "entry has no file name"
                    else:
                        filename = parts[-1]
                        extension = os.path.splitext(filename)[1]
                        if not extension or extension[1:].casefold() not in allowed_extensions:
                            reason = "entry has a disallowed extension"

            if reason is not None:
                errors.append(f"{entry}: {reason}")
                rejected.append(entry)
                rejected_indexes.add(index)
                normalized_paths.append(None)
                continue

            relative_path = os.path.join(*parts)
            candidate = os.path.normpath(os.path.abspath(
                os.path.join(destination_path, relative_path)
            ))

            try:
                if os.path.commonpath((destination_path, candidate)) != destination_path:
                    reason = "entry escapes the destination"
            except (OSError, ValueError):
                reason = "entry destination cannot be validated"

            if reason is not None:
                errors.append(f"{entry}: {reason}")
                rejected.append(entry)
                rejected_indexes.add(index)
                normalized_paths.append(None)
            else:
                normalized_paths.append(candidate.casefold())

        seen = {}
        for index, normalized_path in enumerate(normalized_paths):
            if normalized_path is None:
                continue
            if normalized_path in seen:
                first_index = seen[normalized_path]
                for duplicate_index in (first_index, index):
                    if duplicate_index not in rejected_indexes:
                        rejected_indexes.add(duplicate_index)
                        rejected.append(entries[duplicate_index])
                        errors.append(
                            f"{entries[duplicate_index]}: duplicate destination path"
                        )
            else:
                seen[normalized_path] = index

        return {
            "valid": not errors,
            "errors": errors,
            "rejected": rejected,
        }

    except Exception:
        return {
            "valid": False,
            "errors": ["input could not be validated"],
            "rejected": rejected,
        }