from datetime import datetime

def validate_booking(start, end, rules) -> dict:
    errors = []
    
    try:
        # Type checks for main inputs
        if not isinstance(start, str) or not isinstance(end, str):
            return {"valid": False, "errors": ["range"]}
        if not isinstance(rules, dict):
            return {"valid": False, "errors": ["range"]}
        
        # Parse input dates
        start_date = datetime.fromisoformat(start).date()
        end_date = datetime.fromisoformat(end).date()
        
        # Check if start is before end (range check)
        if start_date >= end_date:
            errors.append("range")
        
        # Parse and validate rules
        allowed_start = datetime.fromisoformat(rules["allowed_start"]).date()
        allowed_end = datetime.fromisoformat(rules["allowed_end"]).date()
        blocked_periods = rules.get("blocked_periods", [])
        max_duration = rules.get("max_duration_days")
        
        # Type check for blocked_periods
        if not isinstance(blocked_periods, list):
            return {"valid": False, "errors": ["range"]}
        
        # Check if booking is within allowed period
        if start_date < allowed_start or end_date > allowed_end:
            errors.append("allowed_period")
        
        # Check duration constraint
        if max_duration is not None:
            if not isinstance(max_duration, int) or isinstance(max_duration, bool):
                return {"valid": False, "errors": ["range"]}
            duration = (end_date - start_date).days
            if duration > max_duration:
                errors.append("duration")
        
        # Check for overlaps with blocked periods
        for blocked_entry in blocked_periods:
            if not isinstance(blocked_entry, (list, tuple)) or len(blocked_entry) != 2:
                return {"valid": False, "errors": ["range"]}
            
            blocked_start_str, blocked_end_str = blocked_entry
            blocked_start = datetime.fromisoformat(blocked_start_str).date()
            blocked_end = datetime.fromisoformat(blocked_end_str).date()
            
            # Check overlap: periods [start, end) overlap if start < other_end AND other_start < end
            if start_date < blocked_end and blocked_start < end_date:
                errors.append("blocked_period")
                break
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    except (ValueError, TypeError, KeyError, AttributeError, IndexError):
        return {"valid": False, "errors": ["range"]}
