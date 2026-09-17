import os
import re
import unicodedata


_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")
_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL", "CLOCK$",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def validate_entries(entries, destination, config) -> dict:
    try:
        if not isinstance(entries, list):
            return {"valid": False, "errors": ["invalid entries"], "rejected": []}

        if not isinstance(config, dict):
            return {"valid": False, "errors": ["invalid config"], "rejected": []}

        allowed = config.get("allowed_extensions")
        if not isinstance(allowed, list):
            return {"valid": False, "errors": ["invalid allowed_extensions"], "rejected": []}

        allowed_extensions = set()
        for extension in allowed:
            if not isinstance(extension, str) or not extension or extension.startswith("."):
                return {
                    "valid": False,
                    "errors": ["invalid allowed_extensions"],
                    "rejected": [],
                }
            allowed_extensions.add(extension.casefold())

        if isinstance(destination, bytes):
            return {"valid": False, "errors": ["invalid destination"], "rejected": []}

        destination_path = os.fspath(destination)
        if not isinstance(destination_path, str) or not destination_path:
            return {"valid": False, "errors": ["invalid destination"], "rejected": []}

        destination_abs = os.path.abspath(os.path.normpath(destination_path))
        destination_key = os.path.normcase(destination_abs)

        errors = []
        rejected_indices = set()
        normalized_destinations = {}

        for index, entry in enumerate(entries):
            if not isinstance(entry, str) or not entry or "\x00" in entry:
                errors.append(f"entry {index}: invalid path")
                rejected_indices.add(index)
                continue

            try:
                path = unicodedata.normalize("NFC", entry)
            except Exception:
                errors.append(f"entry {index}: invalid path")
                rejected_indices.add(index)
                continue

            if "/" in path and "\\" in path:
                errors.append(f"entry {index}: mixed separators")
                rejected_indices.add(index)
                continue

            if _WINDOWS_DRIVE.match(path):
                errors.append(f"entry {index}: drive path")
                rejected_indices.add(index)
                continue

            if path.startswith(("/", "\\")):
                errors.append(f"entry {index}: absolute path")
                rejected_indices.add(index)
                continue

            path = path.replace("\\", "/")
            components = path.split("/")

            unsafe = False
            for component in components:
                if not component or component == ".":
                    continue

                if component == "..":
                    unsafe = True
                    break

                if component.endswith((" ", ".")) or ":" in component:
                    unsafe = True
                    break

                device_name = component.rstrip(" .").split(".", 1)[0].upper()
                if device_name in _RESERVED_NAMES:
                    unsafe = True
                    break

            if unsafe:
                errors.append(f"entry {index}: unsafe path")
                rejected_indices.add(index)
                continue

            relative_path = "/".join(
                component for component in components if component not in ("", ".")
            )
            if not relative_path:
                errors.append(f"entry {index}: invalid path")
                rejected_indices.add(index)
                continue

            filename = components[-1]
            if "." not in filename or filename.endswith("."):
                errors.append(f"entry {index}: disallowed file type")
                rejected_indices.add(index)
                continue

            extension = filename.rsplit(".", 1)[1].casefold()
            if extension not in allowed_extensions:
                errors.append(f"entry {index}: disallowed file type")
                rejected_indices.add(index)
                continue

            candidate = os.path.abspath(
                os.path.normpath(os.path.join(destination_abs, *relative_path.split("/")))
            )
            candidate_key = os.path.normcase(candidate)

            try:
                inside = os.path.commonpath((destination_key, candidate_key)) == destination_key
            except Exception:
                inside = False

            if not inside:
                errors.append(f"entry {index}: destination escape")
                rejected_indices.add(index)
                continue

            normalized_destinations.setdefault(candidate_key, []).append(index)

        for indices in normalized_destinations.values():
            if len(indices) > 1:
                for index in indices:
                    rejected_indices.add(index)
                    errors.append(f"entry {index}: duplicate destination")

        rejected = [entries[index] for index in sorted(rejected_indices)]
        return {
            "valid": not errors,
            "errors": errors,
            "rejected": rejected,
        }

    except BaseException:
        return {"valid": False, "errors": ["validation failed"], "rejected": []}