import re

_EMAIL_RE = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)
_HEADER_NAME_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")


def validate_email_headers(sender, recipients, subject, headers, config) -> dict:
    errors = []

    try:
        config_valid = (
            type(config) is dict
            and type(config.get("max_recipients")) is int
            and config["max_recipients"] >= 0
            and type(config.get("max_subject_length")) is int
            and config["max_subject_length"] >= 0
            and type(config.get("allow_empty_subject")) is bool
        )

        if not isinstance(sender, str) or not sender or not _EMAIL_RE.fullmatch(sender):
            errors.append("sender")

        recipients_valid = (
            isinstance(recipients, list)
            and len(recipients) > 0
            and all(
                isinstance(address, str)
                and bool(address)
                and _EMAIL_RE.fullmatch(address) is not None
                for address in recipients
            )
        )
        if config_valid and len(recipients) > config["max_recipients"]:
            recipients_valid = False
        if not recipients_valid:
            errors.append("recipients")

        subject_valid = (
            isinstance(subject, str)
            and "\r" not in subject
            and "\n" not in subject
        )
        if config_valid and subject_valid:
            subject_valid = len(subject) <= config["max_subject_length"]
            if not config["allow_empty_subject"] and not subject:
                subject_valid = False
        else:
            subject_valid = False
        if not subject_valid:
            errors.append("subject")

        headers_valid = isinstance(headers, dict) and all(
            isinstance(name, str)
            and bool(name)
            and _HEADER_NAME_RE.fullmatch(name) is not None
            and isinstance(value, str)
            and bool(value)
            and "\r" not in name
            and "\n" not in name
            and "\r" not in value
            and "\n" not in value
            for name, value in headers.items()
        )
        if not headers_valid:
            errors.append("headers")

        if not config_valid:
            for check in ("recipients", "subject"):
                if check not in errors:
                    errors.append(check)

        return {"valid": not errors, "errors": errors}
    except BaseException:
        return {
            "valid": False,
            "errors": ["sender", "recipients", "subject", "headers"],
        }