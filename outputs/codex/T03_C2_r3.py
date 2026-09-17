import re


_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email_headers(sender, recipients, subject, headers, config) -> dict:
    errors = []

    try:
        config_valid = (
            type(config) is dict
            and type(config.get("max_recipients")) is int
            and type(config.get("max_subject_length")) is int
            and type(config.get("allow_empty_subject")) is bool
            and config["max_recipients"] >= 1
            and config["max_subject_length"] >= 0
        )

        if not config_valid:
            return {"valid": False, "errors": ["recipients", "subject"]}

        max_recipients = config["max_recipients"]
        max_subject_length = config["max_subject_length"]
        allow_empty_subject = config["allow_empty_subject"]

        if type(sender) is not str or not _EMAIL_PATTERN.fullmatch(sender):
            errors.append("sender")

        recipients_valid = (
            type(recipients) is list
            and len(recipients) > 0
            and len(recipients) <= max_recipients
            and all(
                type(address) is str and _EMAIL_PATTERN.fullmatch(address)
                for address in recipients
            )
        )
        if not recipients_valid:
            errors.append("recipients")

        subject_valid = (
            type(subject) is str
            and len(subject) <= max_subject_length
            and (allow_empty_subject or len(subject) > 0)
            and "\r" not in subject
            and "\n" not in subject
        )
        if not subject_valid:
            errors.append("subject")

        headers_valid = (
            type(headers) is dict
            and all(
                type(name) is str
                and type(value) is str
                and len(name) > 0
                and len(value) > 0
                and "\r" not in name
                and "\n" not in name
                and "\r" not in value
                and "\n" not in value
                for name, value in headers.items()
            )
        )
        if not headers_valid:
            errors.append("headers")

        return {"valid": not errors, "errors": errors}
    except Exception:
        return {"valid": False, "errors": ["sender", "recipients", "subject", "headers"]}