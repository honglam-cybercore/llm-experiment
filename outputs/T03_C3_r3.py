import re

def validate_email_headers(sender, recipients, subject, headers, config) -> dict:
    errors = []
    
    if not isinstance(config, dict):
        config = {}
    max_recipients = config.get("max_recipients", 100)
    max_subject_length = config.get("max_subject_length", 255)
    allow_empty_subject = config.get("allow_empty_subject", False)
    
    if not _validate_sender(sender):
        errors.append("sender")
    
    if not _validate_recipients(recipients, max_recipients):
        errors.append("recipients")
    
    if not _validate_subject(subject, max_subject_length, allow_empty_subject):
        errors.append("subject")
    
    if not _validate_headers(headers):
        errors.append("headers")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def _validate_sender(sender):
    if not isinstance(sender, str):
        return False
    if not sender or len(sender) > 254:
        return False
    if '\r' in sender or '\n' in sender or '\0' in sender:
        return False
    return _is_valid_email(sender)


def _validate_recipients(recipients, max_recipients):
    if not isinstance(recipients, list):
        return False
    if not recipients or len(recipients) > max_recipients:
        return False
    
    for recipient in recipients:
        if not isinstance(recipient, str):
            return False
        if not recipient or len(recipient) > 254:
            return False
        if '\r' in recipient or '\n' in recipient or '\0' in recipient:
            return False
        if not _is_valid_email(recipient):
            return False
    
    return True


def _validate_subject(subject, max_length, allow_empty):
    if not isinstance(subject, str):
        return False
    if not allow_empty and not subject:
        return False
    if len(subject) > max_length:
        return False
    if '\r' in subject or '\n' in subject or '\0' in subject:
        return False
    return True


def _validate_headers(headers):
    if not isinstance(headers, dict):
        return False
    
    for name, value in headers.items():
        if not isinstance(name, str) or not isinstance(value, str):
            return False
        
        if not name:
            return False
        if not re.match(r'^[A-Za-z0-9\-]+$', name):
            return False
        if '\r' in name or '\n' in name or '\0' in name:
            return False
        
        if '\r' in value or '\n' in value or '\0' in value:
            return False
    
    return True


def _is_valid_email(email):
    pattern = r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
    return bool(re.match(pattern, email))
