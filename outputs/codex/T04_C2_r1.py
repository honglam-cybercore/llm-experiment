from datetime import date


def validate_booking(start, end, rules) -> dict:
    errors = []

    def parse_date(value):
        if not isinstance(value, str):
            return None
        try:
            parsed = date.fromisoformat(value)
            return parsed if parsed.isoformat() == value else None
        except Exception:
            return None

    try:
        booking_start = parse_date(start)
        booking_end = parse_date(end)

        if booking_start is None or booking_end is None or booking_start >= booking_end:
            return {"valid": False, "errors": ["range"]}

        if not isinstance(rules, dict):
            return {"valid": False, "errors": ["allowed_period", "blocked_period", "duration"]}

        allowed_start = parse_date(rules.get("allowed_start"))
        allowed_end = parse_date(rules.get("allowed_end"))

        if (
            allowed_start is None
            or allowed_end is None
            or allowed_start >= allowed_end
            or booking_start < allowed_start
            or booking_end > allowed_end
        ):
            errors.append("allowed_period")

        blocked_periods = rules.get("blocked_periods")
        if not isinstance(blocked_periods, list):
            errors.append("blocked_period")
        else:
            blocked_invalid = False
            blocked_overlap = False

            for period in blocked_periods:
                if not isinstance(period, list) or len(period) != 2:
                    blocked_invalid = True
                    continue

                blocked_start = parse_date(period[0])
                blocked_end = parse_date(period[1])

                if (
                    blocked_start is None
                    or blocked_end is None
                    or blocked_start >= blocked_end
                ):
                    blocked_invalid = True
                elif booking_start < blocked_end and booking_end > blocked_start:
                    blocked_overlap = True

            if blocked_invalid or blocked_overlap:
                errors.append("blocked_period")

        max_duration = rules.get("max_duration_days")
        if (
            isinstance(max_duration, bool)
            or not isinstance(max_duration, int)
            or max_duration < 0
            or (booking_end - booking_start).days > max_duration
        ):
            errors.append("duration")

        return {"valid": not errors, "errors": errors}
    except BaseException:
        return {"valid": False, "errors": ["range"]}