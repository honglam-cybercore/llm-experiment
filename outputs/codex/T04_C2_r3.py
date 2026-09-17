from datetime import date


def validate_booking(start, end, rules) -> dict:
    errors = []

    try:
        if not isinstance(start, str) or not isinstance(end, str):
            return {"valid": False, "errors": ["range"]}

        try:
            booking_start = date.fromisoformat(start)
            booking_end = date.fromisoformat(end)
        except (TypeError, ValueError):
            return {"valid": False, "errors": ["range"]}

        if booking_start >= booking_end:
            errors.append("range")

        if not isinstance(rules, dict):
            return {"valid": False, "errors": ["allowed_period", "blocked_period", "duration"]}

        allowed_valid = True
        try:
            allowed_start = date.fromisoformat(rules["allowed_start"])
            allowed_end = date.fromisoformat(rules["allowed_end"])
            if allowed_start >= allowed_end:
                allowed_valid = False
        except (KeyError, TypeError, ValueError):
            allowed_valid = False

        if not allowed_valid:
            errors.append("allowed_period")
        elif booking_start < allowed_start or booking_end > allowed_end:
            errors.append("allowed_period")

        blocked_valid = True
        overlaps_blocked = False
        blocked_periods = rules.get("blocked_periods")

        if not isinstance(blocked_periods, list):
            blocked_valid = False
        else:
            for period in blocked_periods:
                if not isinstance(period, list) or len(period) != 2:
                    blocked_valid = False
                    continue
                try:
                    blocked_start = date.fromisoformat(period[0])
                    blocked_end = date.fromisoformat(period[1])
                    if blocked_start >= blocked_end:
                        blocked_valid = False
                    elif booking_start < blocked_end and booking_end > blocked_start:
                        overlaps_blocked = True
                except (TypeError, ValueError):
                    blocked_valid = False

        if not blocked_valid or overlaps_blocked:
            errors.append("blocked_period")

        duration_valid = True
        max_duration = rules.get("max_duration_days")
        if isinstance(max_duration, bool) or not isinstance(max_duration, int) or max_duration < 0:
            duration_valid = False
        elif (booking_end - booking_start).days > max_duration:
            errors.append("duration")

        if not duration_valid:
            errors.append("duration")

        return {"valid": not errors, "errors": list(dict.fromkeys(errors))}
    except Exception:
        return {"valid": False, "errors": ["range"]}