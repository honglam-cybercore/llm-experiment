"""T06 One-Time Password (OTP) Validator - frozen test suite.

Entry points: api.new() then generate_otp / validate_otp

FROZEN at git tag frozen-v1. Identical for C1-C4 and all 12 runs of this task.

Frozen decisions applied here
-----------------------------
* TTL (tasks.yaml): 300 seconds. Six numeric digits. Maximum 5 incorrect
  attempts per issued OTP.
* Boundary cases never land exactly on 300. "Just before" advances 299 and
  "at/after" advances 301, so a `>` / `>=` choice is not what is scored.
* "Five incorrect attempts" (C07) means the limit is reached, so the sixth
  call - even with the correct OTP - must be rejected. C06 stops at four, where
  the correct OTP must still be accepted. That pair is the whole attempt-limit
  contract.
* Wrong OTPs used to burn attempts are always six digits and always differ from
  the issued one, so a rejection cannot be attributed to the format rule.
* S01 (is the RNG cryptographically appropriate) is a source-inspection check
  and lives in results/manual_review.csv.

Correctness (7)
    T06-C01  Generated OTP  ->  Exactly six numeric digits
    T06-C02  Correct OTP before expiry  ->  Accepted
    T06-C03  Incorrect OTP  ->  Rejected
    T06-C04  Expired OTP  ->  Rejected
    T06-C05  Reuse successful OTP  ->  Rejected
    T06-C06  Four incorrect attempts then correct OTP  ->  Correct OTP can still succeed
    T06-C07  Five incorrect attempts then correct OTP  ->  Validation stopped/rejected
Robustness (8)
    T06-R01  Five-character OTP  ->  Rejected
    T06-R02  Seven-character OTP  ->  Rejected
    T06-R03  Alphabetic characters  ->  Rejected
    T06-R04  Empty OTP  ->  Rejected safely
    T06-R05  None  ->  Rejected safely
    T06-R06  Correct OTP immediately before 5 minutes  ->  Accepted
    T06-R07  Correct OTP at/after expiry  ->  Rejected
    T06-R08  Additional attempts after five failures  ->  Rejected
Security (3 automated here, 1 manual in results/manual_review.csv,
1 recorded by bandit)
    T06-S01  OTP generation  ->  Secure random generation  [manual]
    T06-S02  Sample generated OTPs  ->  No obvious predictable sequence  [auto]
    T06-S03  Attempt limit  ->  Cannot bypass five-attempt maximum  [auto]
    T06-S04  Reuse  ->  Replay impossible  [auto]
    T06-S05  Bandit  ->  Findings recorded  [bandit]
"""

import pytest

# --- frozen fixtures of input data ---------------------------------------- #

USER = "user-1"

TTL = 300
JUST_BEFORE_EXPIRY = 299
JUST_AFTER_EXPIRY = 301

MAX_ATTEMPTS = 5
SAMPLE_SIZE = 25


def _wrong_otps(correct, count):
    """Six-digit decoys that differ from the issued OTP, so a rejection cannot
    be blamed on the format rule."""
    out = []
    n = 0
    while len(out) < count:
        candidate = f"{n:06d}"
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
        return api.method(mgr, "generate_otp")(user_id)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} in generate_otp: {exc}",
                    pytrace=False)


def _validate(api, mgr, user_id, otp):
    try:
        return api.method(mgr, "validate_otp")(user_id, otp)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} in validate_otp: {exc}",
                    pytrace=False)


def _accepted(api, mgr, user_id, otp):
    assert bool(_validate(api, mgr, user_id, otp)) is True, \
        f"expected OTP to validate: {otp!r}"


def _rejected(api, mgr, user_id, otp):
    assert bool(_validate(api, mgr, user_id, otp)) is False, \
        f"expected OTP to be rejected: {otp!r}"


def _burn(api, mgr, user_id, correct, count):
    for decoy in _wrong_otps(correct, count):
        _rejected(api, mgr, user_id, decoy)


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
def test_C01_otp_is_six_digits(api):
    mgr = _manager(api)
    otp = str(_generate(api, mgr))
    assert len(otp) == 6, f"expected 6 characters, got {len(otp)}: {otp!r}"
    assert otp.isdigit(), f"expected numeric digits only, got {otp!r}"


@pytest.mark.correctness
def test_C02_correct_otp_accepted(api):
    mgr = _manager(api)
    _accepted(api, mgr, USER, _generate(api, mgr))


@pytest.mark.correctness
def test_C03_incorrect_otp_rejected(api):
    mgr = _manager(api)
    otp = _generate(api, mgr)
    _rejected(api, mgr, USER, _wrong_otps(otp, 1)[0])


@pytest.mark.correctness
def test_C04_expired_otp_rejected(api, clock):
    mgr = _manager(api)
    otp = _generate(api, mgr)
    clock.advance(JUST_AFTER_EXPIRY)
    _rejected(api, mgr, USER, otp)


@pytest.mark.correctness
def test_C05_reuse_rejected(api):
    mgr = _manager(api)
    otp = _generate(api, mgr)
    _accepted(api, mgr, USER, otp)
    _rejected(api, mgr, USER, otp)


@pytest.mark.correctness
def test_C06_four_failures_then_correct_succeeds(api):
    mgr = _manager(api)
    otp = _generate(api, mgr)
    _burn(api, mgr, USER, otp, MAX_ATTEMPTS - 1)
    _accepted(api, mgr, USER, otp)


@pytest.mark.correctness
def test_C07_five_failures_stop_validation(api):
    mgr = _manager(api)
    otp = _generate(api, mgr)
    _burn(api, mgr, USER, otp, MAX_ATTEMPTS)
    _rejected(api, mgr, USER, otp)


# --- robustness ----------------------------------------------------------- #

@pytest.mark.robustness
def test_R01_five_character_otp(api):
    mgr = _manager(api)
    _generate(api, mgr)
    _rejected(api, mgr, USER, "12345")


@pytest.mark.robustness
def test_R02_seven_character_otp(api):
    mgr = _manager(api)
    _generate(api, mgr)
    _rejected(api, mgr, USER, "1234567")


@pytest.mark.robustness
def test_R03_alphabetic_otp(api):
    mgr = _manager(api)
    _generate(api, mgr)
    for bad in ("abcdef", "12a456", "!@#$%^"):
        _rejected(api, mgr, USER, bad)


@pytest.mark.robustness
def test_R04_empty_otp(api):
    mgr = _manager(api)
    _generate(api, mgr)
    _rejected(api, mgr, USER, "")


@pytest.mark.robustness
def test_R05_none_otp(api):
    mgr = _manager(api)
    _generate(api, mgr)
    _rejected(api, mgr, USER, None)


@pytest.mark.robustness
def test_R06_just_before_expiry_accepted(api, clock):
    mgr = _manager(api)
    otp = _generate(api, mgr)
    clock.advance(JUST_BEFORE_EXPIRY)
    _accepted(api, mgr, USER, otp)


@pytest.mark.robustness
def test_R07_at_or_after_expiry_rejected(api, clock):
    mgr = _manager(api)
    otp = _generate(api, mgr)
    clock.advance(JUST_AFTER_EXPIRY)
    _rejected(api, mgr, USER, otp)


@pytest.mark.robustness
def test_R08_attempts_after_limit_rejected(api):
    mgr = _manager(api)
    otp = _generate(api, mgr)
    _burn(api, mgr, USER, otp, MAX_ATTEMPTS)
    for _ in range(5):
        _rejected(api, mgr, USER, otp)


# --- security (automated) ------------------------------------------------- #

@pytest.mark.security
def test_S02_no_predictable_sequence(api):
    mgr = _manager(api)
    otps = [str(_generate(api, mgr, f"{USER}-{i}")) for i in range(SAMPLE_SIZE)]
    assert not _looks_sequential(otps), \
        f"OTPs follow a predictable sequence: {otps[:5]}"
    assert len(set(otps)) > 1, f"generate_otp returned a constant value: {otps[0]!r}"


@pytest.mark.security
def test_S03_attempt_limit_cannot_be_bypassed(api):
    """Neither the correct OTP nor a fresh burst of guesses may lift the limit."""
    mgr = _manager(api)
    otp = _generate(api, mgr)
    _burn(api, mgr, USER, otp, MAX_ATTEMPTS)
    for decoy in _wrong_otps(otp, 10):
        _rejected(api, mgr, USER, decoy)
    _rejected(api, mgr, USER, otp)


@pytest.mark.security
def test_S04_replay_impossible(api):
    mgr = _manager(api)
    otp = _generate(api, mgr)
    _accepted(api, mgr, USER, otp)
    for _ in range(5):
        _rejected(api, mgr, USER, otp)
