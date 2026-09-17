def validate_email_headers(sender, recipients, subject, headers, config) -> dict:
    if not isinstance(config, dict):
        config = {}
    
    errors = []
    
    if not _is_valid_email(sender):
        errors.append("sender")
    
    if not _are_valid_recipients(recipients, config):
        errors.append("recipients")
    
    if not _is_valid_subject(subject, config):
        errors.append("subject")
    
    if not _are_valid_headers(headers):
        errors.append("headers")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def _is_valid_email(email):
    if not isinstance(email, str):
        return False
    email_stripped = email.strip()
    if not email_stripped or email_stripped.count('@') != 1:
        return False
    local, domain = email_stripped.split('@')
    if not local or not domain or '.' not in domain:
        return False
    return True


def _are_valid_recipients(recipients, config):
    if not isinstance(recipients, list):
        return False
    if len(recipients) == 0:
        return False
    max_recipients = config.get("max_recipients", float('inf'))
    if len(recipients) > max_recipients:
        return False
    for recipient in recipients:
        if not _is_valid_email(recipient):
            return False
    return True


def _is_valid_subject(subject, config):
    if not isinstance(subject, str):
        return False
    allow_empty = config.get("allow_empty_subject", False)
    if not allow_empty and not subject.strip():
        return False
    max_length = config.get("max_subject_length", float('inf'))
    if len(subject) > max_length:
        return False
    return True


def _are_valid_headers(headers):
    if not isinstance(headers, dict):
        return False
    for header_name, header_value in headers.items():
        if not isinstance(header_name, str) or not isinstance(header_value, str):
            return False
        if '\r' in header_name or '\n' in header_name:
            return False
        if '\r' in header_value or '\n' in header_value:
            return False
    return True
