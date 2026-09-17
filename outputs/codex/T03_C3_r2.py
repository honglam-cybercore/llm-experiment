import re
from email.utils import parseaddr

_FIELD_NAME_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
_LOCAL_PART_RE = re.compile(r"^[!#$%&'*+\-/=?^_`{|}~0-9A-Za-z.]+$")
_DOMAIN_LABEL_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")

_PROTECTED_HEADERS = {
    "bcc",
    "cc",
    "content-disposition",
    "content-transfer-encoding",
    "content-type",
    "date",
    "from",
    "in-reply-to",
    "message-id",
    "mime-version",
    "reply-to",
    "resent-bcc",
    "resent-cc",
    "resent-date",
    "resent-from",
    "resent-message-id",
    "resent-reply-to",
    "resent-sender",
    "resent-to",
    "sender",
    "subject",
    "to",
}


def _valid_email_address(value):
    if type(value) is not str or not value or len(value) > 254:
        return False

    if any(ord(char) < 32 or ord(char) == 127 or char.isspace() for char in value):
        return False

    if value.count("@") != 1:
        return False

    parsed_name, parsed_address = parseaddr(value)
    if parsed_name or parsed_address != value:
        return False

    local, domain = value.rsplit("@", 1)

    if not local or len(local) > 64 or local.startswith(".") or local.endswith("."):
        return False
    if ".." in local or not _LOCAL_PART_RE.fullmatch(local):
        return False

    if not domain or len(domain) > 253 or domain.startswith(".") or domain.endswith("."):
        return False

    labels = domain.split(".")
    if any(not label or len(label) > 63 or not _DOMAIN_LABEL_RE.fullmatch(label)
           for label in labels):
        return False

    return True


def _valid_text(value, allow_empty=True):
    if type(value) is not str or (not allow_empty and not value):
        return False

    for char in value:
        code = ord(char)
        if code in (10, 13) or code < 32 or code == 127:
            return False

    return True


def validate_email_headers(sender, recipients, subject, headers, config) -> dict:
    errors = []

    try:
        config_valid = (
            type(config) is dict
            and type(config.get("max_recipients")) is int
            and config["max_recipients"] >= 1
            and type(config.get("max_subject_length")) is int
            and config["max_subject_length"] >= 0
            and type(config.get("allow_empty_subject")) is bool
        )

        sender_valid = _valid_email_address(sender)

        recipients_valid = (
            type(recipients) is list
            and bool(recipients)
            and all(_valid_email_address(address) for address in recipients)
        )
        if config_valid and type(recipients) is list:
            recipients_valid = recipients_valid and len(recipients) <= config["max_recipients"]
        elif not config_valid:
            recipients_valid = False

        subject_valid = _valid_text(subject)
        if config_valid and type(subject) is str:
            subject_valid = (
                subject_valid
                and len(subject) <= config["max_subject_length"]
                and (config["allow_empty_subject"] or bool(subject))
            )
        elif not config_valid:
            subject_valid = False

        headers_valid = type(headers) is dict
        if headers_valid:
            for name, value in headers.items():
                if (
                    type(name) is not str
                    or not name
                    or not _FIELD_NAME_RE.fullmatch(name)
                    or name.lower() in _PROTECTED_HEADERS
                    or type(value) is not str
                    or not _valid_text(value)
                ):
                    headers_valid = False
                    break

        if not sender_valid:
            errors.append("sender")
        if not recipients_valid:
            errors.append("recipients")
        if not subject_valid:
            errors.append("subject")
        if not headers_valid:
            errors.append("headers")

    except Exception:
        return {"valid": False, "errors": ["sender", "recipients", "subject", "headers"]}

    return {"valid": not errors, "errors": errors}