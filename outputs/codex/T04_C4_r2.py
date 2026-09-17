import re
from datetime import date

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _parse_date(value):
    if type(value) is not str or not _DATE_RE.fullmatch(value):
        return None
    try:
        parsed = date.fromisoformat(value)
    except Exception:
        return None
    return parsed if parsed.isoformat() == value else None


def validate_booking(start, end, rules) -> dict:
    errors = []

    start_date = _parse_date(start)
    end_date = _parse_date(end)

    if start_date is None or end_date is None or start_date >= end_date:
        errors.append("range")

    if type(rules) is not dict:
        return {"valid": False, "errors": errors or ["allowed_period"]}

    allowed_start = _parse_date(rules.get("allowed_start"))
    allowed_end = _parse_date(rules.get("allowed_end"))

    allowed_valid = (
        allowed_start is not None
        and allowed_end is not None
        and allowed_start < allowed_end
    )

    if not allowed_valid:
        errors.append("allowed_period")
    elif start_date is not None and end_date is not None:
        if start_date < allowed_start or end_date > allowed_end:
            errors.append("allowed_period")

    blocked_periods = rules.get("blocked_periods")
    blocked_valid = type(blocked_periods) is list

    if blocked_valid:
        for period in blocked_periods:
            if type(period) is not list or len(period) != 2:
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

            if (
                start_date is not None
                and end_date is not None
                and start_date < blocked_end
                and end_date > blocked_start
            ):
                errors.append("blocked_period")
                break

    if not blocked_valid:
        errors.append("blocked_period")

    max_duration = rules.get("max_duration_days")
    duration_valid = type(max_duration) is int and max_duration >= 0

    if not duration_valid:
        errors.append("duration")
    elif start_date is not None and end_date is not None:
        if (end_date - start_date).days > max_duration:
            errors.append("duration")

    unique_errors = []
    for error in errors:
        if error not in unique_errors:
            unique_errors.append(error)

    return {"valid": not unique_errors, "errors": unique_errors}