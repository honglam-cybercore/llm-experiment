from datetime import datetime

def validate_booking(start, end, rules) -> dict:
    # Try to parse all inputs upfront
    try:
        start_date = datetime.fromisoformat(start).date()
        end_date = datetime.fromisoformat(end).date()
        allowed_start = datetime.fromisoformat(rules["allowed_start"]).date()
        allowed_end = datetime.fromisoformat(rules["allowed_end"]).date()
        max_duration_days = int(rules["max_duration_days"])
        blocked_periods = rules.get("blocked_periods", [])
        
        # Pre-parse all blocked periods
        parsed_blocked = []
        for bp in blocked_periods:
            b_start = datetime.fromisoformat(bp[0]).date()
            b_end = datetime.fromisoformat(bp[1]).date()
            parsed_blocked.append((b_start, b_end))
    except (ValueError, TypeError, KeyError, AttributeError, IndexError):
        return {"valid": False, "errors": ["range"]}
    
    errors = []
    
    # Check start < end
    if start_date >= end_date:
        errors.append("range")
    
    # Check allowed period
    if start_date < allowed_start or end_date > allowed_end:
        errors.append("allowed_period")
    
    # Check blocked periods
    for blocked_start, blocked_end in parsed_blocked:
        # Check overlap: [start_date, end_date) overlaps [blocked_start, blocked_end)
        if start_date < blocked_end and blocked_start < end_date:
            errors.append("blocked_period")
            break
    
    # Check duration
    duration = (end_date - start_date).days
    if duration > max_duration_days:
        errors.append("duration")
    
    return {"valid": len(errors) == 0, "errors": errors}
