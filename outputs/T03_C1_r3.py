import re

def validate_email_headers(sender, recipients, subject, headers, config) -> dict:
    errors = []
    
    def is_valid_email(email):
        try:
            if not isinstance(email, str) or len(email) == 0:
                return False
            pattern = r'^[^@]+@[^@]+\.[^@]+$'
            return re.match(pattern, email) is not None
        except:
            return False
    
    try:
        if not isinstance(config, dict):
            return {"valid": False, "errors": ["sender", "recipients", "subject", "headers"]}
        
        max_recipients = config.get("max_recipients")
        max_subject_length = config.get("max_subject_length")
        allow_empty_subject = config.get("allow_empty_subject")
        
        if (max_recipients is None or max_subject_length is None or allow_empty_subject is None):
            return {"valid": False, "errors": ["sender", "recipients", "subject", "headers"]}
        
        if (not isinstance(max_recipients, int) or not isinstance(max_subject_length, int) or 
            not isinstance(allow_empty_subject, bool)):
            return {"valid": False, "errors": ["sender", "recipients", "subject", "headers"]}
    except:
        return {"valid": False, "errors": ["sender", "recipients", "subject", "headers"]}
    
    if not is_valid_email(sender):
        errors.append("sender")
    
    recipients_valid = False
    try:
        if isinstance(recipients, list) and len(recipients) <= max_recipients:
            if all(is_valid_email(r) for r in recipients):
                recipients_valid = True
    except:
        pass
    if not recipients_valid:
        errors.append("recipients")
    
    subject_valid = False
    try:
        if isinstance(subject, str) and len(subject) <= max_subject_length:
            if allow_empty_subject or len(subject) > 0:
                subject_valid = True
    except:
        pass
    if not subject_valid:
        errors.append("subject")
    
    headers_valid = False
    try:
        if isinstance(headers, dict):
            if all(isinstance(k, str) and isinstance(v, str) for k, v in headers.items()):
                headers_valid = True
    except:
        pass
    if not headers_valid:
        errors.append("headers")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
