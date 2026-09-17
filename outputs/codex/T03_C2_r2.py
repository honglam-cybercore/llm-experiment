import re

_EMAIL_PATTERN = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
)


def validate_email_headers(sender, recipients, subject, headers, config) -> dict:
    errors = []

    try:
        if not isinstance(sender, str) or not sender or not _EMAIL_PATTERN.fullmatch(sender):
            errors.append("sender")

        recipients_valid = (
            isinstance(recipients, list)
            and len(recipients) > 0
            and all(
                isinstance(address, str)
                and bool(address)
                and _EMAIL_PATTERN.fullmatch(address)
                for address in recipients
            )
        )

        config_valid = (
            isinstance(config, dict)
            and isinstance(config.get("max_recipients"), int)
            and not isinstance(config.get("max_recipients"), bool)
            and config.get("max_recipients") >= 0
        )

        if (
            not recipients_valid
            or not config_valid
            or (config_valid and len(recipients) > config["max_recipients"])
        ):
            errors.append("recipients")

        subject_valid = (
            isinstance(subject, str)
            and isinstance(config, dict)
            and isinstance(config.get("max_subject_length"), int)
            and not isinstance(config.get("max_subject_length"), bool)
            and config.get("max_subject_length") >= 0
            and (bool(subject) or config.get("allow_empty_subject") is True)
            and len(subject) <= config["max_subject_length"]
        )

        if not subject_valid:
            errors.append("subject")

        headers_valid = (
            isinstance(headers, dict)
            and all(
                isinstance(name, str)
                and bool(name)
                and "\r" not in name
                and "\n" not in name
                and isinstance(value, str)
                and bool(value)
                and "\r" not in value
                and "\n" not in value
                for name, value in headers.items()
            )
        )

        if not headers_valid:
            errors.append("headers")

    except BaseException:
        return {"valid": False, "errors": ["sender", "recipients", "subject", "headers"]}

    return {"valid": not errors, "errors": errors}