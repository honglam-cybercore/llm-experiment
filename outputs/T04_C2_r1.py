from datetime import datetime, date

def validate_booking(start, end, rules) -> dict:
    errors = []
    
    try:
        if not isinstance(rules, dict):
            return {"valid": False, "errors": []}
        
        def parse_date(value):
            if isinstance(value, datetime):
                return value.date()
            if isinstance(value, date):
                return value
            if isinstance(value, str):
                return datetime.fromisoformat(value).date()
            return datetime.fromisoformat(str(value)).date()
        
        start_date = parse_date(start)
        end_date = parse_date(end)
        allowed_start = parse_date(rules['allowed_start'])
        allowed_end = parse_date(rules['allowed_end'])
        
        if start_date >= end_date:
            errors.append("range")
        
        if start_date < allowed_start or end_date > allowed_end:
            errors.append("allowed_period")
        
        duration = (end_date - start_date).days
        if duration > rules['max_duration_days']:
            errors.append("duration")
        
        blocked_periods = rules.get('blocked_periods', [])
        for blocked in blocked_periods:
            blocked_start = parse_date(blocked[0])
            blocked_end = parse_date(blocked[1])
            
            if start_date < blocked_end and end_date > blocked_start:
                errors.append("blocked_period")
                break
        
    except (TypeError, ValueError, KeyError, AttributeError, IndexError):
        return {"valid": False, "errors": []}
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
