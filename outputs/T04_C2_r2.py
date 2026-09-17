from datetime import datetime

def validate_booking(start, end, rules) -> dict:
    errors = []
    
    if not isinstance(rules, dict):
        return {"valid": False, "errors": []}
    
    try:
        start_date = datetime.fromisoformat(start).date()
        end_date = datetime.fromisoformat(end).date()
    except (ValueError, TypeError):
        return {"valid": False, "errors": []}
    
    try:
        allowed_start = datetime.fromisoformat(rules["allowed_start"]).date()
        allowed_end = datetime.fromisoformat(rules["allowed_end"]).date()
    except (ValueError, TypeError, KeyError):
        return {"valid": False, "errors": []}
    
    try:
        max_duration = int(rules["max_duration_days"])
    except (ValueError, TypeError, KeyError):
        return {"valid": False, "errors": []}
    
    try:
        blocked_periods_list = rules.get("blocked_periods", [])
        parsed_blocked = []
        for blocked in blocked_periods_list:
            blocked_start_date = datetime.fromisoformat(blocked[0]).date()
            blocked_end_date = datetime.fromisoformat(blocked[1]).date()
            parsed_blocked.append((blocked_start_date, blocked_end_date))
    except (ValueError, TypeError, IndexError, KeyError):
        return {"valid": False, "errors": []}
    
    if start_date >= end_date:
        errors.append("range")
    
    if start_date < allowed_start or end_date > allowed_end:
        errors.append("allowed_period")
    
    for blocked_start_date, blocked_end_date in parsed_blocked:
        if start_date < blocked_end_date and blocked_start_date < end_date:
            errors.append("blocked_period")
            break
    
    duration = (end_date - start_date).days
    if duration > max_duration:
        errors.append("duration")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
