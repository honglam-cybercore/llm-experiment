"""T08 Rate Limiter - frozen test suite.

Entry points: api.new() then allow_request

FROZEN at git tag frozen-v1. Identical for C1-C4 and all 12 runs of this task.

Frozen decisions applied here
-----------------------------
* Window (decision 3, tasks.yaml): fixed window, 60 seconds, 10 requests. Every
  assertion below is on behaviour a fixed window and a sliding window SHARE:
  10 allowed then 1 rejected inside the window, and allowed again after the
  clock is advanced past a full window from the first request. Nothing here
  distinguishes the two implementations.
* The manager is always constructed with api.new() - no arguments - so the
  frozen defaults (max_requests=10, window_seconds=60) are what is exercised.
* Every test uses a fresh limiter and a distinct user id, so no test inherits
  another's counter.
* This task has no manual security check; S01-S03 are all automated here.

Correctness (6)
    T08-C01  User request 1  ->  Accepted
    T08-C02  Requests 1-10  ->  All accepted
    T08-C03  Request 11 within period  ->  Rejected
    T08-C04  Request after window resets  ->  Accepted
    T08-C05  User A reaches limit  ->  Does not limit User B
    T08-C06  User B also makes 10 requests  ->  Independently accepted
Robustness (6)
    T08-R01  10th request  ->  Accepted
    T08-R02  11th request  ->  Rejected
    T08-R03  Request immediately before reset  ->  Rejected if already at limit
    T08-R04  Request at/after reset  ->  Accepted
    T08-R05  Interleaved requests from multiple users  ->  Counters remain separate
    T08-R06  Repeated rejected attempts  ->  Must not bypass the limit
Security (3 automated here, 0 manual in results/manual_review.csv,
1 recorded by bandit)
    T08-S01  More than 10 requests within valid window  ->  Cannot bypass limit  [auto]
    T08-S02  Different user identifiers  ->  No cross-user counter corruption  [auto]
    T08-S03  Rejected requests  ->  Do not reset/extend state in a way that allows bypass  [auto]
    T08-S04  Bandit  ->  Findings recorded  [bandit]
"""

import pytest

# --- frozen fixtures of input data ---------------------------------------- #

MAX_REQUESTS = 10
WINDOW = 60
JUST_BEFORE_RESET = WINDOW - 1
AFTER_RESET = WINDOW + 1

USER_A = "user-a"
USER_B = "user-b"


# --- helpers -------------------------------------------------------------- #

def _limiter(api):
    try:
        return api.new()
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} constructing limiter: {exc}",
                    pytrace=False)


def _allow(api, limiter, user_id):
    try:
        return api.method(limiter, "allow_request")(user_id)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} in allow_request: {exc}",
                    pytrace=False)


def _accepted(api, limiter, user_id, note=""):
    assert bool(_allow(api, limiter, user_id)) is True, \
        f"expected request to be allowed for {user_id!r}{note}"


def _refused(api, limiter, user_id, note=""):
    assert bool(_allow(api, limiter, user_id)) is False, \
        f"expected request to be rejected for {user_id!r}{note}"


def _fill(api, limiter, user_id, count=MAX_REQUESTS):
    """Consume `count` allowances, asserting each one is granted."""
    for i in range(count):
        _accepted(api, limiter, user_id, note=f" (request {i + 1} of {count})")


# --- correctness ---------------------------------------------------------- #

@pytest.mark.correctness
def test_C01_first_request_allowed(api):
    limiter = _limiter(api)
    _accepted(api, limiter, USER_A)


@pytest.mark.correctness
def test_C02_first_ten_allowed(api):
    limiter = _limiter(api)
    _fill(api, limiter, USER_A)


@pytest.mark.correctness
def test_C03_eleventh_rejected(api):
    limiter = _limiter(api)
    _fill(api, limiter, USER_A)
    _refused(api, limiter, USER_A, note=" (request 11)")


@pytest.mark.correctness
def test_C04_allowed_after_window_reset(api, clock):
    limiter = _limiter(api)
    _fill(api, limiter, USER_A)
    _refused(api, limiter, USER_A)
    clock.advance(AFTER_RESET)
    _accepted(api, limiter, USER_A, note=" (after the window reset)")


@pytest.mark.correctness
def test_C05_limit_is_per_user(api):
    limiter = _limiter(api)
    _fill(api, limiter, USER_A)
    _refused(api, limiter, USER_A)
    _accepted(api, limiter, USER_B, note=" (a different user)")


@pytest.mark.correctness
def test_C06_second_user_gets_full_allowance(api):
    limiter = _limiter(api)
    _fill(api, limiter, USER_A)
    _refused(api, limiter, USER_A)
    _fill(api, limiter, USER_B)
    _refused(api, limiter, USER_B)


# --- robustness ----------------------------------------------------------- #

@pytest.mark.robustness
def test_R01_tenth_request_allowed(api):
    limiter = _limiter(api)
    for i in range(MAX_REQUESTS - 1):
        _accepted(api, limiter, USER_A, note=f" (request {i + 1})")
    _accepted(api, limiter, USER_A, note=" (request 10, the last of the allowance)")


@pytest.mark.robustness
def test_R02_eleventh_request_rejected(api):
    limiter = _limiter(api)
    _fill(api, limiter, USER_A)
    _refused(api, limiter, USER_A, note=" (request 11)")


@pytest.mark.robustness
def test_R03_still_limited_just_before_reset(api, clock):
    limiter = _limiter(api)
    _fill(api, limiter, USER_A)
    clock.advance(JUST_BEFORE_RESET)
    _refused(api, limiter, USER_A, note=f" ({JUST_BEFORE_RESET}s into the window)")


@pytest.mark.robustness
def test_R04_allowed_at_or_after_reset(api, clock):
    limiter = _limiter(api)
    _fill(api, limiter, USER_A)
    clock.advance(AFTER_RESET)
    _accepted(api, limiter, USER_A, note=f" ({AFTER_RESET}s after the first request)")


@pytest.mark.robustness
def test_R05_interleaved_users_keep_separate_counters(api):
    limiter = _limiter(api)
    for i in range(MAX_REQUESTS):
        _accepted(api, limiter, USER_A, note=f" (interleaved request {i + 1})")
        _accepted(api, limiter, USER_B, note=f" (interleaved request {i + 1})")
    _refused(api, limiter, USER_A)
    _refused(api, limiter, USER_B)


@pytest.mark.robustness
def test_R06_repeated_rejections_do_not_bypass(api):
    limiter = _limiter(api)
    _fill(api, limiter, USER_A)
    for i in range(30):
        _refused(api, limiter, USER_A, note=f" (rejected attempt {i + 1})")


# --- security (automated) ------------------------------------------------- #

@pytest.mark.security
def test_S01_limit_cannot_be_exceeded_in_window(api, clock):
    """Across the whole window, exactly the allowance may be granted."""
    limiter = _limiter(api)
    granted = 0
    for offset in range(0, WINDOW, 2):        # 30 attempts, all inside the window
        clock.reset()
        clock.advance(offset)
        if bool(_allow(api, limiter, USER_A)):
            granted += 1
    assert granted <= MAX_REQUESTS, \
        f"{granted} requests granted inside one {WINDOW}s window (limit {MAX_REQUESTS})"


@pytest.mark.security
def test_S02_no_cross_user_counter_corruption(api):
    """Exhausting many users must not spend, or refund, another user's budget."""
    limiter = _limiter(api)
    others = [f"user-{i}" for i in range(20)]
    for user in others:
        _fill(api, limiter, user)
        _refused(api, limiter, user)
    for user in others:
        _refused(api, limiter, user, note=" (still exhausted)")
    _fill(api, limiter, "late-arrival")
    _refused(api, limiter, "late-arrival")


@pytest.mark.security
def test_S03_rejected_requests_do_not_extend_state(api, clock):
    """A rejected request must not roll the window forward or reset the count."""
    limiter = _limiter(api)
    _fill(api, limiter, USER_A)
    for offset in range(0, JUST_BEFORE_RESET, 5):
        clock.reset()
        clock.advance(offset)
        _refused(api, limiter, USER_A, note=f" ({offset}s into the window)")
    clock.reset()
    clock.advance(JUST_BEFORE_RESET)
    _refused(api, limiter, USER_A,
             note=" (the window must not have been extended by the rejections)")
