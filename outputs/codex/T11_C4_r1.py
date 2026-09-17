import os
import posixpath
import re


def validate_entries(entries, destination, config) -> dict:
    errors = []
    rejected = []

    try:
        if not isinstance(entries, list):
            return {"valid": False, "errors": ["Invalid entries input"], "rejected": []}

        if not isinstance(config, dict):
            return {"valid": False, "errors": ["Invalid configuration"], "rejected": []}

        allowed = config.get("allowed_extensions")
        if not isinstance(allowed, list):
            return {"valid": False, "errors": ["Invalid allowed extensions"], "rejected": []}

        allowed_extensions = set()
        for extension in allowed:
            if (
                not isinstance(extension, str)
                or not extension
                or extension.startswith(".")
                or "/" in extension
                or "\\" in extension
                or any(ord(char) < 32 for char in extension)
            ):
                return {
                    "valid": False,
                    "errors": ["Invalid allowed extensions"],
                    "rejected": [],
                }
            allowed_extensions.add(extension.casefold())

        if isinstance(destination, os.PathLike):
            destination = os.fspath(destination)

        if not isinstance(destination, str) or not destination or "\x00" in destination:
            return {"valid": False, "errors": ["Invalid destination"], "rejected": []}

        base = os.path.abspath(os.path.normpath(destination))
        seen = set()

        reserved_names = {
            "CON", "PRN", "AUX", "NUL",
            *(f"COM{i}" for i in range(1, 10)),
            *(f"LPT{i}" for i in range(1, 10)),
        }
        drive_pattern = re.compile(r"^[A-Za-z]:")

        for entry in entries:
            valid_entry = True

            if not isinstance(entry, str) or not entry or "\x00" in entry:
                valid_entry = False
            else:
                has_forward = "/" in entry
                has_backward = "\\" in entry

                if has_forward and has_backward:
                    valid_entry = False
                else:
                    normalized_input = entry.replace("\\", "/")

                    if (
                        normalized_input.startswith("/")
                        or normalized_input.startswith("//")
                        or drive_pattern.match(normalized_input)
                    ):
                        valid_entry = False
                    else:
                        parts = normalized_input.split("/")

                        if any(part == ".." for part in parts):
                            valid_entry = False
                        elif any(
                            not part
                            or any(ord(char) < 32 for char in part)
                            for part in parts
                            if part != ""
                        ):
                            valid_entry = False
                        elif any(":" in part for part in parts):
                            valid_entry = False
                        else:
                            normalized_parts = [
                                part for part in parts if part not in ("", ".")
                            ]

                            if not normalized_parts:
                                valid_entry = False
                            else:
                                for part in normalized_parts:
                                    device_name = part.rstrip(" .").split(".", 1)[0]
                                    if device_name.upper() in reserved_names:
                                        valid_entry = False
                                        break

                            if valid_entry:
                                filename = normalized_parts[-1]
                                if "." not in filename:
                                    valid_entry = False
                                else:
                                    extension = filename.rsplit(".", 1)[1]
                                    if (
                                        not extension
                                        or extension.casefold()
                                        not in allowed_extensions
                                    ):
                                        valid_entry = False

                            if valid_entry:
                                normalized_relative = posixpath.normpath(
                                    "/".join(normalized_parts)
                                )
                                target = os.path.abspath(
                                    os.path.join(base, *normalized_relative.split("/"))
                                )

                                if os.path.commonpath((base, target)) != base:
                                    valid_entry = False
                                else:
                                    destination_key = os.path.normcase(
                                        os.path.normpath(target)
                                    ).casefold()

                                    if destination_key in seen:
                                        valid_entry = False
                                    else:
                                        seen.add(destination_key)

            if not valid_entry:
                if isinstance(entry, str):
                    rejected.append(entry)
                else:
                    rejected.append("<invalid entry>")
                errors.append("One or more archive entries are unsafe or unsupported")

        return {
            "valid": not rejected,
            "errors": errors,
            "rejected": rejected,
        }

    except Exception:
        return {
            "valid": False,
            "errors": ["Input could not be validated"],
            "rejected": rejected,
        }