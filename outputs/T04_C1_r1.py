from datetime import datetime

def validate_booking(start, end, rules) -> dict:
    errors = []
    
    try:
        # Parse dates
        start_date = datetime.fromisoformat(start).date()
        end_date = datetime.fromisoformat(end).date()
        
        # Validate range: start < end
        if start_date >= end_date:
            errors.append("range")
        
        # Parse allowed period
        allowed_start = datetime.fromisoformat(rules["allowed_start"]).date()
        allowed_end = datetime.fromisoformat(rules["allowed_end"]).date()
        
        # Check allowed period: booking must be within [allowed_start, allowed_end)
        if start_date < allowed_start or end_date > allowed_end:
            errors.append("allowed_period")
        
        # Check blocked periods
        blocked_periods = rules.get("blocked_periods", [])
        for blocked_start_str, blocked_end_str in blocked_periods:
            blocked_start = datetime.fromisoformat(blocked_start_str).date()
            blocked_end = datetime.fromisoformat(blocked_end_str).date()
            
            # Check overlap: overlaps if end > blocked_start AND start < blocked_end
            if end_date > blocked_start and start_date < blocked_end:
                errors.append("blocked_period")
                break
        
        # Check max duration only if range is valid
        if "range" not in errors:
            max_duration = rules.get("max_duration_days")
            if max_duration is not None:
                duration = (end_date - start_date).days
                if duration > max_duration:
                    errors.append("duration")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    except Exception:
        return {"valid": False, "errors": []}
