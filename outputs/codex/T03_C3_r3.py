import re

_ATOM_RE = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+$")
_DOMAIN_LABEL_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")
_HEADER_NAME_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")


def _valid_address(value):
    if type(value) is not str or not value or len(value) > 254:
        return False

    if any(ord(char) < 33 or ord(char) == 127 for char in value):
        return False

    if value.count("@") != 1:
        return False

    local, domain = value.rsplit("@", 1)

    if not local or len(local) > 64 or not _ATOM_RE.fullmatch(local):
        return False
    if local.startswith(".") or local.endswith(".") or ".." in local:
        return False

    if domain.startswith("[") and domain.endswith("]"):
        literal = domain[1:-1]
        if not literal or any(
            char not in "0123456789abcdefABCDEF:."
            for char in literal
        ):
            return False
        return len(domain) <= 255

    try:
        ascii_domain = domain.encode("idna").decode("ascii")
    except Exception:
        return False

    if len(ascii_domain) > 253 or not ascii_domain or ascii_domain.endswith("."):
        return False

    labels = ascii_domain.split(".")
    return all(_DOMAIN_LABEL_RE.fullmatch(label) for label in labels)


def _has_header_injection(value):
    return any(ord(char) < 32 or ord(char) == 127 for char in value)


def validate_email_headers(sender, recipients, subject, headers, config) -> dict:
    try:
        errors = []

        if not _valid_address(sender):
            errors.append("sender")

        config_valid = type(config) is dict
        max_recipients = None
        max_subject_length = None
        allow_empty_subject = None

        if config_valid:
            max_recipients = config.get("max_recipients")
            max_subject_length = config.get("max_subject_length")
            allow_empty_subject = config.get("allow_empty_subject")

            if (
                type(max_recipients) is not int
                or max_recipients < 1
            ):
                errors.append("recipients")

            if (
                type(max_subject_length) is not int
                or max_subject_length < 0
                or type(allow_empty_subject) is not bool
            ):
                errors.append("subject")
        else:
            errors.extend(("recipients", "subject"))

        if type(recipients) is not list:
            if "recipients" not in errors:
                errors.append("recipients")
        elif (
            max_recipients is not None
            and type(max_recipients) is int
            and (
                not recipients
                or len(recipients) > max_recipients
                or any(not _valid_address(address) for address in recipients)
            )
        ):
            if "recipients" not in errors:
                errors.append("recipients")

        if type(subject) is not str:
            if "subject" not in errors:
                errors.append("subject")
        elif (
            _has_header_injection(subject)
            or (
                max_subject_length is not None
                and type(max_subject_length) is int
                and len(subject) > max_subject_length
            )
            or (
                subject == ""
                and type(allow_empty_subject) is bool
                and not allow_empty_subject
            )
        ):
            if "subject" not in errors:
                errors.append("subject")

        if type(headers) is not dict:
            errors.append("headers")
        else:
            headers_valid = True
            for name, value in headers.items():
                if (
                    type(name) is not str
                    or not name
                    or len(name) >  дов 998
                ):
                    headers_valid = False
                    break
                try:
                    if not name.isascii() or not _HEADER_NAME_RE.fullmatch(name):
                        headers_valid = False
                        break
                except Exception:
                    headers_valid = False
                    break

                if type(value) is not str or _has_header_injection(value):
                    headers_valid = False
                    break

            if not headers_valid:
                errors.append("headers")

        unique_errors = list(dict.fromkeys(errors))
        return {"valid": not unique_errors, "errors": unique_errors}
    except BaseException:
        return {
            "valid": False,
            "errors": ["sender", "recipients", "subject", "headers"],
        }