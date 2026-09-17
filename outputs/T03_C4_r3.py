def validate_email_headers(sender, recipients, subject, headers, config) -> dict:
    errors = []
    
    try:
        max_recipients = config.get("max_recipients", 0) if isinstance(config, dict) else 0
        max_subject_length = config.get("max_subject_length", 0) if isinstance(config, dict) else 0
        allow_empty_subject = config.get("allow_empty_subject", False) if isinstance(config, dict) else False
    except:
        max_recipients = 0
        max_subject_length = 0
        allow_empty_subject = False
    
    if not _is_valid_email(sender):
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


def _is_valid_email(email):
    try:
        if not isinstance(email, str) or not email:
            return False
        
        if email.count('@') != 1:
            return False
        
        local, domain = email.split('@')
        
        if not local or not domain:
            return False
        
        if '.' not in domain:
            return False
        
        if any(c.isspace() or ord(c) < 32 for c in email):
            return False
        
        return True
    except:
        return False


def _validate_recipients(recipients, max_recipients):
    try:
        if not isinstance(recipients, list):
            return False
        
        if not recipients:
            return False
        
        if max_recipients > 0 and len(recipients) > max_recipients:
            return False
        
        for recipient in recipients:
            if not _is_valid_email(recipient):
                return False
        
        return True
    except:
        return False


def _validate_subject(subject, max_length, allow_empty):
    try:
        if not isinstance(subject, str):
            return False
        
        if not subject and not allow_empty:
            return False
        
        if max_length > 0 and len(subject) > max_length:
            return False
        
        return True
    except:
        return False


def _validate_headers(headers):
    try:
        if not isinstance(headers, dict):
            return False
        
        for name, value in headers.items():
            if not isinstance(name, str) or not isinstance(value, str):
                return False
            
            if '\r' in name or '\n' in name or '\r' in value or '\n' in value:
                return False
        
        return True
    except:
        return False
