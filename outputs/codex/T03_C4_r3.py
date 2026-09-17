import re

_EMAIL_RE = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"[A-Za-z]{2,63}$"
)
_HEADER_NAME_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")


def validate_email_headers(sender, recipients, subject, headers, config) -> dict:
    try:
        errors = []

        if not isinstance(config, dict):
            return {"valid": False, "errors": ["sender", "recipients", "subject", "headers"]}

        max_recipients = config.get("max_recipients")
        max_subject_length = config.get("max_subject_length")
        allow_empty_subject = config.get("allow_empty_subject")

        if (
            type(max_recipients) is not int
            or max_recipients < 0
            or type(max_subject_length) is not int
            or max_subject_length < 0
            or type(allow_empty_subject) is not bool
        ):
            return {"valid": False, "errors": ["sender", "recipients", "subject", "headers"]}

        if (
            not isinstance(sender, str)
            or not sender
            or "\r" in sender
            or "\n" in sender
            or _EMAIL_RE.fullmatch(sender) is None
        ):
            errors.append("sender")

        if (
            type(recipients) is not list
            or not recipients
            or len(recipients) > max_recipients
            or any(
                not isinstance(address, str)
                or not address
                or "\r" in address
                or "\n" in address
                or _EMAIL_RE.fullmatch(address) is None
                for address in recipients
            )
        ):
            errors.append("recipients")

        if (
            not isinstance(subject, str)
            or "\r" in subject
            or "\n" in subject
            or len(subject) > max_subject_length
            or (not subject and not allow_empty_subject)
        ):
            errors.append("subject")

        if (
            type(headers) is not dict
            or any(
                not isinstance(name, str)
                or not name
                or "\r" in name
                or "\n" in name
                or _HEADER_NAME_RE.fullmatch(name) is None
                or not isinstance(value, str)
                or not value
                or "\r" in value
                or "\n" in value
                for name, value in headers.items()
            )
        ):
            errors.append("headers")

        return {"valid": not errors, "errors": errors}
    except BaseException:
        return {"valid": False, "errors": ["sender", "recipients", "subject", "headers"]}