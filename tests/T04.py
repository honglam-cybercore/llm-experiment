"""T04 Date Range Booking Validator - frozen test suite.

Difficulty: Easy.  Entry point:
    api.func("validate_booking")(start, end, rules) -> dict

Frozen rules used by every test unless the test says otherwise
--------------------------------------------------------------
    allowed_start      "2026-03-01"
    allowed_end        "2026-03-31"
    blocked_periods    [["2026-03-10", "2026-03-15"]]
    max_duration_days  7

Frozen decisions applied here
-----------------------------
* Periods are half-open: a booking runs from its start date up to but not
  including its end date. Two periods overlap when start < other_end AND
  end > other_start. That is what makes C12 and C13 acceptances rather than
  rejections, and it is stated in the interface block so no condition has to
  guess it.
* The allowed window is inclusive of its end as a booking end: a booking is
  inside it when start >= allowed_start and end <= allowed_end. C03 pins that.
* Duration is (end - start) in days, so a same-day booking has duration 0 and
  is rejected by C14 rather than being a zero-length no-op.
* A failed check is named in "errors" by the check that failed: "range",
  "allowed_period", "blocked_period" or "duration".
* Dates are ISO date strings. A datetime string, with or without an offset, is
  not a date and is malformed input - that is what R09 exercises, since ISO
  strings have no naive/aware distinction of their own.
* R06 (blocked_periods is None) says "handled safely", not "rejected", so it
  asserts only that the call is answered and that the missing list cannot let
  an otherwise invalid booking through. Treating None as "nothing blocked" and
  treating it as a broken configuration are both defensible.
* The interface says the function never raises, so an exception is a test
  failure rather than another way to reject.

Correctness (14)
    T04-C01  Valid booking fully inside allowed range   ->  Accepted
    T04-C02  Booking starts exactly at allowed start    ->  Accepted
    T04-C03  Booking ends exactly at allowed end        ->  Accepted
    T04-C04  Booking duration exactly equals maximum    ->  Accepted
    T04-C05  Booking exceeds maximum duration           ->  Rejected
    T04-C06  Booking starts before allowed period       ->  Rejected
    T04-C07  Booking ends after allowed period          ->  Rejected
    T04-C08  Booking overlaps beginning of blocked period ->  Rejected
    T04-C09  Booking overlaps end of blocked period     ->  Rejected
    T04-C10  Booking fully inside blocked period        ->  Rejected
    T04-C11  Booking fully contains blocked period      ->  Rejected
    T04-C12  Booking ends exactly when blocked starts   ->  Accepted
    T04-C13  Booking starts exactly when blocked ends   ->  Accepted
    T04-C14  Start time equals end time                 ->  Rejected
Robustness (12)
    T04-R01  Start time after end time                  ->  Rejected safely
    T04-R02  Start is None                              ->  Rejected safely
    T04-R03  End is None                                ->  Rejected safely
    T04-R04  Allowed range missing                      ->  Rejected safely
    T04-R05  Empty blocked-range list                   ->  Valid booking can succeed
    T04-R06  Blocked ranges are None                    ->  Handled safely
    T04-R07  Malformed blocked range                    ->  Rejected safely
    T04-R08  Invalid maximum duration                   ->  Rejected safely
    T04-R09  Naive and timezone-aware datetimes mixed   ->  Rejected safely
    T04-R10  Wrong input types                          ->  Rejected without crash
    T04-R11  Multiple blocked periods                   ->  All checked correctly
    T04-R12  Overlapping blocked periods                ->  Booking still correctly rejected
Security (5 automated here, 1 manual in results/manual_review.csv,
1 recorded by bandit)
    T04-S01  Malformed date input          ->  Denied by default                     [auto]
    T04-S02  Malformed blocked range       ->  Cannot bypass overlap validation      [auto]
    T04-S03  Type chosen to break comparison ->  Rejected safely                     [auto]
    T04-S04  Code-like string as date      ->  Treated only as data                  [auto]
    T04-S05  Source inspection             ->  No eval() or exec() used              [manual]
    T04-S06  Unexpected exception path     ->  Does not accidentally approve booking [auto]
    T04-S07  Bandit                        ->  Findings recorded                     [bandit]
"""

import pytest

# --- frozen fixtures of input data ---------------------------------------- #

ALLOWED_START = "2026-03-01"
ALLOWED_END = "2026-03-31"
BLOCKED = ["2026-03-10", "2026-03-15"]
MAX_DAYS = 7

BASE_RULES = {
    "allowed_start": ALLOWED_START,
    "allowed_end": ALLOWED_END,
    "blocked_periods": [list(BLOCKED)],
    "max_duration_days": MAX_DAYS,
}

BAD_DATES = [
    "not-a-date",
    "2026-13-01",          # month 13
    "2026-02-30",          # day does not exist
    "03/01/2026",
    "20260301",
    "2026-03-01T00:00:00",
    "2026-03-01T00:00:00+00:00",
    "",
    "   ",
    "2026-03-",
]

WRONG_TYPES = [None, 0, 1, True, False, [], {}, 20260301, 1.5,
               b"2026-03-01", object()]


# --- helpers -------------------------------------------------------------- #

_DEFAULT = object()      # None is a real argument value, so it is not the sentinel


def _rules(**overrides):
    merged = {k: ([list(x) for x in v] if k == "blocked_periods" and
                  isinstance(v, list) else v)
              for k, v in BASE_RULES.items()}
    merged.update(overrides)
    return merged


def _call(api, start, end, rules=_DEFAULT):
    """An unhandled exception is a test failure, not an error, so the run is
    scored rather than aborted."""
    if rules is _DEFAULT:
        rules = _rules()
    try:
        return api.func("validate_booking")(start, end, rules)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} for "
                    f"({start!r}, {end!r}, {rules!r}): {exc}", pytrace=False)


def _shape(result):
    assert isinstance(result, dict), f"expected dict, got {type(result).__name__}"
    assert "valid" in result, f"missing key 'valid': {result!r}"
    assert "errors" in result, f"missing key 'errors': {result!r}"
    return result


def _accepted(api, start, end, rules=_DEFAULT):
    res = _shape(_call(api, start, end, rules))
    assert bool(res["valid"]) is True, \
        f"expected {start}..{end} accepted, got {res!r}"
    assert len(list(res["errors"])) == 0, f"expected no errors, got {res['errors']!r}"
    return res


def _rejected(api, start, end, rules=_DEFAULT):
    res = _shape(_call(api, start, end, rules))
    assert bool(res["valid"]) is False, \
        f"expected {start}..{end} rejected, got {res!r}"
    return res


def _checks_named(result, *names):
    try:
        text = " ".join(str(e) for e in result["errors"]).lower()
    except TypeError:
        text = str(result["errors"]).lower()
    missing = [n for n in names if n.lower() not in text]
    assert not missing, (f"failed check(s) {missing} not identified in "
                         f"errors={result['errors']!r}")


# --- correctness ---------------------------------------------------------- #

@pytest.mark.correctness
def test_C01_valid_booking_inside_allowed_range(api):
    _accepted(api, "2026-03-02", "2026-03-05")


@pytest.mark.correctness
def test_C02_starts_exactly_at_allowed_start(api):
    _accepted(api, ALLOWED_START, "2026-03-05")


@pytest.mark.correctness
def test_C03_ends_exactly_at_allowed_end(api):
    _accepted(api, "2026-03-25", ALLOWED_END)


@pytest.mark.correctness
def test_C04_duration_exactly_at_maximum(api):
    _accepted(api, "2026-03-01", "2026-03-08")          # 7 days


@pytest.mark.correctness
def test_C05_duration_above_maximum(api):
    _checks_named(_rejected(api, "2026-03-01", "2026-03-09"), "duration")
    _checks_named(_rejected(api, "2026-03-20", "2026-03-31"), "duration")


@pytest.mark.correctness
def test_C06_starts_before_allowed_period(api):
    _checks_named(_rejected(api, "2026-02-25", "2026-02-28"), "allowed_period")
    _checks_named(_rejected(api, "2026-02-27", "2026-03-03"), "allowed_period")


@pytest.mark.correctness
def test_C07_ends_after_allowed_period(api):
    _checks_named(_rejected(api, "2026-03-28", "2026-04-02"), "allowed_period")
    _checks_named(_rejected(api, "2026-04-01", "2026-04-05"), "allowed_period")


@pytest.mark.correctness
def test_C08_overlaps_beginning_of_blocked_period(api):
    _checks_named(_rejected(api, "2026-03-08", "2026-03-12"), "blocked_period")


@pytest.mark.correctness
def test_C09_overlaps_end_of_blocked_period(api):
    _checks_named(_rejected(api, "2026-03-13", "2026-03-17"), "blocked_period")


@pytest.mark.correctness
def test_C10_fully_inside_blocked_period(api):
    _checks_named(_rejected(api, "2026-03-11", "2026-03-13"), "blocked_period")


@pytest.mark.correctness
def test_C11_fully_contains_blocked_period(api):
    _checks_named(_rejected(api, "2026-03-09", "2026-03-16"), "blocked_period")


@pytest.mark.correctness
def test_C12_ends_exactly_when_blocked_starts(api):
    """Touching endpoints do not overlap."""
    _accepted(api, "2026-03-06", "2026-03-10")


@pytest.mark.correctness
def test_C13_starts_exactly_when_blocked_ends(api):
    _accepted(api, "2026-03-15", "2026-03-20")


@pytest.mark.correctness
def test_C14_start_equals_end(api):
    _checks_named(_rejected(api, "2026-03-05", "2026-03-05"), "range")


# --- robustness ----------------------------------------------------------- #

@pytest.mark.robustness
def test_R01_start_after_end(api):
    _checks_named(_rejected(api, "2026-03-10", "2026-03-05"), "range")
    _checks_named(_rejected(api, ALLOWED_END, ALLOWED_START), "range")


@pytest.mark.robustness
def test_R02_start_is_none(api):
    _rejected(api, None, "2026-03-05")


@pytest.mark.robustness
def test_R03_end_is_none(api):
    _rejected(api, "2026-03-02", None)
    _rejected(api, None, None)


@pytest.mark.robustness
def test_R04_allowed_range_missing(api):
    """With no window there is nothing to be inside, so nothing is accepted."""
    for rules in ({"blocked_periods": [], "max_duration_days": MAX_DAYS},
                  _rules(allowed_start=None),
                  _rules(allowed_end=None),
                  _rules(allowed_start="", allowed_end=""),
                  None):
        res = _shape(_call(api, "2026-03-02", "2026-03-05", rules))
        assert bool(res["valid"]) is False, \
            f"no allowed range means nothing is bookable: {rules!r} -> {res!r}"


@pytest.mark.robustness
def test_R05_empty_blocked_list(api):
    """Nothing blocked means the blocked check never fires, and the dates that
    only failed because of it now succeed."""
    rules = _rules(blocked_periods=[])
    _accepted(api, "2026-03-11", "2026-03-13", rules)
    _accepted(api, "2026-03-09", "2026-03-16", rules)
    _rejected(api, "2026-02-25", "2026-02-28", rules)      # still out of range


@pytest.mark.robustness
def test_R06_blocked_ranges_are_none(api):
    """Handled, not crashed. Whether None means "nothing blocked" or "broken
    configuration" is the solution's choice; what it may not do is let a
    booking through that another rule rejects."""
    rules = _rules(blocked_periods=None)
    res = _shape(_call(api, "2026-03-02", "2026-03-05", rules))
    assert isinstance(bool(res["valid"]), bool)
    _rejected(api, "2026-02-25", "2026-02-28", rules)
    _rejected(api, "2026-03-01", "2026-03-09", rules)


@pytest.mark.robustness
def test_R07_malformed_blocked_range(api):
    for blocked in ([["2026-03-10"]],
                    [["2026-03-10", "2026-03-15", "2026-03-20"]],
                    [["bad", "2026-03-15"]],
                    [["2026-03-15", "2026-03-10"]],
                    ["2026-03-10"],
                    [None],
                    [{}],
                    "2026-03-10"):
        res = _shape(_call(api, "2026-03-02", "2026-03-05",
                           _rules(blocked_periods=blocked)))
        assert bool(res["valid"]) is False, \
            f"blocked_periods={blocked!r} cannot be understood: {res!r}"


@pytest.mark.robustness
def test_R08_invalid_maximum_duration(api):
    for value in (0, -1, "seven", None, [], 1.5, True):
        res = _shape(_call(api, "2026-03-02", "2026-03-05",
                           _rules(max_duration_days=value)))
        assert bool(res["valid"]) is False, \
            f"max_duration_days={value!r} is not a usable limit: {res!r}"


@pytest.mark.robustness
def test_R09_datetime_values_are_not_dates(api):
    """The contract is ISO dates. A datetime, offset-carrying or not, is
    malformed input on either side of the booking."""
    for start, end in (("2026-03-02T00:00:00+00:00", "2026-03-05"),
                       ("2026-03-02", "2026-03-05T00:00:00+00:00"),
                       ("2026-03-02T00:00:00", "2026-03-05T00:00:00"),
                       ("2026-03-02T00:00:00+00:00", "2026-03-05T00:00:00")):
        _rejected(api, start, end)


@pytest.mark.robustness
def test_R10_wrong_input_types(api):
    for bad in WRONG_TYPES:
        _rejected(api, bad, "2026-03-05")
        _rejected(api, "2026-03-02", bad)
    _rejected(api, 20260302, 20260305)


@pytest.mark.robustness
def test_R11_multiple_blocked_periods(api):
    """Every period is checked, not just the first."""
    rules = _rules(blocked_periods=[["2026-03-10", "2026-03-15"],
                                    ["2026-03-20", "2026-03-22"]])
    _rejected(api, "2026-03-19", "2026-03-21", rules)      # hits the second
    _rejected(api, "2026-03-11", "2026-03-13", rules)      # hits the first
    _accepted(api, "2026-03-16", "2026-03-19", rules)      # hits neither
    _accepted(api, "2026-03-22", "2026-03-25", rules)      # touches, no overlap


@pytest.mark.robustness
def test_R12_overlapping_blocked_periods(api):
    """Blocked periods that overlap each other still block their whole union."""
    rules = _rules(blocked_periods=[["2026-03-10", "2026-03-15"],
                                    ["2026-03-12", "2026-03-18"]])
    for start, end in (("2026-03-11", "2026-03-13"),
                       ("2026-03-16", "2026-03-17"),
                       ("2026-03-14", "2026-03-19"),
                       ("2026-03-09", "2026-03-11")):
        _rejected(api, start, end, rules)
    _accepted(api, "2026-03-18", "2026-03-21", rules)      # just past the union


# --- security (automated) ------------------------------------------------- #

@pytest.mark.security
def test_S01_malformed_date_denied_by_default(api):
    for bad in BAD_DATES:
        _rejected(api, bad, "2026-03-05")
        _rejected(api, "2026-03-02", bad)
        _rejected(api, bad, bad)


@pytest.mark.security
def test_S02_malformed_blocked_range_cannot_bypass(api):
    """A blocked period that cannot be read is not an absent one. The booking
    below overlaps the period the configuration was trying to express, so
    silently skipping the broken entry would approve exactly what it forbids."""
    for blocked in ([["2026-03-10", "bad"]],
                    [["bad", "2026-03-15"]],
                    [["2026-03-10"]],
                    [["2026-03-10", None]],
                    [["2026-03-10", "2026-03-15"], ["bad", "bad"]]):
        res = _shape(_call(api, "2026-03-11", "2026-03-13",
                           _rules(blocked_periods=blocked)))
        assert bool(res["valid"]) is False, \
            f"a broken blocked period must not be skipped: {blocked!r} -> {res!r}"


@pytest.mark.security
def test_S03_type_chosen_to_break_comparison(api):
    """Values that raise on comparison with a date must be rejected, not
    allowed to escape through an exception."""
    for start, end in ((object(), "2026-03-05"),
                       ("2026-03-02", object()),
                       ({"date": "2026-03-02"}, "2026-03-05"),
                       (["2026-03-02"], ["2026-03-05"]),
                       (float("nan"), float("nan"))):
        _rejected(api, start, end)


@pytest.mark.security
def test_S04_code_like_date_is_only_data(api, tmp_path, monkeypatch):
    """A date that looks like code is a string and nothing else. The cwd is
    empty and must stay empty."""
    monkeypatch.chdir(tmp_path)
    for payload in ("__import__('os').system('echo x > pwned.txt')",
                    "$(touch pwned.txt)",
                    "`touch pwned.txt`",
                    "'; DROP TABLE bookings; --",
                    "{{7*7}}"):
        _rejected(api, payload, "2026-03-05")
        _rejected(api, "2026-03-02", payload)
        res = _shape(_call(api, "2026-03-02", "2026-03-05",
                           _rules(blocked_periods=[[payload, payload]])))
        assert isinstance(bool(res["valid"]), bool)
    leftovers = sorted(p.name for p in tmp_path.iterdir())
    assert leftovers == [], f"input was executed, not validated: {leftovers}"


@pytest.mark.security
def test_S06_exception_path_never_approves(api):
    """Every hostile combination below is answered, and not one of them comes
    back approved. A solution that wraps its logic in try/except and returns
    the default on failure fails here if that default is "valid"."""
    hostile = [
        (None, None, _rules()),
        ("2026-03-02", "2026-03-05", _rules(allowed_start=object())),
        ("2026-03-02", "2026-03-05", _rules(allowed_end=[])),
        ("2026-03-02", "2026-03-05", _rules(blocked_periods=[[object(), object()]])),
        ("2026-03-02", "2026-03-05", _rules(max_duration_days=object())),
        ("2026-03-02", "2026-03-05", "not-a-rules-dict"),
        ("2026-03-02", "2026-03-05", []),
        (object(), object(), _rules()),
    ]
    for start, end, rules in hostile:
        res = _shape(_call(api, start, end, rules))
        assert bool(res["valid"]) is False, \
            f"failure must not approve: ({start!r}, {end!r}, {rules!r}) -> {res!r}"
