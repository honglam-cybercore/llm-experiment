import re
from typing import Dict, List, Any

def validate_email_headers(sender, recipients, subject, headers, config) -> dict:
    """
    Validate email sender, recipients, subject, and custom headers.
    
    Returns a dict with 'valid' (bool) and 'errors' (list of str).
    """
    errors = []
    
    # Handle None or invalid config - use defaults
    if not isinstance(config, dict):
        config = {}
    
    # Extract config values with defaults and type validation
    max_recipients = config.get("max_recipients", 100)
    if not isinstance(max_recipients, int) or max_recipients <= 0:
        max_recipients = 100
    
    max_subject_length = config.get("max_subject_length", 256)
    if not isinstance(max_subject_length, int) or max_subject_length <= 0:
        max_subject_length = 256
    
    allow_empty_subject = config.get("allow_empty_subject", False)
    if not isinstance(allow_empty_subject, bool):
        allow_empty_subject = False
    
    # Validate sender
    if not _is_valid_email(sender):
        errors.append("sender")
    
    # Validate recipients
    if not _is_valid_recipients(recipients, max_recipients):
        errors.append("recipients")
    
    # Validate subject
    if not _is_valid_subject(subject, max_subject_length, allow_empty_subject):
        errors.append("subject")
    
    # Validate headers
    if not _is_valid_headers(headers):
        errors.append("headers")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def _is_valid_email(email) -> bool:
    """Check if email address is valid."""
    if not isinstance(email, str):
        return False
    if not email or not email.strip():
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def _is_valid_recipients(recipients, max_recipients: int) -> bool:
    """Check if recipients list is valid."""
    if not isinstance(recipients, list):
        return False
    
    if not recipients:
        return False
    
    if len(recipients) > max_recipients:
        return False
    
    for recipient in recipients:
        if not _is_valid_email(recipient):
            return False
    
    return True


def _is_valid_subject(subject, max_length: int, allow_empty: bool) -> bool:
    """Check if subject is valid."""
    if not isinstance(subject, str):
        return False
    
    if not subject and not allow_empty:
        return False
    
    if len(subject) > max_length:
        return False
    
    return True


def _is_valid_headers(headers) -> bool:
    """Check if headers dict is valid."""
    if not isinstance(headers, dict):
        return False
    
    for name, value in headers.items():
        if not isinstance(name, str):
            return False
        
        if not isinstance(value, str):
            return False
        
        if '\n' in name or '\r' in name or ':' in name:
            return False
        
        if '\n' in value or '\r' in value:
            return False
    
    return True
