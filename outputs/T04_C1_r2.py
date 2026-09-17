from datetime import datetime

def validate_booking(start, end, rules) -> dict:
    try:
        # Parse dates
        start_date = datetime.fromisoformat(start).date()
        end_date = datetime.fromisoformat(end).date()
        
        # Check if booking range is valid
        if start_date >= end_date:
            return {"valid": False, "errors": ["range"]}
        
        # Parse rules
        allowed_start = datetime.fromisoformat(rules["allowed_start"]).date()
        allowed_end = datetime.fromisoformat(rules["allowed_end"]).date()
        blocked_periods = rules["blocked_periods"]
        max_duration_days = rules["max_duration_days"]
        
    except (ValueError, TypeError, KeyError, AttributeError):
        return {"valid": False, "errors": ["range"]}
    
    errors = []
    
    # Check if booking is within allowed period
    if start_date < allowed_start or end_date > allowed_end:
        errors.append("allowed_period")
    
    # Check for overlaps with blocked periods
    try:
        for blocked_start_str, blocked_end_str in blocked_periods:
            blocked_start = datetime.fromisoformat(blocked_start_str).date()
            blocked_end = datetime.fromisoformat(blocked_end_str).date()
            # Period [s1, e1) overlaps with [s2, e2) if s1 < e2 and e1 > s2
            if start_date < blocked_end and end_date > blocked_start:
                errors.append("blocked_period")
                break
    except (ValueError, TypeError, KeyError, AttributeError, IndexError):
        return {"valid": False, "errors": ["range"]}
    
    # Check if duration is within limits
    try:
        duration = (end_date - start_date).days
        if duration > max_duration_days:
            errors.append("duration")
    except TypeError:
        return {"valid": False, "errors": ["range"]}
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
