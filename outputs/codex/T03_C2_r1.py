import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email_headers(sender, recipients, subject, headers, config) -> dict:
    errors = []

    try:
        config_valid = (
            isinstance(config, dict)
            and type(config.get("max_recipients")) is int
            and config["max_recipients"] >= 0
            and type(config.get("max_subject_length")) is int
            and config["max_subject_length"] >= 0
            and type(config.get("allow_empty_subject")) is bool
        )

        sender_valid = (
            isinstance(sender, str)
            and bool(sender)
            and _EMAIL_RE.fullmatch(sender) is not None
        )
        if not sender_valid:
            errors.append("sender")

        recipients_valid = (
            isinstance(recipients, list)
            and config_valid
            and len(recipients) <= config["max_recipients"]
            and all(
                isinstance(address, str)
                and bool(address)
                and _EMAIL_RE.fullmatch(address) is not None
                for address in recipients
            )
        )
        if not recipients_valid:
            errors.append("recipients")

        subject_valid = (
            isinstance(subject, str)
            and config_valid
            and (bool(subject) or config["allow_empty_subject"])
            and len(subject) <= config["max_subject_length"]
            and "\r" not in subject
            and "\n" not in subject
        )
        if not subject_valid:
            errors.append("subject")

        headers_valid = (
            isinstance(headers, dict)
            and all(
                isinstance(name, str)
                and isinstance(value, str)
                and bool(name)
                and "\r" not in name
                and "\n" not in name
                and "\r" not in value
                and "\n" not in value
                and ":" not in name
                for name, value in headers.items()
            )
        )
        if not headers_valid:
            errors.append("headers")

        if not config_valid:
            for name in ("sender", "recipients", "subject", "headers"):
                if name not in errors:
                    errors.append(name)

        return {"valid": not errors, "errors": errors}
    except Exception:
        return {
            "valid": False,
            "errors": ["sender", "recipients", "subject", "headers"],
        }