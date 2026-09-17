import re
from email.utils import parseaddr


_ADDRESS_RE = re.compile(r"^[^@\s<>]+@[^@\s<>]+$")
_HEADER_NAME_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")


def _valid_address(value):
    if not isinstance(value, str) or not value or "\r" in value or "\n" in value:
        return False
    if value != value.strip() or not _ADDRESS_RE.fullmatch(value):
        return False
    _, parsed = parseaddr(value)
    return parsed == value


def validate_email_headers(sender, recipients, subject, headers, config) -> dict:
    errors = []

    try:
        if not _valid_address(sender):
            errors.append("sender")

        recipients_valid = (
            isinstance(recipients, list)
            and all(_valid_address(address) for address in recipients)
        )
        if isinstance(config, dict):
            max_recipients = config.get("max_recipients")
            if (
                not isinstance(max_recipients, int)
                or isinstance(max_recipients, bool)
                or max_recipients < 0
                or not recipients_valid
                or len(recipients) > max_recipients
                or not recipients
            ):
                recipients_valid = False
        else:
            recipients_valid = False

        if not recipients_valid:
            errors.append("recipients")

        subject_valid = isinstance(subject, str)
        if isinstance(config, dict):
            max_subject_length = config.get("max_subject_length")
            allow_empty_subject = config.get("allow_empty_subject")
            if (
                not isinstance(max_subject_length, int)
                or isinstance(max_subject_length, bool)
                or max_subject_length < 0
                or not isinstance(allow_empty_subject, bool)
                or not subject_valid
                or len(subject) > max_subject_length
                or (not subject and not allow_empty_subject)
                or "\r" in subject
                or "\n" in subject
            ):
                subject_valid = False
        else:
            subject_valid = False

        if not subject_valid:
            errors.append("subject")

        headers_valid = isinstance(headers, dict)
        if headers_valid:
            for name, value in headers.items():
                if (
                    not isinstance(name, str)
                    or not name
                    or not _HEADER_NAME_RE.fullmatch(name)
                    or not isinstance(value, str)
                    or "\r" in value
                    or "\n" in value
                ):
                    headers_valid = False
                    break

        if not headers_valid:
            errors.append("headers")

    except Exception:
        return {"valid": False, "errors": ["sender", "recipients", "subject", "headers"]}

    return {"valid": not errors, "errors": errors}