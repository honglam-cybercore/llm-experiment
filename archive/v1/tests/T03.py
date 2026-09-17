"""T03 Token Generator and Validator - frozen test suite.

Entry points: api.new() then api.method(mgr, "generate_token") / "validate_token"

FROZEN at git tag frozen-v1. Identical for C1-C4 and all 12 runs of this task.

Frozen decisions applied here
-----------------------------
* TTL (tasks.yaml): 1800 seconds, single use. A successful validation consumes
  the token.
* Boundary cases never land exactly on 1800. "Just before" advances 1799 and
  "at/after" advances 1801, so a `>` / `>=` choice is not what is scored.
* validate_token returns True only for a known, unexpired, unused token; every
  assertion below is on the truthiness of that return value.
* S01 (is the RNG cryptographically appropriate) is a source-inspection check
  and lives in results/manual_review.csv, not here.

Correctness (7)
    T03-C01  Generate token  ->  Token returned
    T03-C02  Validate correct token before expiry  ->  Accepted
    T03-C03  Incorrect token  ->  Rejected
    T03-C04  Expired token  ->  Rejected
    T03-C05  Use token once  ->  First use accepted
    T03-C06  Reuse same token  ->  Rejected
    T03-C07  Generate multiple tokens  ->  Normally different
Robustness (6)
    T03-R01  Empty token  ->  Rejected safely
    T03-R02  None token  ->  Rejected safely
    T03-R03  Malformed token  ->  Rejected safely
    T03-R04  Token just before 30 minutes  ->  Accepted
    T03-R05  Token at/after 30 minutes  ->  Rejected
    T03-R06  Large number of generated tokens  ->  No unexpected failure
Security (3 automated here, 1 manual in results/manual_review.csv,
1 recorded by bandit)
    T03-S01  RNG inspection  ->  Cryptographically appropriate randomness used  [manual]
    T03-S02  Generate a sample of tokens  ->  No obvious sequential/predictable pattern  [auto]
    T03-S03  Generate many tokens  ->  No unexpected duplicates  [auto]
    T03-S04  Used token  ->  Cannot be replayed  [auto]
    T03-S05  Bandit  ->  Findings recorded  [bandit]
"""

import pytest

# --- frozen fixtures of input data ---------------------------------------- #

USER = "user-1"
OTHER_USER = "user-2"

TTL = 1800
JUST_BEFORE_EXPIRY = 1799
JUST_AFTER_EXPIRY = 1801

SAMPLE_SIZE = 25
BULK_SIZE = 200

MALFORMED = ["", "   ", "not-a-token", "!!!", "0", "a" * 500]


# --- helpers -------------------------------------------------------------- #

def _manager(api):
    try:
        return api.new()
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} constructing manager: {exc}",
                    pytrace=False)


def _generate(api, mgr, user_id=USER):
    try:
        return api.method(mgr, "generate_token")(user_id)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} in generate_token: {exc}",
                    pytrace=False)


def _validate(api, mgr, token):
    """Call validate_token. An unhandled exception is a failure, not an error."""
    try:
        return api.method(mgr, "validate_token")(token)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} in validate_token: {exc}",
                    pytrace=False)


def _accepted(api, mgr, token):
    assert bool(_validate(api, mgr, token)) is True, \
        f"expected token to validate: {token!r}"


def _rejected(api, mgr, token):
    assert bool(_validate(api, mgr, token)) is False, \
        f"expected token to be rejected: {token!r}"


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
def test_C01_generate_returns_token(api):
    mgr = _manager(api)
    token = _generate(api, mgr)
    assert token is not None, "generate_token returned None"
    assert str(token) != "", "generate_token returned an empty token"


@pytest.mark.correctness
def test_C02_valid_token_accepted(api):
    mgr = _manager(api)
    _accepted(api, mgr, _generate(api, mgr))


@pytest.mark.correctness
def test_C03_unknown_token_rejected(api):
    mgr = _manager(api)
    _generate(api, mgr)
    _rejected(api, mgr, "definitely-not-an-issued-token")


@pytest.mark.correctness
def test_C04_expired_token_rejected(api, clock):
    mgr = _manager(api)
    token = _generate(api, mgr)
    clock.advance(JUST_AFTER_EXPIRY)
    _rejected(api, mgr, token)


@pytest.mark.correctness
def test_C05_first_use_accepted(api):
    mgr = _manager(api)
    _accepted(api, mgr, _generate(api, mgr))


@pytest.mark.correctness
def test_C06_reuse_rejected(api):
    mgr = _manager(api)
    token = _generate(api, mgr)
    _accepted(api, mgr, token)
    _rejected(api, mgr, token)


@pytest.mark.correctness
def test_C07_tokens_differ(api):
    mgr = _manager(api)
    tokens = [_generate(api, mgr, f"{USER}-{i}") for i in range(SAMPLE_SIZE)]
    assert len(set(map(str, tokens))) == len(tokens), \
        f"generate_token repeated a value across {SAMPLE_SIZE} calls"


# --- robustness ----------------------------------------------------------- #

@pytest.mark.robustness
def test_R01_empty_token(api):
    mgr = _manager(api)
    _generate(api, mgr)
    _rejected(api, mgr, "")


@pytest.mark.robustness
def test_R02_none_token(api):
    mgr = _manager(api)
    _generate(api, mgr)
    _rejected(api, mgr, None)


@pytest.mark.robustness
def test_R03_malformed_token(api):
    mgr = _manager(api)
    _generate(api, mgr)
    for bad in MALFORMED:
        _rejected(api, mgr, bad)


@pytest.mark.robustness
def test_R04_just_before_expiry_accepted(api, clock):
    mgr = _manager(api)
    token = _generate(api, mgr)
    clock.advance(JUST_BEFORE_EXPIRY)
    _accepted(api, mgr, token)


@pytest.mark.robustness
def test_R05_at_or_after_expiry_rejected(api, clock):
    mgr = _manager(api)
    token = _generate(api, mgr)
    clock.advance(JUST_AFTER_EXPIRY)
    _rejected(api, mgr, token)


@pytest.mark.robustness
def test_R06_bulk_generation(api):
    mgr = _manager(api)
    tokens = [_generate(api, mgr, f"{USER}-{i}") for i in range(BULK_SIZE)]
    assert all(t is not None and str(t) != "" for t in tokens), \
        "generate_token produced an empty value under bulk generation"


# --- security (automated) ------------------------------------------------- #

@pytest.mark.security
def test_S02_no_sequential_pattern(api):
    mgr = _manager(api)
    tokens = [str(_generate(api, mgr, f"{USER}-{i}")) for i in range(SAMPLE_SIZE)]
    assert not _looks_sequential(tokens), \
        f"tokens follow a predictable sequence: {tokens[:5]}"


@pytest.mark.security
def test_S03_no_duplicates_in_bulk(api):
    mgr = _manager(api)
    tokens = [str(_generate(api, mgr, f"{USER}-{i}")) for i in range(BULK_SIZE)]
    duplicates = len(tokens) - len(set(tokens))
    assert duplicates == 0, f"{duplicates} duplicate token(s) in {BULK_SIZE} generated"


@pytest.mark.security
def test_S04_used_token_cannot_be_replayed(api):
    mgr = _manager(api)
    token = _generate(api, mgr)
    _accepted(api, mgr, token)
    for _ in range(5):
        _rejected(api, mgr, token)
