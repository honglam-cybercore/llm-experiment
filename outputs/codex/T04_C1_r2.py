from datetime import date
import re

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _parse_date(value):
    if not isinstance(value, str) or not _DATE_PATTERN.fullmatch(value):
        return None
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed.isoformat() == value else None


def validate_booking(start, end, rules) -> dict:
    errors = []

    start_date = _parse_date(start)
    end_date = _parse_date(end)

    if start_date is None or end_date is None or start_date >= end_date:
        errors.append("range")

    if not isinstance(rules, dict):
        return {"valid": False, "errors": errors + ["allowed_period", "blocked_period", "duration"]}

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
    if not isinstance(blocked_periods, list):
        errors.append("blocked_period")
    else:
        parsed_blocked = []
        blocked_valid = True
        for period in blocked_periods:
            if not isinstance(period, (list, tuple)) or len(period) != 2:
                blocked_valid = False
                break
            blocked_start = _parse_date(period[0])
            blocked_end = _parse_date(period[1])
            if (
                blocked_start is None
                or blocked_end is None
                or blocked_start >= blocked_end
            ):
                blocked_valid = False
                break
            parsed_blocked.append((blocked_start, blocked_end))

        if not blocked_valid:
            errors.append("blocked_period")
        elif start_date is not None and end_date is not None:
            if any(
                start_date < blocked_end and end_date > blocked_start
                for blocked_start, blocked_end in parsed_blocked
            ):
                errors.append("blocked_period")

    max_duration = rules.get("max_duration_days")
    if (
        isinstance(max_duration, bool)
        or not isinstance(max_duration, int)
        or max_duration < 0
        or (
            start_date is not None
            and end_date is not None
            and (end_date - start_date).days > max_duration
        )
    ):
        errors.append("duration")

    ordered_errors = [
        error
        for error in ("range", "allowed_period", "blocked_period", "duration")
        if error in errors
    ]
    return {"valid": not ordered_errors, "errors": ordered_errors}