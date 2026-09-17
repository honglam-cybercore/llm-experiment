from datetime import datetime

def validate_booking(start, end, rules) -> dict:
    errors = []
    start_date = None
    end_date = None
    
    try:
        start_date = datetime.fromisoformat(start).date()
        end_date = datetime.fromisoformat(end).date()
        if start_date >= end_date:
            errors.append("range")
    except (ValueError, TypeError, AttributeError):
        errors.append("range")
    
    if start_date is None or end_date is None:
        return {"valid": False, "errors": errors}
    
    if not isinstance(rules, dict):
        return {"valid": False, "errors": ["allowed_period", "blocked_period", "duration"]}
    
    try:
        allowed_start = datetime.fromisoformat(rules["allowed_start"]).date()
        allowed_end = datetime.fromisoformat(rules["allowed_end"]).date()
        if start_date < allowed_start or end_date > allowed_end:
            errors.append("allowed_period")
    except (ValueError, TypeError, AttributeError, KeyError):
        errors.append("allowed_period")
    
    blocked_error = False
    try:
        blocked_periods = rules.get("blocked_periods", [])
        if blocked_periods is None:
            blocked_periods = []
        if not isinstance(blocked_periods, list):
            blocked_error = True
        else:
            for blocked in blocked_periods:
                if not isinstance(blocked, (list, tuple)) or len(blocked) != 2:
                    blocked_error = True
                    break
                try:
                    blocked_start = datetime.fromisoformat(blocked[0]).date()
                    blocked_end = datetime.fromisoformat(blocked[1]).date()
                    if start_date < blocked_end and blocked_start < end_date:
                        blocked_error = True
                        break
                except (ValueError, TypeError, AttributeError):
                    blocked_error = True
                    break
    except (TypeError, AttributeError):
        blocked_error = True
    
    if blocked_error:
        errors.append("blocked_period")
    
    try:
        max_duration = rules["max_duration_days"]
        if not isinstance(max_duration, int):
            errors.append("duration")
        else:
            duration = (end_date - start_date).days
            if duration > max_duration:
                errors.append("duration")
    except (KeyError, TypeError):
        errors.append("duration")
    
    if errors:
        return {"valid": False, "errors": errors}
    else:
        return {"valid": True, "errors": []}
