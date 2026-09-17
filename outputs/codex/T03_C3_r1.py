import re

_TOKEN_CHARS = frozenset("!#$%&'*+-.^_`|~0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
_ATOM_CHARS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&'*+-/=?^_`{|}~.")
_EMAIL_MAX_LENGTH = 254
_LOCAL_MAX_LENGTH = 64
_DOMAIN_MAX_LENGTH = 253


def _is_valid_email(value):
    if type(value) is not str:
        return False
    if not value or len(value) > _EMAIL_MAX_LENGTH:
        return False
    if any(ord(char) < 33 or ord(char) > 126 for char in value):
        return False
    if value.count("@") != 1:
        return False

    local, domain = value.rsplit("@", 1)

    if not local or len(local) > _LOCAL_MAX_LENGTH:
        return False
    if not domain or len(domain) > _DOMAIN_MAX_LENGTH:
        return False
    if local.startswith(".") or local.endswith(".") or ".." in local:
        return False
    if any(char not in _ATOM_CHARS for char in local):
        return False
    if domain.startswith(".") or domain.endswith(".") or ".." in domain:
        return False

    labels = domain.split(".")
    if any(
        not label
        or len(label) > 63
        or label.startswith("-")
        or label.endswith("-")
        or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-" for char in label)
        for label in labels
    ):
        return False

    return True


def _contains_invalid_header_text(value):
    return any(
        ord(char) < 32 and char != "\t" or ord(char) == 127
        for char in value
    )


def validate_email_headers(sender, recipients, subject, headers, config) -> dict:
    try:
        errors = []

        config_valid = (
            type(config) is dict
            and type(config.get("max_recipients")) is int
            and config["max_recipients"] >= 0
            and type(config.get("max_subject_length")) is int
            and config["max_subject_length"] >= 0
            and type(config.get("allow_empty_subject")) is bool
        )

        sender_valid = _is_valid_email(sender)

        recipients_valid = (
            type(recipients) is list
            and config_valid
            and len(recipients) <= config["max_recipients"]
            and all(_is_valid_email(recipient) for recipient in recipients)
        )

        subject_valid = (
            type(subject) is str
            and config_valid
            and len(subject) <= config["max_subject_length"]
            and (config["allow_empty_subject"] or bool(subject))
            and not _contains_invalid_header_text(subject)
            and "\r" not in subject
            and "\n" not in subject
        )

        headers_valid = (
            type(headers) is dict
            and all(
                type(name) is str
                and bool(name)
                and all(char in _TOKEN_CHARS for char in name)
                and type(value) is str
                and "\r" not in value
                and "\n" not in value
                and not _contains_invalid_header_text(value)
                for name, value in headers.items()
            )
        )

        if not sender_valid:
            errors.append("sender")
        if not recipients_valid:
            errors.append("recipients")
        if not subject_valid:
            errors.append("subject")
        if not headers_valid:
            errors.append("headers")

        return {"valid": not errors, "errors": errors}
    except BaseException:
        return {
            "valid": False,
            "errors": ["sender", "recipients", "subject", "headers"],
        }