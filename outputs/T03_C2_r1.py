def validate_email_headers(sender, recipients, subject, headers, config) -> dict:
    errors = []
    
    try:
        if not _validate_email_address(sender):
            errors.append("sender")
        
        if not _validate_recipients(recipients, config.get("max_recipients", 0)):
            errors.append("recipients")
        
        if not _validate_subject(subject, config):
            errors.append("subject")
        
        if not _validate_headers(headers):
            errors.append("headers")
    except Exception:
        return {"valid": False, "errors": ["sender", "recipients", "subject", "headers"]}
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def _validate_email_address(address):
    if not isinstance(address, str) or not address:
        return False
    
    parts = address.split("@")
    if len(parts) != 2:
        return False
    
    local, domain = parts
    return bool(local and domain)


def _validate_recipients(recipients, max_recipients):
    if not isinstance(recipients, (list, tuple)):
        return False
    
    if len(recipients) == 0:
        return False
    
    if max_recipients > 0 and len(recipients) > max_recipients:
        return False
    
    return all(_validate_email_address(recipient) for recipient in recipients)


def _validate_subject(subject, config):
    if not isinstance(subject, str):
        return False
    
    allow_empty = config.get("allow_empty_subject", False)
    if not subject and not allow_empty:
        return False
    
    max_length = config.get("max_subject_length", float('inf'))
    if len(subject) > max_length:
        return False
    
    return True


def _validate_headers(headers):
    if not isinstance(headers, dict):
        return False
    
    for name, value in headers.items():
        if not isinstance(name, str) or not isinstance(value, str):
            return False
        if '\r' in name or '\n' in name or '\r' in value or '\n' in value:
            return False
    
    return True
