import re
from datetime import date


_DATE_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


def _parse_date(value):
    if not isinstance(value, str) or not _DATE_PATTERN.fullmatch(value):
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError, OverflowError):
        return None


def validate_booking(start, end, rules) -> dict:
    errors = []

    try:
        booking_start = _parse_date(start)
        booking_end = _parse_date(end)

        if booking_start is None or booking_end is None or booking_start >= booking_end:
            errors.append("range")

        if not isinstance(rules, dict):
            return {"valid": False, "errors": ["allowed_period", "blocked_period", "duration"]}

        allowed_start = _parse_date(rules.get("allowed_start"))
        allowed_end = _parse_date(rules.get("allowed_end"))

        allowed_valid = (
            allowed_start is not None
            and allowed_end is not None
            and allowed_start < allowed_end
        )

        if not allowed_valid or (
            booking_start is not None
            and booking_end is not None
            and (
                booking_start < allowed_start
                or booking_end > allowed_end
            )
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
                    and blocked_start < booking_end
                ):
                    errors.append("blocked_period")
                    break

        if not blocked_valid and "blocked_period" not in errors:
            errors.append("blocked_period")

        max_duration = rules.get("max_duration_days")
        duration_valid = (
            isinstance(max_duration, int)
            and not isinstance(max_duration, bool)
            and max_duration >= 0
        )

        if not duration_valid or (
            booking_start is not None
            and booking_end is not None
            and (booking_end - booking_start).days > max_duration
        ):
            errors.append("duration")

    except BaseException:
        return {"valid": False, "errors": ["range", "allowed_period", "blocked_period", "duration"]}

    unique_errors = []
    for error in errors:
        if error not in unique_errors:
            unique_errors.append(error)

    return {"valid": not unique_errors, "errors": unique_errors}