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
        if not isinstance(sender, str) or not sender or not _EMAIL_RE.fullmatch(sender):
            errors.append("sender")

        recipients_valid = (
            isinstance(recipients, list)
            and bool(recipients)
            and all(
                isinstance(address, str)
                and bool(address)
                and _EMAIL_RE.fullmatch(address) is not None
                for address in recipients
            )
        )

        config_valid = (
            isinstance(config, dict)
            and isinstance(config.get("max_recipients"), int)
            and not isinstance(config.get("max_recipients"), bool)
            and config.get("max_recipients") >= 0
        )
        if not recipients_valid or not config_valid:
            errors.append("recipients")
        elif len(recipients) > config["max_recipients"]:
            errors.append("recipients")

        subject_config_valid = (
            isinstance(config, dict)
            and isinstance(config.get("max_subject_length"), int)
            and not isinstance(config.get("max_subject_length"), bool)
            and config.get("max_subject_length") >= 0
            and isinstance(config.get("allow_empty_subject"), bool)
        )
        subject_valid = isinstance(subject, str)
        if subject_valid and not subject:
            subject_valid = subject_config_valid and config["allow_empty_subject"]
        if subject_valid and subject_config_valid:
            subject_valid = (
                len(subject) <= config["max_subject_length"]
                and "\r" not in subject
                and "\n" not in subject
            )
        if not subject_valid or not subject_config_valid:
            errors.append("subject")

        headers_valid = isinstance(headers, dict)
        if headers_valid:
            for name, value in headers.items():
                if (
                    not isinstance(name, str)
                    or not name
                    or _HEADER_NAME_RE.fullmatch(name) is None
                    or not isinstance(value, str)
                    or not value
                    or "\r" in name
                    or "\n" in name
                    or "\r" in value
                    or "\n" in value
                ):
                    headers_valid = False
                    break
        if not headers_valid:
            errors.append("headers")

        unique_errors = list(dict.fromkeys(errors))
        return {"valid": not unique_errors, "errors": unique_errors}
    except BaseException:
        return {"valid": False, "errors": ["sender", "recipients", "subject", "headers"]}