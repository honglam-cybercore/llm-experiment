import re

_EMAIL_RE = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)
_HEADER_NAME_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")


def _valid_address(value):
    return (
        isinstance(value, str)
        and len(value) <= 254
        and "\r" not in value
        and "\n" not in value
        and bool(_EMAIL_RE.fullmatch(value))
    )


def validate_email_headers(sender, recipients, subject, headers, config) -> dict:
    errors = []

    try:
        if not isinstance(config, dict):
            return {
                "valid": False,
                "errors": ["sender", "recipients", "subject", "headers"],
            }

        max_recipients = config.get("max_recipients")
        max_subject_length = config.get("max_subject_length")
        allow_empty_subject = config.get("allow_empty_subject")

        if (
            not isinstance(max_recipients, int)
            or isinstance(max_recipients, bool)
            or max_recipients < 1
            or not isinstance(max_subject_length, int)
            or isinstance(max_subject_length, bool)
            or max_subject_length < 0
            or not isinstance(allow_empty_subject, bool)
        ):
            return {
                "valid": False,
                "errors": ["sender", "recipients", "subject", "headers"],
            }

        if not _valid_address(sender):
            errors.append("sender")

        if (
            not isinstance(recipients, list)
            or not recipients
            or len(recipients) > max_recipients
            or any(not _valid_address(address) for address in recipients)
        ):
            errors.append("recipients")

        if (
            not isinstance(subject, str)
            or ("\r" in subject or "\n" in subject)
            or len(subject) > max_subject_length
            or (not subject and not allow_empty_subject)
        ):
            errors.append("subject")

        if not isinstance(headers, dict):
            errors.append("headers")
        else:
            invalid_headers = False
            for name, value in headers.items():
                if (
                    not isinstance(name, str)
                    or not name
                    or not _HEADER_NAME_RE.fullmatch(name)
                    or not isinstance(value, str)
                    or "\r" in value
                    or "\n" in value
                ):
                    invalid_headers = True
                    break
            if invalid_headers:
                errors.append("headers")

    except Exception:
        return {
            "valid": False,
            "errors": ["sender", "recipients", "subject", "headers"],
        }

    return {"valid": not errors, "errors": errors}