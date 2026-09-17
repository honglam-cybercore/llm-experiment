import re

_ADDRESS_RE = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)*"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$"
)
_HEADER_NAME_RE = re.compile(r"^[!-9;-~]+$")


def _valid_address(value):
    if type(value) is not str or not value or len(value) > 254:
        return False
    if "\r" in value or "\n" in value or "\x00" in value:
        return False
    if value.count("@") != 1:
        return False

    local, domain = value.rsplit("@", 1)
    if not local or len(local) > 64 or len(domain) > 253:
        return False
    if local.startswith(".") or local.endswith(".") or ".." in local:
        return False

    return bool(_ADDRESS_RE.fullmatch(value))


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

        if not config_valid:
            return {"valid": False, "errors": ["recipients", "subject"]}

        if not _valid_address(sender):
            errors.append("sender")

        recipients_valid = (
            type(recipients) is list
            and len(recipients) > 0
            and len(recipients) <= config["max_recipients"]
            and all(_valid_address(address) for address in recipients)
        )
        if not recipients_valid:
            errors.append("recipients")

        subject_valid = (
            type(subject) is str
            and (config["allow_empty_subject"] or bool(subject))
            and len(subject) <= config["max_subject_length"]
            and "\r" not in subject
            and "\n" not in subject
            and "\x00" not in subject
        )
        if not subject_valid:
            errors.append("subject")

        headers_valid = (
            type(headers) is dict
            and all(
                type(name) is str
                and bool(name)
                and bool(_HEADER_NAME_RE.fullmatch(name))
                and type(value) is str
                and "\r" not in value
                and "\n" not in value
                and "\x00" not in value
                for name, value in headers.items()
            )
        )
        if not headers_valid:
            errors.append("headers")

        return {"valid": not errors, "errors": errors}
    except BaseException:
        return {
            "valid": False,
            "errors": ["sender", "recipients", "subject", "headers"],
        }