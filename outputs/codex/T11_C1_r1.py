import os
import ntpath


def validate_entries(entries, destination, config) -> dict:
    errors = []
    rejected = []

    def fail(message, entry=None):
        errors.append(message)
        if entry is not None:
            rejected.append(entry)

    try:
        if not isinstance(entries, list):
            return {"valid": False, "errors": ["entries must be a list"], "rejected": []}

        if not isinstance(config, dict):
            return {"valid": False, "errors": ["config must be a dict"], "rejected": []}

        allowed = config.get("allowed_extensions")
        if not isinstance(allowed, list):
            return {"valid": False, "errors": ["allowed_extensions must be a list"], "rejected": []}

        allowed_extensions = set()
        for extension in allowed:
            if not isinstance(extension, str) or not extension or "." in extension:
                return {
                    "valid": False,
                    "errors": ["allowed_extensions contains an invalid extension"],
                    "rejected": [],
                }
            allowed_extensions.add(extension.casefold())

        if not isinstance(destination, (str, os.PathLike)):
            return {"valid": False, "errors": ["destination is invalid"], "rejected": []}

        destination = os.fspath(destination)
        if not isinstance(destination, str) or not destination or "\x00" in destination:
            return {"valid": False, "errors": ["destination is invalid"], "rejected": []}

        destination = os.path.abspath(os.path.normpath(destination))
        destination_key = os.path.normcase(destination).casefold()
        seen = set()

        reserved_names = {
            "con", "prn", "aux", "nul",
            *(f"com{i}" for i in range(1, 10)),
            *(f"lpt{i}" for i in range(1, 10)),
        }

        for entry in entries:
            if not isinstance(entry, str):
                fail("entry is not a string", entry)
                continue

            try:
                if not entry or "\x00" in entry:
                    fail("entry is empty or contains a null character", entry)
                    continue

                windows_entry = entry.replace("/", "\\")
                drive, _ = ntpath.splitdrive(windows_entry)

                if (
                    drive
                    or ntpath.isabs(windows_entry)
                    or windows_entry.startswith("\\")
                    or windows_entry.startswith("//")
                ):
                    fail("entry is absolute or uses an unsafe Windows path", entry)
                    continue

                components = [
                    component
                    for component in windows_entry.replace("\\", "/").split("/")
                    if component not in ("", ".")
                ]

                for component in components:
                    device_component = component.rstrip(" .").casefold()
                    device_component = device_component.split(":", 1)[0]
                    device_component = device_component.split(".", 1)[0]
                    if device_component in reserved_names:
                        raise ValueError("reserved device name")

                relative = os.path.join(*components) if components else ""
                candidate = os.path.abspath(os.path.normpath(os.path.join(destination, relative)))

                try:
                    within_destination = os.path.commonpath(
                        [destination_key, os.path.normcase(candidate).casefold()]
                    ) == destination_key
                except (ValueError, TypeError):
                    within_destination = False

                if not within_destination:
                    fail("normalised destination escapes destination", entry)
                    continue

                filename = components[-1] if components else ""
                extension = os.path.splitext(filename)[1]
                extension = extension[1:].casefold() if extension.startswith(".") else ""

                if extension not in allowed_extensions:
                    fail("entry extension is not allowed", entry)
                    continue

                destination_id = os.path.normcase(candidate).casefold()
                if destination_id in seen:
                    fail("duplicate destination path", entry)
                    continue

                seen.add(destination_id)

            except Exception:
                fail("entry cannot be validated", entry)

        return {
            "valid": not errors,
            "errors": errors,
            "rejected": rejected,
        }

    except Exception:
        return {
            "valid": False,
            "errors": ["input cannot be validated"],
            "rejected": rejected,
        }