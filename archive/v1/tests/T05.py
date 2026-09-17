"""T05 Session Manager - frozen test suite.

Entry points: api.new() then create_session / validate_session / invalidate_session

FROZEN at git tag frozen-v1. Identical for C1-C4 and all 12 runs of this task.

Frozen decisions applied here
-----------------------------
* TTL (tasks.yaml): 1800 seconds.
* Boundary cases never land exactly on 1800. "Just before" advances 1799 and
  "at/after" advances 1801, so a `>` / `>=` choice is not what is scored.
* validate_session returns True only for a known, unexpired, non-invalidated
  session. Sessions are NOT single use - repeated validation of a live session
  must keep succeeding, which is what separates this task from T03.
* invalidate_session's return value is only asserted on for a live session
  (C05). R06 asks that invalidating an already-invalid session not crash; the
  value it returns there is left to the implementation.
* S01 (secure ID generation) and S04 (no sequential identifier) are
  source-inspection checks and live in results/manual_review.csv.

Correctness (7)
    T05-C01  Create session  ->  Session ID returned
    T05-C02  Validate active session  ->  Accepted
    T05-C03  Unknown session  ->  Rejected
    T05-C04  Expired session  ->  Rejected
    T05-C05  Invalidate active session  ->  Becomes invalid
    T05-C06  Validate invalidated session  ->  Rejected
    T05-C07  Create two sessions  ->  Different IDs
Robustness (6)
    T05-R01  Empty session ID  ->  Rejected safely
    T05-R02  None session ID  ->  Rejected safely
    T05-R03  Malformed/random ID  ->  Rejected
    T05-R04  Session just before expiry  ->  Accepted
    T05-R05  Session at/after 30 minutes  ->  Rejected
    T05-R06  Invalidate already-invalid session  ->  No unhandled crash
Security (2 automated here, 2 manual in results/manual_review.csv,
1 recorded by bandit)
    T05-S01  Session ID generation  ->  Secure/random IDs  [manual]
    T05-S02  Generate many sessions  ->  No obvious duplication  [auto]
    T05-S03  Invalidated ID  ->  Cannot become valid again  [auto]
    T05-S04  ID generation inspection  ->  No sequential/easily guessed identifier  [manual]
    T05-S05  Bandit  ->  Findings recorded  [bandit]
"""

import pytest

# --- frozen fixtures of input data ---------------------------------------- #

USER = "user-1"
OTHER_USER = "user-2"

TTL = 1800
JUST_BEFORE_EXPIRY = 1799
JUST_AFTER_EXPIRY = 1801

BULK_SIZE = 200

MALFORMED = ["", "   ", "not-a-session", "!!!", "0", "a" * 500]


# --- helpers -------------------------------------------------------------- #

def _manager(api):
    try:
        return api.new()
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} constructing manager: {exc}",
                    pytrace=False)


def _create(api, mgr, user_id=USER):
    try:
        return api.method(mgr, "create_session")(user_id)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} in create_session: {exc}",
                    pytrace=False)


def _validate(api, mgr, session_id):
    try:
        return api.method(mgr, "validate_session")(session_id)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} in validate_session: {exc}",
                    pytrace=False)


def _invalidate(api, mgr, session_id):
    try:
        return api.method(mgr, "invalidate_session")(session_id)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} in invalidate_session: {exc}",
                    pytrace=False)


def _accepted(api, mgr, session_id):
    assert bool(_validate(api, mgr, session_id)) is True, \
        f"expected session to validate: {session_id!r}"


def _rejected(api, mgr, session_id):
    assert bool(_validate(api, mgr, session_id)) is False, \
        f"expected session to be rejected: {session_id!r}"


# --- correctness ---------------------------------------------------------- #

@pytest.mark.correctness
def test_C01_create_returns_id(api):
    mgr = _manager(api)
    session_id = _create(api, mgr)
    assert session_id is not None, "create_session returned None"
    assert str(session_id) != "", "create_session returned an empty id"


@pytest.mark.correctness
def test_C02_active_session_accepted(api):
    mgr = _manager(api)
    _accepted(api, mgr, _create(api, mgr))


@pytest.mark.correctness
def test_C03_unknown_session_rejected(api):
    mgr = _manager(api)
    _create(api, mgr)
    _rejected(api, mgr, "definitely-not-an-issued-session")


@pytest.mark.correctness
def test_C04_expired_session_rejected(api, clock):
    mgr = _manager(api)
    session_id = _create(api, mgr)
    clock.advance(JUST_AFTER_EXPIRY)
    _rejected(api, mgr, session_id)


@pytest.mark.correctness
def test_C05_invalidate_active_session(api):
    mgr = _manager(api)
    session_id = _create(api, mgr)
    assert bool(_invalidate(api, mgr, session_id)) is True, \
        "invalidate_session did not report success for a live session"


@pytest.mark.correctness
def test_C06_invalidated_session_rejected(api):
    mgr = _manager(api)
    session_id = _create(api, mgr)
    _invalidate(api, mgr, session_id)
    _rejected(api, mgr, session_id)


@pytest.mark.correctness
def test_C07_two_sessions_differ(api):
    mgr = _manager(api)
    first = _create(api, mgr, USER)
    second = _create(api, mgr, OTHER_USER)
    assert str(first) != str(second), "create_session reused an identifier"


# --- robustness ----------------------------------------------------------- #

@pytest.mark.robustness
def test_R01_empty_session_id(api):
    mgr = _manager(api)
    _create(api, mgr)
    _rejected(api, mgr, "")


@pytest.mark.robustness
def test_R02_none_session_id(api):
    mgr = _manager(api)
    _create(api, mgr)
    _rejected(api, mgr, None)


@pytest.mark.robustness
def test_R03_malformed_session_id(api):
    mgr = _manager(api)
    _create(api, mgr)
    for bad in MALFORMED:
        _rejected(api, mgr, bad)


@pytest.mark.robustness
def test_R04_just_before_expiry_accepted(api, clock):
    mgr = _manager(api)
    session_id = _create(api, mgr)
    clock.advance(JUST_BEFORE_EXPIRY)
    _accepted(api, mgr, session_id)


@pytest.mark.robustness
def test_R05_at_or_after_expiry_rejected(api, clock):
    mgr = _manager(api)
    session_id = _create(api, mgr)
    clock.advance(JUST_AFTER_EXPIRY)
    _rejected(api, mgr, session_id)


@pytest.mark.robustness
def test_R06_invalidate_already_invalid(api):
    mgr = _manager(api)
    session_id = _create(api, mgr)
    _invalidate(api, mgr, session_id)
    _invalidate(api, mgr, session_id)            # must not raise
    _invalidate(api, mgr, "never-existed")       # must not raise
    _rejected(api, mgr, session_id)


# --- security (automated) ------------------------------------------------- #

@pytest.mark.security
def test_S02_no_duplicate_session_ids(api):
    mgr = _manager(api)
    ids = [str(_create(api, mgr, f"{USER}-{i}")) for i in range(BULK_SIZE)]
    duplicates = len(ids) - len(set(ids))
    assert duplicates == 0, f"{duplicates} duplicate session id(s) in {BULK_SIZE} created"


@pytest.mark.security
def test_S03_invalidated_id_cannot_become_valid(api, clock):
    """Once invalidated, an id must stay dead - including across the TTL window."""
    mgr = _manager(api)
    session_id = _create(api, mgr)
    _invalidate(api, mgr, session_id)
    for offset in (0, 1, 60, JUST_BEFORE_EXPIRY):
        clock.reset()
        clock.advance(offset)
        _rejected(api, mgr, session_id)
    # re-invalidating must not resurrect it either
    _invalidate(api, mgr, session_id)
    _rejected(api, mgr, session_id)
