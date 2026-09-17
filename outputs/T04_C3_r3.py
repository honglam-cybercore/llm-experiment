from datetime import date

def validate_booking(start, end, rules) -> dict:
    errors = []
    
    # Validate input types
    if not isinstance(start, str) or not isinstance(end, str):
        return {"valid": False, "errors": ["range"]}
    
    if not isinstance(rules, dict):
        return {"valid": False, "errors": ["range"]}
    
    # Try to parse dates
    try:
        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end)
    except (ValueError, AttributeError, TypeError):
        return {"valid": False, "errors": ["range"]}
    
    # Check if start < end
    if start_date >= end_date:
        return {"valid": False, "errors": ["range"]}
    
    # Try to extract and validate rules
    try:
        allowed_start_date = date.fromisoformat(rules["allowed_start"])
        allowed_end_date = date.fromisoformat(rules["allowed_end"])
        if allowed_start_date >= allowed_end_date:
            return {"valid": False, "errors": ["range"]}
        blocked_periods = rules.get("blocked_periods", [])
        max_duration = rules.get("max_duration_days")
    except (KeyError, ValueError, AttributeError, TypeError):
        return {"valid": False, "errors": ["range"]}
    
    # Check if booking is within allowed period
    if start_date < allowed_start_date or end_date > allowed_end_date:
        errors.append("allowed_period")
    
    # Check blocked periods
    if not isinstance(blocked_periods, list):
        return {"valid": False, "errors": ["range"]}
    
    for blocked_period in blocked_periods:
        try:
            if not isinstance(blocked_period, (list, tuple)) or len(blocked_period) != 2:
                return {"valid": False, "errors": ["range"]}
            blocked_start = date.fromisoformat(blocked_period[0])
            blocked_end = date.fromisoformat(blocked_period[1])
            
            # Validate blocked period structure
            if blocked_start >= blocked_end:
                return {"valid": False, "errors": ["range"]}
            
            # Check if booking overlaps with blocked period
            if start_date < blocked_end and end_date > blocked_start:
                errors.append("blocked_period")
                break
        except (ValueError, AttributeError, TypeError, IndexError):
            return {"valid": False, "errors": ["range"]}
    
    # Check duration
    if max_duration is not None:
        try:
            max_duration_int = int(max_duration)
            duration = (end_date - start_date).days
            if duration > max_duration_int:
                errors.append("duration")
        except (ValueError, TypeError):
            return {"valid": False, "errors": ["range"]}
    
    # Return result
    if errors:
        return {"valid": False, "errors": errors}
    else:
        return {"valid": True, "errors": []}
