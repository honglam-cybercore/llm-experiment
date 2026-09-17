import re

def validate_email_headers(sender, recipients, subject, headers, config) -> dict:
    try:
        errors = []
        
        if not isinstance(config, dict):
            return {
                "valid": False,
                "errors": ["sender", "recipients", "subject", "headers"]
            }
        
        max_recipients = config.get("max_recipients", 0)
        max_subject_length = config.get("max_subject_length", 0)
        allow_empty_subject = config.get("allow_empty_subject", False)
        
        if not isinstance(max_recipients, int) or max_recipients < 0:
            return {
                "valid": False,
                "errors": ["sender", "recipients", "subject", "headers"]
            }
        if not isinstance(max_subject_length, int) or max_subject_length < 0:
            return {
                "valid": False,
                "errors": ["sender", "recipients", "subject", "headers"]
            }
        if not isinstance(allow_empty_subject, bool):
            return {
                "valid": False,
                "errors": ["sender", "recipients", "subject", "headers"]
            }
        
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
    except Exception:
        return {
            "valid": False,
            "errors": ["sender", "recipients", "subject", "headers"]
        }


def _is_valid_email(email):
    if not isinstance(email, str) or not email:
        return False
    pattern = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'
    return bool(re.match(pattern, email))


def _validate_recipients(recipients, max_recipients):
    if not isinstance(recipients, list):
        return False
    if len(recipients) == 0:
        return False
    if max_recipients > 0 and len(recipients) > max_recipients:
        return False
    for recipient in recipients:
        if not _is_valid_email(recipient):
            return False
    return True


def _validate_subject(subject, max_subject_length, allow_empty_subject):
    if not isinstance(subject, str):
        return False
    if not allow_empty_subject and not subject.strip():
        return False
    if max_subject_length > 0 and len(subject) > max_subject_length:
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
