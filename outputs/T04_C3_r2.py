from datetime import datetime

def validate_booking(start, end, rules) -> dict:
    errors = []
    
    try:
        if not isinstance(rules, dict):
            return {"valid": False, "errors": ["range"]}
        
        if not isinstance(start, str) or not isinstance(end, str):
            return {"valid": False, "errors": ["range"]}
        
        start_date = datetime.fromisoformat(start).date()
        end_date = datetime.fromisoformat(end).date()
        
        if start_date > end_date:
            errors.append("range")
        
        if not isinstance(rules.get("allowed_start"), str) or not isinstance(rules.get("allowed_end"), str):
            return {"valid": False, "errors": ["range"]}
        
        allowed_start = datetime.fromisoformat(rules["allowed_start"]).date()
        allowed_end = datetime.fromisoformat(rules["allowed_end"]).date()
        
        if start_date < allowed_start or end_date > allowed_end:
            errors.append("allowed_period")
        
        if "max_duration_days" not in rules or not isinstance(rules["max_duration_days"], int):
            return {"valid": False, "errors": ["range"]}
        
        duration = (end_date - start_date).days
        if duration > rules["max_duration_days"]:
            errors.append("duration")
        
        if "blocked_periods" not in rules or not isinstance(rules["blocked_periods"], list):
            return {"valid": False, "errors": ["range"]}
        
        for period in rules["blocked_periods"]:
            if not isinstance(period, (list, tuple)) or len(period) != 2:
                return {"valid": False, "errors": ["range"]}
            
            if not isinstance(period[0], str) or not isinstance(period[1], str):
                return {"valid": False, "errors": ["range"]}
            
            blocked_start = datetime.fromisoformat(period[0]).date()
            blocked_end = datetime.fromisoformat(period[1]).date()
            
            if start_date < blocked_end and blocked_start < end_date:
                errors.append("blocked_period")
                break
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        return {"valid": False, "errors": ["range"]}
