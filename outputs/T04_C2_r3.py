from datetime import date

def validate_booking(start, end, rules) -> dict:
    errors = []
    
    try:
        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end)
    except (ValueError, TypeError, AttributeError):
        return {"valid": False, "errors": ["range"]}
    
    if start_date >= end_date:
        errors.append("range")
    
    if not isinstance(rules, dict):
        return {"valid": False, "errors": ["allowed_period", "blocked_period", "duration"]}
    
    try:
        allowed_start = date.fromisoformat(rules["allowed_start"])
        allowed_end = date.fromisoformat(rules["allowed_end"])
    except (ValueError, TypeError, AttributeError, KeyError):
        return {"valid": False, "errors": ["allowed_period"]}
    
    if start_date < allowed_start or end_date > allowed_end:
        errors.append("allowed_period")
    
    try:
        max_duration = rules["max_duration_days"]
        if not isinstance(max_duration, int):
            return {"valid": False, "errors": ["duration"]}
        duration = (end_date - start_date).days
        if duration > max_duration:
            errors.append("duration")
    except KeyError:
        return {"valid": False, "errors": ["duration"]}
    
    try:
        blocked_periods = rules["blocked_periods"]
    except KeyError:
        return {"valid": False, "errors": ["blocked_period"]}
    
    if not isinstance(blocked_periods, list):
        return {"valid": False, "errors": ["blocked_period"]}
    
    try:
        for blocked_period in blocked_periods:
            try:
                blocked_start = date.fromisoformat(blocked_period[0])
                blocked_end = date.fromisoformat(blocked_period[1])
                if start_date < blocked_end and end_date > blocked_start:
                    errors.append("blocked_period")
                    break
            except (ValueError, TypeError, AttributeError, IndexError, KeyError):
                return {"valid": False, "errors": ["blocked_period"]}
    except TypeError:
        return {"valid": False, "errors": ["blocked_period"]}
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
