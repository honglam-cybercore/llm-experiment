from datetime import date


def _parse_date(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if parsed.isoformat() != value:
        return None
    return parsed


def validate_booking(start, end, rules) -> dict:
    errors = []

    start_date = _parse_date(start)
    end_date = _parse_date(end)

    if start_date is None or end_date is None or start_date >= end_date:
        errors.append("range")

    if not isinstance(rules, dict):
        return {"valid": False, "errors": errors or ["range"]}

    allowed_start = _parse_date(rules.get("allowed_start"))
    allowed_end = _parse_date(rules.get("allowed_end"))

    if (
        allowed_start is None
        or allowed_end is None
        or allowed_start >= allowed_end
        or start_date is None
        or end_date is None
        or start_date < allowed_start
        or end_date > allowed_end
    ):
        errors.append("allowed_period")

    blocked_periods = rules.get("blocked_periods")
    blocked_invalid = not isinstance(blocked_periods, list)

    if not blocked_invalid:
        for period in blocked_periods:
            if not isinstance(period, (list, tuple)) or len(period) != 2:
                blocked_invalid = True
                break

            blocked_start = _parse_date(period[0])
            blocked_end = _parse_date(period[1])

            if (
                blocked_start is None
                or blocked_end is None
                or blocked_start >= blocked_end
            ):
                blocked_invalid = True
                break

            if (
                start_date is not None
                and end_date is not None
                and start_date < blocked_end
                and end_date > blocked_start
            ):
                errors.append("blocked_period")
                break

    if blocked_invalid:
        errors.append("blocked_period")

    max_duration = rules.get("max_duration_days")
    if (
        isinstance(max_duration, bool)
        or not isinstance(max_duration, int)
        or max_duration < 0
        or start_date is None
        or end_date is None
        or end_date <= start_date
        or (end_date - start_date).days > max_duration
    ):
        errors.append("duration")

    unique_errors = list(dict.fromkeys(errors))
    return {"valid": not unique_errors, "errors": unique_errors}