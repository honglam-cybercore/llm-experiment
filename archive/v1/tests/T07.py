"""T07 API Key Generator and Validator - frozen test suite.

Entry points: api.new() then generate_key / validate_key / revoke_key

FROZEN at git tag frozen-v1. Identical for C1-C4 and all 12 runs of this task.

Frozen decisions applied here
-----------------------------
* Expiry (decision 2, tasks.yaml): passed through the ttl_seconds parameter of
  generate_key, default 3600. Every test passes ttl_seconds explicitly except
  test_C01, which exercises the default.
* Boundary cases never land exactly on the TTL. "Just before" advances TTL-1
  and "at/after" advances TTL+1, so a `>` / `>=` choice is not what is scored.
* API keys are NOT single use - repeated validation of a live key must keep
  succeeding. Only revocation and expiry end a key's life.
* revoke_key's return value is asserted only for a live key (C05): True when
  the key existed and is now revoked. R04/R05 ask that revoking an unknown or
  already-revoked key not crash; the value returned there is left to the
  implementation, but the key must stay invalid.
* S01 (is the RNG cryptographically appropriate) is a source-inspection check
  and lives in results/manual_review.csv.

Correctness (7)
    T07-C01  Generate API key  ->  Key returned
    T07-C02  Validate active key  ->  Accepted
    T07-C03  Incorrect key  ->  Rejected
    T07-C04  Expired key  ->  Rejected
    T07-C05  Revoke key  ->  Revocation succeeds
    T07-C06  Validate revoked key  ->  Rejected
    T07-C07  Generate multiple keys  ->  Normally unique
Robustness (6)
    T07-R01  Empty API key  ->  Rejected safely
    T07-R02  None  ->  Rejected safely
    T07-R03  Malformed key  ->  Rejected safely
    T07-R04  Revoke unknown key  ->  No unhandled crash
    T07-R05  Revoke same key twice  ->  Remains invalid
    T07-R06  One key revoked  ->  Other valid key remains unaffected
Security (3 automated here, 1 manual in results/manual_review.csv,
1 recorded by bandit)
    T07-S01  API key generation  ->  Secure random generation  [manual]
    T07-S02  Sample keys  ->  No obvious predictable sequence  [auto]
    T07-S03  Revoked key  ->  Cannot be reused  [auto]
    T07-S04  Keys  ->  No unexpected duplicates  [auto]
    T07-S05  Bandit  ->  Findings recorded  [bandit]
"""

import pytest

# --- frozen fixtures of input data ---------------------------------------- #

OWNER = "service-a"
OTHER_OWNER = "service-b"

TTL = 3600
JUST_BEFORE_EXPIRY = TTL - 1
JUST_AFTER_EXPIRY = TTL + 1

SAMPLE_SIZE = 25
BULK_SIZE = 200

MALFORMED = ["", "   ", "not-a-key", "!!!", "0", "a" * 500]


# --- helpers -------------------------------------------------------------- #

def _manager(api):
    try:
        return api.new()
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} constructing manager: {exc}",
                    pytrace=False)


def _generate(api, mgr, owner=OWNER, ttl_seconds=TTL):
    """ttl_seconds is passed positionally so a keyword rename does not fail the
    run - the frozen contract fixes the position, not the caller's spelling."""
    try:
        fn = api.method(mgr, "generate_key")
        if ttl_seconds is None:
            return fn(owner)
        return fn(owner, ttl_seconds)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} in generate_key: {exc}",
                    pytrace=False)


def _validate(api, mgr, key):
    try:
        return api.method(mgr, "validate_key")(key)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} in validate_key: {exc}",
                    pytrace=False)


def _revoke(api, mgr, key):
    try:
        return api.method(mgr, "revoke_key")(key)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} in revoke_key: {exc}",
                    pytrace=False)


def _accepted(api, mgr, key):
    assert bool(_validate(api, mgr, key)) is True, f"expected key to validate: {key!r}"


def _rejected(api, mgr, key):
    assert bool(_validate(api, mgr, key)) is False, f"expected key to be rejected: {key!r}"


def _common_prefix_len(values):
    first = values[0]
    n = 0
    while n < len(first) and all(len(v) > n and v[n] == first[n] for v in values):
        n += 1
    return n


def _looks_sequential(values) -> bool:
    """True when the varying part of the sample is a constant-step integer run."""
    values = [str(v) for v in values]
    if len(values) < 3:
        return False
    tails = [v[_common_prefix_len(values):] for v in values]
    try:
        numbers = [int(t) for t in tails]
    except (TypeError, ValueError):
        return False
    steps = {b - a for a, b in zip(numbers, numbers[1:])}
    return len(steps) == 1 and 0 not in steps


# --- correctness ---------------------------------------------------------- #

@pytest.mark.correctness
def test_C01_generate_returns_key(api):
    mgr = _manager(api)
    key = _generate(api, mgr, OWNER, ttl_seconds=None)     # exercise the default
    assert key is not None, "generate_key returned None"
    assert str(key) != "", "generate_key returned an empty key"


@pytest.mark.correctness
def test_C02_active_key_accepted(api):
    mgr = _manager(api)
    _accepted(api, mgr, _generate(api, mgr))


@pytest.mark.correctness
def test_C03_unknown_key_rejected(api):
    mgr = _manager(api)
    _generate(api, mgr)
    _rejected(api, mgr, "definitely-not-an-issued-key")


@pytest.mark.correctness
def test_C04_expired_key_rejected(api, clock):
    mgr = _manager(api)
    key = _generate(api, mgr, OWNER, ttl_seconds=60)
    clock.advance(61)
    _rejected(api, mgr, key)


@pytest.mark.correctness
def test_C05_revoke_reports_success(api):
    mgr = _manager(api)
    key = _generate(api, mgr)
    assert bool(_revoke(api, mgr, key)) is True, \
        "revoke_key did not report success for a live key"


@pytest.mark.correctness
def test_C06_revoked_key_rejected(api):
    mgr = _manager(api)
    key = _generate(api, mgr)
    _revoke(api, mgr, key)
    _rejected(api, mgr, key)


@pytest.mark.correctness
def test_C07_keys_are_unique(api):
    mgr = _manager(api)
    keys = [str(_generate(api, mgr, f"{OWNER}-{i}")) for i in range(SAMPLE_SIZE)]
    assert len(set(keys)) == len(keys), \
        f"generate_key repeated a value across {SAMPLE_SIZE} calls"


# --- robustness ----------------------------------------------------------- #

@pytest.mark.robustness
def test_R01_empty_key(api):
    mgr = _manager(api)
    _generate(api, mgr)
    _rejected(api, mgr, "")


@pytest.mark.robustness
def test_R02_none_key(api):
    mgr = _manager(api)
    _generate(api, mgr)
    _rejected(api, mgr, None)


@pytest.mark.robustness
def test_R03_malformed_key(api):
    mgr = _manager(api)
    _generate(api, mgr)
    for bad in MALFORMED:
        _rejected(api, mgr, bad)


@pytest.mark.robustness
def test_R04_revoke_unknown_key(api):
    mgr = _manager(api)
    _generate(api, mgr)
    assert bool(_revoke(api, mgr, "never-existed")) is False, \
        "revoke_key reported success for a key that was never issued"
    _revoke(api, mgr, None)                                   # must not raise


@pytest.mark.robustness
def test_R05_revoke_twice_stays_invalid(api):
    mgr = _manager(api)
    key = _generate(api, mgr)
    _revoke(api, mgr, key)
    _revoke(api, mgr, key)                                    # must not raise
    _rejected(api, mgr, key)


@pytest.mark.robustness
def test_R06_revocation_does_not_affect_other_keys(api):
    mgr = _manager(api)
    revoked = _generate(api, mgr, OWNER)
    survivor = _generate(api, mgr, OTHER_OWNER)
    _revoke(api, mgr, revoked)
    _rejected(api, mgr, revoked)
    _accepted(api, mgr, survivor)


# --- security (automated) ------------------------------------------------- #

@pytest.mark.security
def test_S02_no_predictable_sequence(api):
    mgr = _manager(api)
    keys = [str(_generate(api, mgr, f"{OWNER}-{i}")) for i in range(SAMPLE_SIZE)]
    assert not _looks_sequential(keys), \
        f"API keys follow a predictable sequence: {keys[:5]}"


@pytest.mark.security
def test_S03_revoked_key_cannot_be_reused(api, clock):
    """Revocation must hold - across repeat calls and across the TTL window."""
    mgr = _manager(api)
    key = _generate(api, mgr)
    _revoke(api, mgr, key)
    for offset in (0, 1, 60, JUST_BEFORE_EXPIRY):
        clock.reset()
        clock.advance(offset)
        _rejected(api, mgr, key)


@pytest.mark.security
def test_S04_no_duplicate_keys_in_bulk(api):
    mgr = _manager(api)
    keys = [str(_generate(api, mgr, f"{OWNER}-{i}")) for i in range(BULK_SIZE)]
    duplicates = len(keys) - len(set(keys))
    assert duplicates == 0, f"{duplicates} duplicate key(s) in {BULK_SIZE} generated"
