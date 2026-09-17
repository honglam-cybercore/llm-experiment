import re
from datetime import date

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _parse_date(value):
    if not isinstance(value, str) or not _DATE_PATTERN.fullmatch(value):
        return None
    try:
        parsed = date.fromisoformat(value)
    except Exception:
        return None
    return parsed if parsed.isoformat() == value else None


def validate_booking(start, end, rules) -> dict:
    try:
        errors = []

        booking_start = _parse_date(start)
        booking_end = _parse_date(end)

        if booking_start is None or booking_end is None or booking_start >= booking_end:
            errors.append("range")

        if not isinstance(rules, dict):
            return {
                "valid": False,
                "errors": ["range", "allowed_period", "blocked_period", "duration"],
            }

        allowed_start = _parse_date(rules.get("allowed_start"))
        allowed_end = _parse_date(rules.get("allowed_end"))

        if (
            allowed_start is None
            or allowed_end is None
            or allowed_start >= allowed_end
            or booking_start is None
            or booking_end is None
            or booking_start < allowed_start
            or booking_end > allowed_end
        ):
            errors.append("allowed_period")

        blocked_periods = rules.get("blocked_periods")
        blocked_valid = isinstance(blocked_periods, list)

        if blocked_valid:
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

                if (
                    booking_start is not None
                    and booking_end is not None
                    and booking_start < blocked_end
                    and booking_end > blocked_start
                ):
                    errors.append("blocked_period")
                    break

        if not blocked_valid and "blocked_period" not in errors:
            errors.append("blocked_period")

        max_duration = rules.get("max_duration_days")
        if (
            not isinstance(max_duration, int)
            or isinstance(max_duration, bool)
            or max_duration < 0
            or booking_start is None
            or booking_end is None
            or booking_end.toordinal() - booking_start.toordinal() > max_duration
        ):
            errors.append("duration")

        unique_errors = list(dict.fromkeys(errors))
        return {"valid": not unique_errors, "errors": unique_errors}

    except BaseException:
        return {
            "valid": False,
            "errors": ["range", "allowed_period", "blocked_period", "duration"],
        }