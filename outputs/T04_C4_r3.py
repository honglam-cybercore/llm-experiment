from datetime import datetime

def validate_booking(start, end, rules) -> dict:
    errors = []
    start_date = None
    end_date = None
    
    try:
        if not isinstance(start, str):
            errors.append("range")
        else:
            start_date = datetime.fromisoformat(start).date()
    except (ValueError, TypeError, AttributeError):
        errors.append("range")
    
    try:
        if not isinstance(end, str):
            errors.append("range")
        else:
            end_date = datetime.fromisoformat(end).date()
    except (ValueError, TypeError, AttributeError):
        errors.append("range")
    
    if "range" in errors:
        return {"valid": False, "errors": errors}
    
    if not isinstance(rules, dict):
        return {"valid": False, "errors": ["range"]}
    
    try:
        allowed_start_str = rules.get("allowed_start")
        allowed_end_str = rules.get("allowed_end")
        if not isinstance(allowed_start_str, str) or not isinstance(allowed_end_str, str):
            return {"valid": False, "errors": ["allowed_period"]}
        allowed_start = datetime.fromisoformat(allowed_start_str).date()
        allowed_end = datetime.fromisoformat(allowed_end_str).date()
    except (ValueError, TypeError, AttributeError):
        return {"valid": False, "errors": ["allowed_period"]}
    
    try:
        max_duration = rules.get("max_duration_days")
        if max_duration is None:
            return {"valid": False, "errors": ["duration"]}
        max_duration_days = int(max_duration)
    except (ValueError, TypeError):
        return {"valid": False, "errors": ["duration"]}
    
    parsed_blocked = []
    try:
        blocked_periods = rules.get("blocked_periods", [])
        if not isinstance(blocked_periods, list):
            return {"valid": False, "errors": ["blocked_period"]}
        
        for period in blocked_periods:
            if not isinstance(period, (list, tuple)) or len(period) != 2:
                return {"valid": False, "errors": ["blocked_period"]}
            blocked_start = datetime.fromisoformat(period[0]).date()
            blocked_end = datetime.fromisoformat(period[1]).date()
            parsed_blocked.append((blocked_start, blocked_end))
    except (ValueError, TypeError, AttributeError, IndexError):
        return {"valid": False, "errors": ["blocked_period"]}
    
    if start_date >= end_date:
        errors.append("range")
    
    if start_date < allowed_start or end_date > allowed_end:
        errors.append("allowed_period")
    
    duration = (end_date - start_date).days
    if duration > max_duration_days:
        errors.append("duration")
    
    for blocked_start, blocked_end in parsed_blocked:
        if start_date < blocked_end and end_date > blocked_start:
            errors.append("blocked_period")
            break
    
    if errors:
        return {"valid": False, "errors": errors}
    else:
        return {"valid": True, "errors": []}
