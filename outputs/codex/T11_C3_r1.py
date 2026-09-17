import os
import re


def validate_entries(entries, destination, config) -> dict:
    errors = []
    rejected_indices = set()

    try:
        if not isinstance(entries, list):
            return {"valid": False, "errors": ["Invalid entries input."], "rejected": []}

        if not isinstance(destination, str) or not destination or "\x00" in destination:
            return {"valid": False, "errors": ["Invalid destination."], "rejected": []}

        if not isinstance(config, dict):
            return {"valid": False, "errors": ["Invalid configuration."], "rejected": []}

        allowed = config.get("allowed_extensions")
        if not isinstance(allowed, list):
            return {"valid": False, "errors": ["Invalid allowed extensions."], "rejected": []}

        allowed_extensions = set()
        for extension in allowed:
            if (
                not isinstance(extension, str)
                or "\x00" in extension
                or "/" in extension
                or "\\" in extension
                or "." in extension
            ):
                return {
                    "valid": False,
                    "errors": ["Invalid allowed extensions."],
                    "rejected": [],
                }
            allowed_extensions.add(extension.casefold())

        destination_abs = os.path.abspath(os.path.normpath(destination))
        normalized_targets = {}

        reserved_names = {
            "con", "prn", "aux", "nul",
            *(f"com{i}" for i in range(1, 10)),
            *(f"lpt{i}" for i in range(1, 10)),
        }

        for index, entry in enumerate(entries):
            if not isinstance(entry, str) or not entry or "\x00" in entry:
                rejected_indices.add(index)
                errors.append("Invalid archive entry path.")
                continue

            path = entry.replace("\\", "/")

            if path.startswith("/") or re.match(r"^[A-Za-z]:", path):
                rejected_indices.add(index)
                errors.append("Absolute or drive-qualified archive path.")
                continue

            components = []
            unsafe = False

            for component in path.split("/"):
                if component == "" or component == ".":
                    continue

                if component == "..":
                    if not components:
                        unsafe = True
                        break
                    components.pop()
                    continue

                if ":" in component:
                    unsafe = True
                    break

                if component.endswith((" ", ".")):
                    unsafe = True
                    break

                device_name = component.split(".", 1)[0].casefold()
                if device_name in reserved_names:
                    unsafe = True
                    break

                components.append(component)

            if unsafe or not components:
                rejected_indices.add(index)
                errors.append("Unsafe archive entry path.")
                continue

            basename = components[-1]
            dot = basename.rfind(".")
            extension = basename[dot + 1:].casefold() if dot > 0 else ""

            if extension not in allowed_extensions:
                rejected_indices.add(index)
                errors.append("Disallowed archive entry type.")
                continue

            target = os.path.normpath(os.path.join(destination_abs, *components))

            try:
                if os.path.commonpath([destination_abs, target]) != destination_abs:
                    rejected_indices.add(index)
                    errors.append("Archive entry escapes destination.")
                    continue
            except (TypeError, ValueError):
                rejected_indices.add(index)
                errors.append("Archive entry escapes destination.")
                continue

            duplicate_key = os.path.normcase(target).casefold()
            previous_index = normalized_targets.get(duplicate_key)
            if previous_index is not None:
                rejected_indices.add(previous_index)
                rejected_indices.add(index)
                errors.append("Duplicate archive destination path.")
            else:
                normalized_targets[duplicate_key] = index

        rejected = [
            entry for index, entry in enumerate(entries)
            if index in rejected_indices
        ]

        return {
            "valid": not rejected_indices,
            "errors": errors,
            "rejected": rejected,
        }

    except Exception:
        return {
            "valid": False,
            "errors": ["Archive entry validation failed."],
            "rejected": [],
        }