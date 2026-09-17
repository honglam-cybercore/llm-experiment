import re
from datetime import date

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _parse_date(value):
    if type(value) is not str or not _DATE_PATTERN.fullmatch(value):
        return None
    try:
        return date.fromisoformat(value)
    except Exception:
        return None


def validate_booking(start, end, rules) -> dict:
    try:
        errors = []

        booking_start = _parse_date(start)
        booking_end = _parse_date(end)

        if booking_start is None or booking_end is None or booking_start >= booking_end:
            return {"valid": False, "errors": ["range"]}

        if type(rules) is not dict:
            return {
                "valid": False,
                "errors": ["allowed_period", "blocked_period", "duration"],
            }

        allowed_start = _parse_date(rules.get("allowed_start"))
        allowed_end = _parse_date(rules.get("allowed_end"))

        if (
            allowed_start is None
            or allowed_end is None
            or allowed_start >= allowed_end
            or booking_start < allowed_start
            or booking_end > allowed_end
        ):
            errors.append("allowed_period")

        blocked_periods = rules.get("blocked_periods")
        if type(blocked_periods) is not list:
            errors.append("blocked_period")
        else:
            blocked_invalid = False
            for period in blocked_periods:
                if type(period) is not list or len(period) != 2:
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

                if booking_start < blocked_end and blocked_start < booking_end:
                    errors.append("blocked_period")
                    break

            if blocked_invalid and "blocked_period" not in errors:
                errors.append("blocked_period")

        max_duration = rules.get("max_duration_days")
        if type(max_duration) is not int or isinstance(max_duration, bool) or max_duration < 0:
            errors.append("duration")
        elif (booking_end - booking_start).days > max_duration:
            errors.append("duration")

        return {"valid": not errors, "errors": errors}
    except BaseException:
        return {"valid": False, "errors": ["range"]}