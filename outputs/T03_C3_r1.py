import re

def validate_email_headers(sender, recipients, subject, headers, config) -> dict:
    errors = []
    
    # Validate and extract config
    try:
        if not isinstance(config, dict):
            return {"valid": False, "errors": ["config"]}
        
        max_recipients = config.get("max_recipients")
        max_subject_length = config.get("max_subject_length")
        allow_empty_subject = config.get("allow_empty_subject")
        
        if not isinstance(max_recipients, int) or max_recipients <= 0:
            return {"valid": False, "errors": ["config"]}
        if not isinstance(max_subject_length, int) or max_subject_length < 0:
            return {"valid": False, "errors": ["config"]}
        if not isinstance(allow_empty_subject, bool):
            return {"valid": False, "errors": ["config"]}
    except (AttributeError, TypeError):
        return {"valid": False, "errors": ["config"]}
    
    # Email validation regex
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    def is_valid_email(email):
        """Validate email address format"""
        if not isinstance(email, str) or not email:
            return False
        # Reject emails with consecutive dots or control characters
        if '..' in email or '\r' in email or '\n' in email:
            return False
        return re.match(email_regex, email) is not None
    
    def has_header_injection(value):
        """Check for CRLF header injection attempts"""
        if not isinstance(value, str):
            return True
        return '\r' in value or '\n' in value
    
    # Validate sender
    if not is_valid_email(sender):
        errors.append("sender")
    
    # Validate recipients
    recipient_valid = True
    if not isinstance(recipients, list):
        recipient_valid = False
    elif len(recipients) == 0:
        recipient_valid = False
    elif len(recipients) > max_recipients:
        recipient_valid = False
    else:
        for recipient in recipients:
            if not is_valid_email(recipient):
                recipient_valid = False
                break
    
    if not recipient_valid:
        errors.append("recipients")
    
    # Validate subject
    subject_valid = True
    if not isinstance(subject, str):
        subject_valid = False
    elif not allow_empty_subject and not subject:
        subject_valid = False
    elif len(subject) > max_subject_length:
        subject_valid = False
    elif has_header_injection(subject):
        subject_valid = False
    
    if not subject_valid:
        errors.append("subject")
    
    # Validate headers
    headers_valid = True
    if headers is not None:
        if not isinstance(headers, dict):
            headers_valid = False
        else:
            for key, value in headers.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    headers_valid = False
                    break
                if has_header_injection(key) or has_header_injection(value):
                    headers_valid = False
                    break
    
    if not headers_valid:
        errors.append("headers")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
