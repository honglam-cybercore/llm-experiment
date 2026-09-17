def validate_email_headers(sender, recipients, subject, headers, config) -> dict:
    """Validate email sender, recipients, subject, and headers."""
    errors = []
    
    def is_valid_email(email):
        """Check if email has basic valid structure."""
        try:
            if not isinstance(email, str):
                return False
            email = email.strip()
            if not email:
                return False
            if '@' not in email:
                return False
            parts = email.split('@')
            if len(parts) != 2:
                return False
            local_part, domain = parts
            if not local_part.strip() or not domain.strip():
                return False
            if '.' not in domain:
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
            max_recipients = config.get("max_recipients") if isinstance(config, dict) else None
            if max_recipients is not None and len(recipients) > max_recipients:
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
            config_dict = config if isinstance(config, dict) else {}
            max_length = config_dict.get("max_subject_length")
            allow_empty = config_dict.get("allow_empty_subject", False)
            
            if len(subject) == 0 and not allow_empty:
                errors.append("subject")
            elif max_length is not None and len(subject) > max_length:
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
                if '\r' in key or '\n' in key or '\r' in value or '\n' in value:
                    errors.append("headers")
                    break
    except:
        errors.append("headers")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
