import re

def validate_email_headers(sender, recipients, subject, headers, config) -> dict:
    errors = []
    
    def is_valid_email(email):
        try:
            if not isinstance(email, str):
                return False
            if email.count('@') != 1:
                return False
            local, domain = email.rsplit('@', 1)
            if not local or not domain:
                return False
            if domain != 'localhost' and '.' not in domain:
                return False
            return True
        except:
            return False
    
    # Validate sender
    if not is_valid_email(sender):
        errors.append("sender")
    
    # Validate recipients
    try:
        if not isinstance(recipients, list):
            errors.append("recipients")
        else:
            max_recipients = config.get("max_recipients", float('inf'))
            if len(recipients) > max_recipients:
                errors.append("recipients")
            else:
                for recipient in recipients:
                    if not is_valid_email(recipient):
                        errors.append("recipients")
                        break
    except:
        errors.append("recipients")
    
    # Validate subject
    try:
        if not isinstance(subject, str):
            errors.append("subject")
        else:
            max_length = config.get("max_subject_length", float('inf'))
            allow_empty = config.get("allow_empty_subject", True)
            
            if not allow_empty and subject == "":
                errors.append("subject")
            elif len(subject) > max_length:
                errors.append("subject")
    except:
        errors.append("subject")
    
    # Validate headers
    try:
        if not isinstance(headers, dict):
            errors.append("headers")
        else:
            for key, value in headers.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    errors.append("headers")
                    break
                if not re.match(r'^[A-Za-z0-9\-_]+$', key):
                    errors.append("headers")
                    break
    except:
        errors.append("headers")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
