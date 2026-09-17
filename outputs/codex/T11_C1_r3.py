import os
import posixpath
import re
import unicodedata


_DRIVE_RE = re.compile(r"^[A-Za-z]:")
_RESERVED_NAMES = {
    "con",
    "prn",
    "aux",
    "nul",
    "clock$",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
    "com¹",
    "com²",
    "com³",
    "lpt¹",
    "lpt²",
    "lpt³",
}


def validate_entries(entries, destination, config) -> dict:
    errors = []
    rejected = []

    try:
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
                "errors": ["config.allowed_extensions must be a list"],
                "rejected": [],
            }

        allowed_extensions = set()
        for extension in allowed:
            if not isinstance(extension, str) or not extension:
                return {
                    "valid": False,
                    "errors": ["allowed_extensions must contain non-empty strings"],
                    "rejected": [],
                }
            if extension.startswith(".") or any(
                char in extension for char in ("/", "\\", "\x00")
            ):
                return {
                    "valid": False,
                    "errors": ["allowed_extensions must contain extensions without dots"],
                    "rejected": [],
                }
            allowed_extensions.add(extension.casefold())

        if isinstance(destination, os.PathLike):
            destination = os.fspath(destination)
        if not isinstance(destination, str) or not destination or "\x00" in destination:
            return {
                "valid": False,
                "errors": ["destination must be a valid directory path"],
                "rejected": [],
            }

        destination_abs = os.path.normpath(os.path.abspath(destination))
        destination_key = os.path.normcase(destination_abs).casefold()

        candidates = {}
        entry_data = []

        for entry in entries:
            if not isinstance(entry, str):
                errors.append("entry is not a string")
                rejected.append(entry)
                entry_data.append(None)
                continue

            entry_errors = []
            if not entry or "\x00" in entry:
                entry_errors.append("entry is empty or contains a null byte")

            if entry.startswith(("/", "\\")) or _DRIVE_RE.match(entry):
                entry_errors.append("entry is an absolute or drive-qualified path")

            normalized = entry.replace("\\", "/")
            raw_parts = normalized.split("/")
            parts = []

            for part in raw_parts:
                if part in ("", "."):
                    continue
                if part == "..":
                    if not parts:
                        entry_errors.append("entry escapes the destination")
                    else:
                        parts.pop()
                    continue

                if ":" in part:
                    entry_errors.append("entry contains an unsafe colon")
                if part.rstrip(" .").casefold() in _RESERVED_NAMES:
                    entry_errors.append("entry contains a reserved Windows device name")
                parts.append(part)

            if not parts:
                entry_errors.append("entry does not identify a file")

            normalized_relative = posixpath.join(*parts) if parts else ""
            filename = parts[-1] if parts else ""
            extension = os.path.splitext(filename)[1]

            if not extension or extension[1:].casefold() not in allowed_extensions:
                entry_errors.append("entry has a disallowed file extension")

            target = os.path.normpath(
                os.path.join(destination_abs, *parts)
            ) if parts else destination_abs

            try:
                target_key = os.path.normcase(target).casefold()
                if os.path.commonpath([destination_key, target_key]) != destination_key:
                    entry_errors.append("entry escapes the destination")
            except Exception:
                entry_errors.append("entry destination could not be normalized")

            if entry_errors:
                for message in dict.fromkeys(entry_errors):
                    errors.append(f"{entry!r}: {message}")
                rejected.append(entry)
                entry_data.append(None)
            else:
                candidates.setdefault(target_key, []).append(len(entry_data))
                entry_data.append((entry, target_key, normalized_relative))

        for indexes in candidates.values():
            if len(indexes) > 1:
                for index in indexes:
                    entry = entry_data[index][0]
                    errors.append(f"{entry!r}: duplicate destination path")
                    rejected.append(entry)

        rejected_set = {id(entry) for entry in rejected}
        return {
            "valid": not errors,
            "errors": errors,
            "rejected": rejected,
        }

    except BaseException:
        return {
            "valid": False,
            "errors": ["input could not be validated"],
            "rejected": rejected,
        }