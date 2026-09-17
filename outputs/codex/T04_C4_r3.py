from datetime import date


def _parse_iso_date(value):
    if type(value) is not str:
        return None
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return parsed if parsed.isoformat() == value else None


def validate_booking(start, end, rules) -> dict:
    errors = []

    try:
        start_date = _parse_iso_date(start)
        end_date = _parse_iso_date(end)

        if start_date is None or end_date is None or start_date >= end_date:
            errors.append("range")

        if type(rules) is not dict:
            return {
                "valid": False,
                "errors": errors + [
                    "allowed_period",
                    "blocked_period",
                    "duration",
                ],
            }

        allowed_start = _parse_iso_date(rules.get("allowed_start"))
        allowed_end = _parse_iso_date(rules.get("allowed_end"))

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
        blocked_invalid = type(blocked_periods) is not list

        if not blocked_invalid:
            for period in blocked_periods:
                if type(period) is not list or len(period) != 2:
                    blocked_invalid = True
                    break

                blocked_start = _parse_iso_date(period[0])
                blocked_end = _parse_iso_date(period[1])

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
        duration_invalid = type(max_duration) is not int or max_duration < 0

        if not duration_invalid and start_date is not None and end_date is not None:
            if (end_date - start_date).days > max_duration:
                errors.append("duration")
        elif duration_invalid:
            errors.append("duration")

        unique_errors = list(dict.fromkeys(errors))
        return {"valid": not unique_errors, "errors": unique_errors}

    except Exception:
        return {"valid": False, "errors": ["range"]}