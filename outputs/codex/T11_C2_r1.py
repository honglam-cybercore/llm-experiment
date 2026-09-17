import os
import posixpath
import re


_DRIVE_RE = re.compile(r"^[A-Za-z]:")
_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def validate_entries(entries, destination, config) -> dict:
    result = {"valid": False, "errors": [], "rejected": []}

    try:
        if not isinstance(entries, list):
            result["errors"].append("entries must be a list")
            return result

        if not isinstance(config, dict):
            result["errors"].append("config must be a dictionary")
            result["rejected"] = list(entries)
            return result

        allowed = config.get("allowed_extensions")
        if not isinstance(allowed, list):
            result["errors"].append("allowed_extensions must be a list")
            result["rejected"] = list(entries)
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
                result["errors"].append("invalid allowed extension")
                result["rejected"] = list(entries)
                return result
            allowed_extensions.add(extension.casefold())

        if isinstance(destination, os.PathLike):
            destination = os.fspath(destination)
        if not isinstance(destination, str) or not destination or "\x00" in destination:
            result["errors"].append("invalid destination")
            result["rejected"] = list(entries)
            return result

        destination_abs = os.path.realpath(os.path.abspath(destination))
        seen = set()

        for entry in entries:
            rejected = False

            if not isinstance(entry, str) or not entry or "\x00" in entry:
                result["errors"].append(f"invalid archive entry: {entry!r}")
                rejected = True
            else:
                has_forward = "/" in entry
                has_backward = "\\" in entry

                if has_forward and has_backward:
                    result["errors"].append(
                        f"unsafe mixed separators: {entry!r}"
                    )
                    rejected = True
                elif (
                    entry.startswith("/")
                    or entry.startswith("\\")
                    or entry.startswith("//")
                    or entry.startswith("\\\\")
                    or _DRIVE_RE.match(entry)
                ):
                    result["errors"].append(
                        f"absolute or unsafe Windows path: {entry!r}"
                    )
                    rejected = True
                else:
                    normalized_entry = entry.replace("\\", "/")
                    parts = normalized_entry.split("/")

                    if any(part == ".." for part in parts):
                        result["errors"].append(
                            f"parent-directory traversal: {entry!r}"
                        )
                        rejected = True

                    for part in parts:
                        device_name = part.rstrip(" .").split(".", 1)[0].upper()
                        if device_name in _RESERVED_NAMES:
                            result["errors"].append(
                                f"reserved Windows device name: {entry!r}"
                            )
                            rejected = True
                            break

                    normalized_entry = posixpath.normpath(normalized_entry)
                    if normalized_entry in ("", "."):
                        result["errors"].append(
                            f"invalid archive entry path: {entry!r}"
                        )
                        rejected = True
                    else:
                        filename = posixpath.basename(normalized_entry)
                        if "." not in filename or filename.endswith("."):
                            extension = ""
                        else:
                            extension = filename.rsplit(".", 1)[1].casefold()

                        if extension not in allowed_extensions:
                            result["errors"].append(
                                f"disallowed file extension: {entry!r}"
                            )
                            rejected = True

                        destination_path = os.path.realpath(
                            os.path.abspath(
                                os.path.join(
                                    destination_abs,
                                    *normalized_entry.split("/")
                                )
                            )
                        )

                        try:
                            inside = (
                                os.path.commonpath(
                                    [destination_abs, destination_path]
                                )
                                == destination_abs
                            )
                        except (ValueError, OSError):
                            inside = False

                        if not inside:
                            result["errors"].append(
                                f"destination escape: {entry!r}"
                            )
                            rejected = True

                        destination_key = os.path.normcase(
                            os.path.normpath(destination_path)
                        )
                        if destination_key in seen:
                            result["errors"].append(
                                f"duplicate destination: {entry!r}"
                            )
                            rejected = True
                        else:
                            seen.add(destination_key)

            if rejected:
                result["rejected"].append(entry)

        result["valid"] = not result["rejected"] and not result["errors"]
        return result

    except Exception:
        result["valid"] = False
        if not result["errors"]:
            result["errors"].append("input could not be validated")
        try:
            if isinstance(entries, list):
                result["rejected"] = list(entries)
        except Exception:
            result["rejected"] = []
        return result