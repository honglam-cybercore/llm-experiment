import os
import ntpath


def validate_entries(entries, destination, config) -> dict:
    errors = []
    rejected = []

    try:
        if not isinstance(entries, list):
            return {"valid": False, "errors": ["entries must be a list"], "rejected": []}

        if not isinstance(destination, str) or not destination:
            return {"valid": False, "errors": ["destination must be a non-empty string"], "rejected": []}

        if not isinstance(config, dict):
            return {"valid": False, "errors": ["config must be a dictionary"], "rejected": []}

        allowed = config.get("allowed_extensions")
        if not isinstance(allowed, list):
            return {"valid": False, "errors": ["allowed_extensions must be a list"], "rejected": []}

        allowed_extensions = set()
        for extension in allowed:
            if not isinstance(extension, str) or not extension or extension.startswith("."):
                return {
                    "valid": False,
                    "errors": ["allowed_extensions contains an invalid extension"],
                    "rejected": [],
                }
            allowed_extensions.add(extension.casefold())

        destination_abs = os.path.abspath(os.path.normpath(destination))
        destination_key = os.path.normcase(destination_abs).casefold()
        seen = set()

        reserved_names = {
            "CON", "PRN", "AUX", "NUL",
            *(f"COM{i}" for i in range(1, 10)),
            *(f"LPT{i}" for i in range(1, 10)),
        }

        for entry in entries:
            if not isinstance(entry, str):
                errors.append("an entry is not a string")
                rejected.append(entry)
                continue

            reason = None
            normalized = entry.replace("\\", "/")

            if not normalized or "\x00" in normalized:
                reason = "invalid entry path"
            elif (
                normalized.startswith("/")
                or normalized.startswith("//")
                or ntpath.isabs(entry)
                or ntpath.splitdrive(entry)[0]
            ):
                reason = "absolute or drive-qualified path"
            elif ":" in normalized:
                reason = "invalid path syntax"
            else:
                parts = []
                for part in normalized.split("/"):
                    if part in ("", "."):
                        continue
                    if part == "..":
                        if parts:
                            parts.pop()
                        else:
                            reason = "path escapes destination"
                            break
                    else:
                        parts.append(part)

                if reason is None:
                    for part in parts:
                        cleaned = part.rstrip(" .")
                        stem = ntpath.splitext(cleaned)[0].upper()
                        if not cleaned or stem in reserved_names:
                            reason = "reserved or invalid Windows path component"
                            break

                if reason is None:
                    relative = os.path.join(*parts) if parts else ""
                    candidate = os.path.abspath(os.path.normpath(
                        os.path.join(destination_abs, relative)
                    ))

                    try:
                        if os.path.commonpath([destination_abs, candidate]) != destination_abs:
                            reason = "path escapes destination"
                    except (OSError, ValueError):
                        reason = "invalid destination path"

                    if reason is None:
                        filename = parts[-1] if parts else ""
                        extension = ntpath.splitext(filename)[1]
                        if not extension or extension[1:].casefold() not in allowed_extensions:
                            reason = "file extension is not allowed"

                    if reason is None:
                        candidate_key = os.path.normcase(candidate).casefold()
                        if candidate_key in seen:
                            reason = "duplicate destination path"
                        else:
                            seen.add(candidate_key)

            if reason is not None:
                errors.append(reason)
                rejected.append(entry)

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