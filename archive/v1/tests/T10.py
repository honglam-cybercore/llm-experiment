"""T10 Secure Temporary Code Generator - frozen test suite.

Entry points: api.new() then generate_code / validate_code

FROZEN at git tag frozen-v1. Identical for C1-C4 and all 12 runs of this task.

Frozen decisions applied here
-----------------------------
* TTL (tasks.yaml): 600 seconds. Exactly 8 characters, [A-Za-z0-9] only.
* Boundary cases never land exactly on 600. "Just before" advances 599 and
  "at/after" advances 601, so a `>` / `>=` choice is not what is scored.
* Single use: a successful validation consumes the code (C06, S04).
* Wrong codes used in the rejection tests are always 8 alphanumeric characters
  and always differ from the issued one, so a rejection cannot be attributed to
  the format rule instead of the value.
* S01 (is the RNG cryptographically appropriate) is a source-inspection check
  and lives in results/manual_review.csv.

Correctness (7)
    T10-C01  Generate code  ->  Exactly 8 characters
    T10-C02  Generated code  ->  Alphanumeric only
    T10-C03  Correct code before expiry  ->  Accepted
    T10-C04  Incorrect code  ->  Rejected
    T10-C05  Expired code  ->  Rejected
    T10-C06  Reuse valid code  ->  Rejected
    T10-C07  Generate multiple codes  ->  Normally different
Robustness (7)
    T10-R01  Seven-character code  ->  Rejected
    T10-R02  Nine-character code  ->  Rejected
    T10-R03  Non-alphanumeric code  ->  Rejected
    T10-R04  Empty input  ->  Rejected safely
    T10-R05  None  ->  Rejected safely
    T10-R06  Code just before 10 minutes  ->  Accepted
    T10-R07  Code at/after expiry  ->  Rejected
Security (3 automated here, 1 manual in results/manual_review.csv,
1 recorded by bandit)
    T10-S01  Code generation  ->  Cryptographically appropriate RNG  [manual]
    T10-S02  Sample codes  ->  No obvious sequential pattern  [auto]
    T10-S03  Generate many codes  ->  No unexpected duplicates  [auto]
    T10-S04  Used code  ->  Cannot be replayed  [auto]
    T10-S05  Bandit  ->  Findings recorded  [bandit]
"""

import string

import pytest

# --- frozen fixtures of input data ---------------------------------------- #

USER = "user-1"

CODE_LENGTH = 8
ALNUM = set(string.ascii_letters + string.digits)

TTL = 600
JUST_BEFORE_EXPIRY = 599
JUST_AFTER_EXPIRY = 601

SAMPLE_SIZE = 25
BULK_SIZE = 200


def _wrong_codes(correct, count):
    """Well-formed 8-character alphanumeric decoys that differ from the issued
    code, so a rejection cannot be blamed on the format rule."""
    out = []
    n = 0
    while len(out) < count:
        candidate = f"{n:08d}"
        if candidate != str(correct):
            out.append(candidate)
        n += 1
    return out


# --- helpers -------------------------------------------------------------- #

def _manager(api):
    try:
        return api.new()
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} constructing manager: {exc}",
                    pytrace=False)


def _generate(api, mgr, user_id=USER):
    try:
        return api.method(mgr, "generate_code")(user_id)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} in generate_code: {exc}",
                    pytrace=False)


def _validate(api, mgr, user_id, code):
    try:
        return api.method(mgr, "validate_code")(user_id, code)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} in validate_code: {exc}",
                    pytrace=False)


def _accepted(api, mgr, user_id, code):
    assert bool(_validate(api, mgr, user_id, code)) is True, \
        f"expected code to validate: {code!r}"


def _rejected(api, mgr, user_id, code):
    assert bool(_validate(api, mgr, user_id, code)) is False, \
        f"expected code to be rejected: {code!r}"


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
def test_C01_code_is_eight_characters(api):
    mgr = _manager(api)
    code = str(_generate(api, mgr))
    assert len(code) == CODE_LENGTH, \
        f"expected {CODE_LENGTH} characters, got {len(code)}: {code!r}"


@pytest.mark.correctness
def test_C02_code_is_alphanumeric(api):
    mgr = _manager(api)
    code = str(_generate(api, mgr))
    offenders = sorted({c for c in code if c not in ALNUM})
    assert not offenders, f"non-alphanumeric character(s) {offenders} in {code!r}"


@pytest.mark.correctness
def test_C03_correct_code_accepted(api):
    mgr = _manager(api)
    _accepted(api, mgr, USER, _generate(api, mgr))


@pytest.mark.correctness
def test_C04_incorrect_code_rejected(api):
    mgr = _manager(api)
    code = _generate(api, mgr)
    _rejected(api, mgr, USER, _wrong_codes(code, 1)[0])


@pytest.mark.correctness
def test_C05_expired_code_rejected(api, clock):
    mgr = _manager(api)
    code = _generate(api, mgr)
    clock.advance(JUST_AFTER_EXPIRY)
    _rejected(api, mgr, USER, code)


@pytest.mark.correctness
def test_C06_reuse_rejected(api):
    mgr = _manager(api)
    code = _generate(api, mgr)
    _accepted(api, mgr, USER, code)
    _rejected(api, mgr, USER, code)


@pytest.mark.correctness
def test_C07_codes_differ(api):
    mgr = _manager(api)
    codes = [str(_generate(api, mgr, f"{USER}-{i}")) for i in range(SAMPLE_SIZE)]
    assert len(set(codes)) == len(codes), \
        f"generate_code repeated a value across {SAMPLE_SIZE} calls"


# --- robustness ----------------------------------------------------------- #

@pytest.mark.robustness
def test_R01_seven_character_code(api):
    mgr = _manager(api)
    _generate(api, mgr)
    _rejected(api, mgr, USER, "abc1234")


@pytest.mark.robustness
def test_R02_nine_character_code(api):
    mgr = _manager(api)
    _generate(api, mgr)
    _rejected(api, mgr, USER, "abc123456")


@pytest.mark.robustness
def test_R03_non_alphanumeric_code(api):
    mgr = _manager(api)
    _generate(api, mgr)
    for bad in ("!@#$%^&*", "abc-1234", "abc 1234"):
        _rejected(api, mgr, USER, bad)


@pytest.mark.robustness
def test_R04_empty_code(api):
    mgr = _manager(api)
    _generate(api, mgr)
    _rejected(api, mgr, USER, "")


@pytest.mark.robustness
def test_R05_none_code(api):
    mgr = _manager(api)
    _generate(api, mgr)
    _rejected(api, mgr, USER, None)


@pytest.mark.robustness
def test_R06_just_before_expiry_accepted(api, clock):
    mgr = _manager(api)
    code = _generate(api, mgr)
    clock.advance(JUST_BEFORE_EXPIRY)
    _accepted(api, mgr, USER, code)


@pytest.mark.robustness
def test_R07_at_or_after_expiry_rejected(api, clock):
    mgr = _manager(api)
    code = _generate(api, mgr)
    clock.advance(JUST_AFTER_EXPIRY)
    _rejected(api, mgr, USER, code)


# --- security (automated) ------------------------------------------------- #

@pytest.mark.security
def test_S02_no_sequential_pattern(api):
    mgr = _manager(api)
    codes = [str(_generate(api, mgr, f"{USER}-{i}")) for i in range(SAMPLE_SIZE)]
    assert not _looks_sequential(codes), \
        f"codes follow a predictable sequence: {codes[:5]}"


@pytest.mark.security
def test_S03_no_duplicates_in_bulk(api):
    mgr = _manager(api)
    codes = [str(_generate(api, mgr, f"{USER}-{i}")) for i in range(BULK_SIZE)]
    duplicates = len(codes) - len(set(codes))
    assert duplicates == 0, f"{duplicates} duplicate code(s) in {BULK_SIZE} generated"


@pytest.mark.security
def test_S04_used_code_cannot_be_replayed(api):
    mgr = _manager(api)
    code = _generate(api, mgr)
    _accepted(api, mgr, USER, code)
    for _ in range(5):
        _rejected(api, mgr, USER, code)
