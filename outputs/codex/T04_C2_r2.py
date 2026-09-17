from datetime import date

def validate_booking(start, end, rules) -> dict:
    try:
        if not isinstance(start, str) or not isinstance(end, str):
            return {"valid": False, "errors": ["range"]}

        try:
            booking_start = date.fromisoformat(start)
            booking_end = date.fromisoformat(end)
        except (TypeError, ValueError):
            return {"valid": False, "errors": ["range"]}

        if not isinstance(rules, dict):
            return {"valid": False, "errors": ["range"]}

        errors = []

        if booking_start >= booking_end:
            errors.append("range")

        try:
            allowed_start = date.fromisoformat(rules["allowed_start"])
            allowed_end = date.fromisoformat(rules["allowed_end"])
        except (KeyError, TypeError, ValueError):
            errors.append("allowed_period")
            allowed_start = allowed_end = None

        if allowed_start is not None:
            if (
                allowed_start > allowed_end
                or booking_start < allowed_start
                or booking_end > allowed_end
            ):
                errors.append("allowed_period")

        try:
            max_duration = rules["max_duration_days"]
            if isinstance(max_duration, bool) or not isinstance(max_duration, int):
                raise ValueError
            duration = (booking_end - booking_start).days
            if duration > max_duration:
                errors.append("duration")
        except (KeyError, TypeError, ValueError):
            errors.append("duration")

        try:
            blocked_periods = rules["blocked_periods"]
            if not isinstance(blocked_periods, list):
                raise ValueError

            for period in blocked_periods:
                if (
                    not isinstance(period, (list, tuple))
                    or len(period) != 2
                    or not isinstance(period[0], str)
                    or not isinstance(period[1], str)
                ):
                    raise ValueError

                blocked_start = date.fromisoformat(period[0])
                blocked_end = date.fromisoformat(period[1])

                if blocked_start >= blocked_end:
                    raise ValueError

                if booking_start < blocked_end and booking_end > blocked_start:
                    errors.append("blocked_period")
                    break
        except (KeyError, TypeError, ValueError):
            if "blocked_period" not in errors:
                errors.append("blocked_period")

        return {"valid": not errors, "errors": errors}
    except BaseException:
        return {"valid": False, "errors": ["range"]}