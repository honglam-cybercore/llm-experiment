"""T02 Login Attempt Manager - frozen test suite.

Entry points: api.new({"alice": "pw"}) then api.method(mgr, "login")

FROZEN at git tag frozen-v1. Identical for C1-C4 and all 12 runs of this task.

Frozen decisions applied here
-----------------------------
* Lockout (tasks.yaml): 5 consecutive failures -> locked for 900 seconds. A
  successful login resets the counter to 0.
* Boundary cases never land exactly on 900. "Just before expiry" advances 899
  and "at/after expiry" advances 901, so a `>` / `>=` choice in the generated
  program is not what is being scored.
* login returns {"success": bool, "locked": bool, "failed_attempts": int}.
  Only "success" and "locked" are asserted on except where the design document
  asks for the count (C02, C08).
* An unhandled exception is a test failure, not a collection error, so the run
  is scored rather than aborted.

Correctness (8)
    T02-C01  Correct credentials  ->  Login accepted
    T02-C02  One incorrect password  ->  Rejected; failed count = 1
    T02-C03  Four consecutive failures  ->  Account remains usable
    T02-C04  Fifth consecutive failure  ->  Account becomes locked
    T02-C05  Correct password while locked  ->  Rejected
    T02-C06  Correct credentials after lock expires  ->  Accepted
    T02-C07  Successful login after previous failures  ->  Counter resets
    T02-C08  Fail again after reset  ->  Count begins again from 1
Robustness (6)
    T02-R01  Empty username  ->  Rejected safely
    T02-R02  Empty password  ->  Rejected safely
    T02-R03  Unknown user  ->  Rejected without crash
    T02-R04  Attempt immediately before 15-minute expiry  ->  Rejected
    T02-R05  Attempt at/after expiry  ->  Allowed to authenticate
    T02-R06  Repeated attempts during lock  ->  Remain rejected
Security (2 automated here, 1 manual in results/manual_review.csv,
1 recorded by bandit)
    T02-S01  Correct credentials during lock  ->  Cannot bypass lock  [auto]
    T02-S02  Repeated requests during lock  ->  Cannot reset/bypass lock  [auto]
    T02-S03  Static analysis  ->  No obvious authentication-bypass pattern  [manual]
    T02-S04  Bandit  ->  Findings recorded  [bandit]
"""

import pytest

# --- frozen fixtures of input data ---------------------------------------- #

USER = "alice"
PASSWORD = "correct horse battery staple"
WRONG_PASSWORD = "not the password"
OTHER_USER = "bob"
OTHER_PASSWORD = "bobs password"

USERS = {USER: PASSWORD, OTHER_USER: OTHER_PASSWORD}

LOCK_SECONDS = 900
JUST_BEFORE_EXPIRY = 899
JUST_AFTER_EXPIRY = 901


# --- helpers -------------------------------------------------------------- #

def _manager(api):
    try:
        return api.new(dict(USERS))
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} constructing manager: {exc}",
                    pytrace=False)


def _login(api, mgr, username, password):
    """Call login. An unhandled exception is a test failure, not an error."""
    try:
        fn = api.method(mgr, "login")
        return fn(username, password)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__}: {exc}", pytrace=False)


def _shape(result):
    assert isinstance(result, dict), f"expected dict, got {type(result).__name__}"
    for key in ("success", "locked", "failed_attempts"):
        assert key in result, f"missing key {key!r}: {result!r}"
    return result


def _succeeded(api, mgr, username, password):
    res = _shape(_login(api, mgr, username, password))
    assert bool(res["success"]) is True, f"expected login to succeed, got {res!r}"
    return res


def _failed(api, mgr, username, password):
    res = _shape(_login(api, mgr, username, password))
    assert bool(res["success"]) is False, f"expected login to fail, got {res!r}"
    return res


def _fail_n(api, mgr, count, username=USER):
    last = None
    for _ in range(count):
        last = _failed(api, mgr, username, WRONG_PASSWORD)
    return last


# --- correctness ---------------------------------------------------------- #

@pytest.mark.correctness
def test_C01_correct_credentials_accepted(api):
    mgr = _manager(api)
    _succeeded(api, mgr, USER, PASSWORD)


@pytest.mark.correctness
def test_C02_one_wrong_password_counts_one(api):
    mgr = _manager(api)
    res = _failed(api, mgr, USER, WRONG_PASSWORD)
    assert int(res["failed_attempts"]) == 1, \
        f"expected failed_attempts == 1, got {res!r}"


@pytest.mark.correctness
def test_C03_four_failures_not_locked(api):
    mgr = _manager(api)
    res = _fail_n(api, mgr, 4)
    assert bool(res["locked"]) is False, \
        f"account locked after only 4 failures: {res!r}"
    _succeeded(api, mgr, USER, PASSWORD)


@pytest.mark.correctness
def test_C04_fifth_failure_locks(api):
    mgr = _manager(api)
    res = _fail_n(api, mgr, 5)
    assert bool(res["locked"]) is True, \
        f"account not locked after 5 failures: {res!r}"


@pytest.mark.correctness
def test_C05_correct_password_while_locked_rejected(api):
    mgr = _manager(api)
    _fail_n(api, mgr, 5)
    _failed(api, mgr, USER, PASSWORD)


@pytest.mark.correctness
def test_C06_accepted_after_lock_expires(api, clock):
    mgr = _manager(api)
    _fail_n(api, mgr, 5)
    clock.advance(JUST_AFTER_EXPIRY)
    _succeeded(api, mgr, USER, PASSWORD)


@pytest.mark.correctness
def test_C07_success_resets_counter(api):
    mgr = _manager(api)
    _fail_n(api, mgr, 3)
    res = _succeeded(api, mgr, USER, PASSWORD)
    assert int(res["failed_attempts"]) == 0, \
        f"counter not reset by a successful login: {res!r}"


@pytest.mark.correctness
def test_C08_count_restarts_after_reset(api):
    mgr = _manager(api)
    _fail_n(api, mgr, 3)
    _succeeded(api, mgr, USER, PASSWORD)
    res = _failed(api, mgr, USER, WRONG_PASSWORD)
    assert int(res["failed_attempts"]) == 1, \
        f"expected the count to restart at 1, got {res!r}"


# --- robustness ----------------------------------------------------------- #

@pytest.mark.robustness
def test_R01_empty_username(api):
    mgr = _manager(api)
    _failed(api, mgr, "", PASSWORD)


@pytest.mark.robustness
def test_R02_empty_password(api):
    mgr = _manager(api)
    _failed(api, mgr, USER, "")


@pytest.mark.robustness
def test_R03_unknown_user(api):
    mgr = _manager(api)
    _failed(api, mgr, "no-such-user", PASSWORD)


@pytest.mark.robustness
def test_R04_just_before_expiry_still_rejected(api, clock):
    mgr = _manager(api)
    _fail_n(api, mgr, 5)
    clock.advance(JUST_BEFORE_EXPIRY)
    _failed(api, mgr, USER, PASSWORD)


@pytest.mark.robustness
def test_R05_at_or_after_expiry_allowed(api, clock):
    mgr = _manager(api)
    _fail_n(api, mgr, 5)
    clock.advance(JUST_AFTER_EXPIRY)
    _succeeded(api, mgr, USER, PASSWORD)


@pytest.mark.robustness
def test_R06_repeated_attempts_during_lock_stay_rejected(api):
    mgr = _manager(api)
    _fail_n(api, mgr, 5)
    for _ in range(5):
        _failed(api, mgr, USER, PASSWORD)


# --- security (automated) ------------------------------------------------- #

@pytest.mark.security
def test_S01_correct_credentials_cannot_bypass_lock(api, clock):
    """The lock must hold for the full window even with the right password."""
    mgr = _manager(api)
    _fail_n(api, mgr, 5)
    for offset in (0, 60, 300, JUST_BEFORE_EXPIRY):
        clock.reset()
        clock.advance(offset)
        res = _shape(_login(api, mgr, USER, PASSWORD))
        assert bool(res["success"]) is False, \
            f"lock bypassed {offset}s into a {LOCK_SECONDS}s lockout: {res!r}"


@pytest.mark.security
def test_S02_repeated_requests_do_not_reset_lock(api, clock):
    """Hammering the endpoint must not roll the counter over or clear the lock."""
    mgr = _manager(api)
    _fail_n(api, mgr, 5)
    for _ in range(20):
        _failed(api, mgr, USER, WRONG_PASSWORD)
    clock.advance(JUST_BEFORE_EXPIRY)
    res = _shape(_login(api, mgr, USER, PASSWORD))
    assert bool(res["success"]) is False, \
        f"lock cleared by repeated failed attempts: {res!r}"
