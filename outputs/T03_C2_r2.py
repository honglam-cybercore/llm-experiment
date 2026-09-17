def validate_email_headers(sender, recipients, subject, headers, config) -> dict:
    errors = []
    
    try:
        if not isinstance(config, dict):
            return {"valid": False, "errors": ["sender", "recipients", "subject", "headers"]}
        
        max_recipients = config.get("max_recipients", 0)
        max_subject_length = config.get("max_subject_length", 0)
        allow_empty_subject = config.get("allow_empty_subject", False)
        
        if not _is_valid_email(sender):
            errors.append("sender")
        
        if not _is_valid_recipients(recipients, max_recipients):
            errors.append("recipients")
        
        if not _is_valid_subject(subject, max_subject_length, allow_empty_subject):
            errors.append("subject")
        
        if not _is_valid_headers(headers):
            errors.append("headers")
    except Exception:
        return {"valid": False, "errors": ["sender", "recipients", "subject", "headers"]}
    
    return {"valid": len(errors) == 0, "errors": errors}


def _is_valid_email(email):
    if not isinstance(email, str) or not email:
        return False
    
    if '@' not in email:
        return False
    
    parts = email.split('@')
    if len(parts) != 2:
        return False
    
    local, domain = parts
    if not local or not domain:
        return False
    
    if '.' not in domain:
        return False
    
    if '\r' in email or '\n' in email:
        return False
    
    return True


def _is_valid_recipients(recipients, max_recipients):
    if not isinstance(recipients, list):
        return False
    
    if max_recipients > 0 and len(recipients) > max_recipients:
        return False
    
    for recipient in recipients:
        if not _is_valid_email(recipient):
            return False
    
    return True


def _is_valid_subject(subject, max_subject_length, allow_empty_subject):
    if not isinstance(subject, str):
        return False
    
    if not subject and not allow_empty_subject:
        return False
    
    if max_subject_length > 0 and len(subject) > max_subject_length:
        return False
    
    if '\r' in subject or '\n' in subject:
        return False
    
    return True


def _is_valid_headers(headers):
    if not isinstance(headers, dict):
        return False
    
    for name, value in headers.items():
        if not isinstance(name, str) or not isinstance(value, str):
            return False
        
        if not name:
            return False
        
        if '\r' in name or '\n' in name or '\r' in value or '\n' in value:
            return False
    
    return True
