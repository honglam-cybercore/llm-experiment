from datetime import date


def _parse_iso_date(value):
    if not isinstance(value, str):
        return None
    try:
        if len(value) != 10 or value[4] != "-" or value[7] != "-":
            return None
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value:
            return None
        return parsed
    except Exception:
        return None


def validate_booking(start, end, rules) -> dict:
    try:
        errors = []

        start_date = _parse_iso_date(start)
        end_date = _parse_iso_date(end)

        if start_date is None or end_date is None or start_date >= end_date:
            errors.append("range")

        if not isinstance(rules, dict):
            return {"valid": False, "errors": errors or ["range"]}

        allowed_start = _parse_iso_date(rules.get("allowed_start"))
        allowed_end = _parse_iso_date(rules.get("allowed_end"))

        if (
            allowed_start is None
            or allowed_end is None
            or allowed_start >= allowed_end
        ):
            errors.append("allowed_period")
        elif start_date is not None and end_date is not None:
            if start_date < allowed_start or end_date > allowed_end:
                errors.append("allowed_period")

        blocked_periods = rules.get("blocked_periods")
        if not isinstance(blocked_periods, list):
            errors.append("blocked_period")
        else:
            for period in blocked_periods:
                if not isinstance(period, (list, tuple)) or len(period) != 2:
                    errors.append("blocked_period")
                    break

                blocked_start = _parse_iso_date(period[0])
                blocked_end = _parse_iso_date(period[1])

                if (
                    blocked_start is None
                    or blocked_end is None
                    or blocked_start >= blocked_end
                ):
                    errors.append("blocked_period")
                    break

                if (
                    start_date is not None
                    and end_date is not None
                    and start_date < blocked_end
                    and end_date > blocked_start
                ):
                    errors.append("blocked_period")
                    break

        max_duration = rules.get("max_duration_days")
        if isinstance(max_duration, bool) or not isinstance(max_duration, int):
            errors.append("duration")
        elif max_duration < 0:
            errors.append("duration")
        elif start_date is not None and end_date is not None:
            if (end_date - start_date).days > max_duration:
                errors.append("duration")

        return {"valid": not errors, "errors": errors}
    except Exception:
        return {"valid": False, "errors": ["range"]}