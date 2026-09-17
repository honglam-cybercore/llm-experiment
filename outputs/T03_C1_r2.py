import re

def validate_email_headers(sender, recipients, subject, headers, config) -> dict:
    errors = []
    
    if not _is_valid_email(sender):
        errors.append("sender")
    
    if not _is_valid_recipients(recipients, config):
        errors.append("recipients")
    
    if not _is_valid_subject(subject, config):
        errors.append("subject")
    
    if not _is_valid_headers(headers):
        errors.append("headers")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def _is_valid_email(email):
    try:
        if not isinstance(email, str) or not email:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    except:
        return False


def _is_valid_recipients(recipients, config):
    try:
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
    except:
        return False


def _is_valid_subject(subject, config):
    try:
        if not isinstance(subject, str):
            return False
        max_subject_length = config.get("max_subject_length", float('inf'))
        if len(subject) > max_subject_length:
            return False
        allow_empty_subject = config.get("allow_empty_subject", False)
        if not allow_empty_subject and not subject:
            return False
        return True
    except:
        return False


def _is_valid_headers(headers):
    try:
        if not isinstance(headers, dict):
            return False
        header_name_pattern = r'^[a-zA-Z0-9-]+$'
        for key, value in headers.items():
            if not isinstance(key, str) or not isinstance(value, str):
                return False
            if not re.match(header_name_pattern, key):
                return False
        return True
    except:
        return False
