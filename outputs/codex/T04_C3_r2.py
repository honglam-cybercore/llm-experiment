import re
from datetime import date

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _parse_date(value):
    if type(value) is not str or _DATE_PATTERN.fullmatch(value) is None:
        return None
    try:
        return date.fromisoformat(value)
    except Exception:
        return None


def validate_booking(start, end, rules) -> dict:
    try:
        errors = []

        start_date = _parse_date(start)
        end_date = _parse_date(end)

        if start_date is None or end_date is None or start_date >= end_date:
            return {"valid": False, "errors": ["range"]}

        if type(rules) is not dict:
            return {
                "valid": False,
                "errors": ["allowed_period", "blocked_period", "duration"],
            }

        allowed_start = _parse_date(rules.get("allowed_start"))
        allowed_end = _parse_date(rules.get("allowed_end"))

        allowed_valid = (
            allowed_start is not None
            and allowed_end is not None
            and allowed_start < allowed_end
        )

        if (
            not allowed_valid
            or start_date < allowed_start
            or end_date > allowed_end
        ):
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

                if start_date < blocked_end and end_date > blocked_start:
                    errors.append("blocked_period")
                    break

        if not blocked_valid and "blocked_period" not in errors:
            errors.append("blocked_period")

        max_duration_days = rules.get("max_duration_days")
        duration = (end_date - start_date).days

        if (
            type(max_duration_days) is not int
            or max_duration_days < 0
            or duration > max_duration_days
        ):
            errors.append("duration")

        ordered_errors = [
            name for name in ("range", "allowed_period", "blocked_period", "duration")
            if name in errors
        ]
        return {"valid": not ordered_errors, "errors": ordered_errors}
    except Exception:
        return {"valid": False, "errors": ["range"]}