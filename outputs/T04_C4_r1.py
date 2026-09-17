from datetime import datetime

def validate_booking(start, end, rules) -> dict:
    # Validate input types
    if not isinstance(start, str) or not isinstance(end, str):
        return {"valid": False, "errors": ["range"]}
    
    if not isinstance(rules, dict):
        return {"valid": False, "errors": ["range"]}
    
    # Parse booking dates
    try:
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        end_date = datetime.strptime(end, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return {"valid": False, "errors": ["range"]}
    
    # Parse allowed period
    try:
        allowed_start_str = rules.get("allowed_start")
        allowed_end_str = rules.get("allowed_end")
        if not isinstance(allowed_start_str, str) or not isinstance(allowed_end_str, str):
            raise ValueError("Invalid type")
        allowed_start = datetime.strptime(allowed_start_str, "%Y-%m-%d").date()
        allowed_end = datetime.strptime(allowed_end_str, "%Y-%m-%d").date()
    except (ValueError, TypeError, AttributeError):
        return {"valid": False, "errors": ["range"]}
    
    # Parse max_duration_days
    try:
        max_duration = rules.get("max_duration_days")
        if max_duration is None:
            raise ValueError("max_duration_days missing")
        max_duration = int(max_duration)
        if max_duration < 0:
            raise ValueError("max_duration_days negative")
    except (ValueError, TypeError):
        return {"valid": False, "errors": ["range"]}
    
    # Parse blocked periods
    try:
        blocked_periods = rules.get("blocked_periods", [])
        if not isinstance(blocked_periods, list):
            raise ValueError("blocked_periods not a list")
        blocked_dates = []
        for period in blocked_periods:
            if not isinstance(period, (list, tuple)) or len(period) != 2:
                raise ValueError("Invalid period format")
            blocked_start = datetime.strptime(period[0], "%Y-%m-%d").date()
            blocked_end = datetime.strptime(period[1], "%Y-%m-%d").date()
            blocked_dates.append((blocked_start, blocked_end))
    except (ValueError, TypeError, IndexError, AttributeError):
        return {"valid": False, "errors": ["range"]}
    
    # Collect validation errors
    errors = []
    
    # Check start < end
    if start_date >= end_date:
        errors.append("range")
    
    # Check booking is within allowed period [allowed_start, allowed_end)
    if start_date < allowed_start or end_date > allowed_end:
        errors.append("allowed_period")
    
    # Check duration
    duration = (end_date - start_date).days
    if duration > max_duration:
        errors.append("duration")
    
    # Check for overlaps with blocked periods
    for blocked_start, blocked_end in blocked_dates:
        if start_date < blocked_end and blocked_start < end_date:
            errors.append("blocked_period")
            break
    
    return {"valid": len(errors) == 0, "errors": errors}
