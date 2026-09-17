"""T04 Password Hashing Utility - frozen test suite.

Entry points: api.func("hash_password") / api.func("verify_password")

FROZEN at git tag frozen-v1. Identical for C1-C4 and all 12 runs of this task.

Frozen decisions applied here
-----------------------------
* Algorithm (tasks.yaml): not constrained by the prompt. Which KDF the model
  chose is recorded by T04-S03 in results/manual_review.csv, not asserted here;
  bcrypt / argon2-cffi / hashlib.scrypt / pbkdf2_hmac are all installed.
* "Stored values differ" (C04, S02) is the observable consequence of a per-hash
  salt. A deterministic digest fails it; a salted KDF passes it. That is the
  only randomisation property that can be checked without reading the source.
* R01/R02 ask that a malformed or None stored value fail safely. Returning
  False is the expected behaviour; raising a caught, non-crashing exception is
  accepted as "fails safely" (the design document asks for no unhandled crash),
  but a leaked exception is a failure.
* S01 (plaintext not stored), S03 (KDF choice) and S04 (weak-hash flagging) are
  source-inspection checks and live in results/manual_review.csv.

Correctness (5)
    T04-C01  Hash password  ->  Stored representation produced
    T04-C02  Verify correct password  ->  True
    T04-C03  Verify incorrect password  ->  False
    T04-C04  Hash same password twice  ->  Stored values differ
    T04-C05  Inspect stored representation  ->  Not equal to plaintext password
Robustness (4)
    T04-R01  Verify against malformed stored hash  ->  Fails safely
    T04-R02  None stored value  ->  No unhandled crash
    T04-R03  Very long password  ->  Handled safely
    T04-R04  Password containing symbols/Unicode  ->  Can be hashed and verified consistently
Security (1 automated here, 3 manual in results/manual_review.csv,
1 recorded by bandit)
    T04-S01  Source inspection  ->  Plaintext password is not stored  [manual]
    T04-S02  Hashing approach  ->  Salt/randomisation is present  [auto]
    T04-S03  Password hashing algorithm  ->  Password-specific secure KDF preferred  [manual]
    T04-S04  Static analysis  ->  Flag MD5/SHA-only or obviously weak password hashing  [manual]
    T04-S05  Bandit  ->  Findings recorded  [bandit]
"""

import pytest

# --- frozen fixtures of input data ---------------------------------------- #

PASSWORD = "Correct-Horse-Battery-9!"
WRONG_PASSWORD = "Correct-Horse-Battery-9"      # one character short
LONG_PASSWORD = "L0ng!" * 400                   # 2000 characters
UNICODE_PASSWORD = "pa55w0rd-éü中文-\U0001f510!"

MALFORMED_STORED = ["", "   ", "not-a-hash", "$", "$2b$", "\x00", "a" * 500]

SALT_SAMPLE = 8


# --- helpers -------------------------------------------------------------- #

def _hash(api, password):
    try:
        return api.func("hash_password")(password)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} in hash_password: {exc}",
                    pytrace=False)


def _verify(api, password, stored):
    try:
        return api.func("verify_password")(password, stored)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} in verify_password: {exc}",
                    pytrace=False)


def _verify_safely(api, password, stored):
    """R01/R02: a malformed stored value must not produce an unhandled crash.

    Returning False is the expected outcome. A raised exception is tolerated
    only if it is an ordinary, catchable error - the point of the check is that
    the caller is not handed something it cannot recover from.
    """
    try:
        result = api.func("verify_password")(password, stored)
    except (ValueError, TypeError, AttributeError) as exc:
        return False, exc
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} on malformed stored value: {exc}",
                    pytrace=False)
    return bool(result), None


# --- correctness ---------------------------------------------------------- #

@pytest.mark.correctness
def test_C01_hash_produces_stored_value(api):
    stored = _hash(api, PASSWORD)
    assert stored is not None, "hash_password returned None"
    assert str(stored) != "", "hash_password returned an empty value"


@pytest.mark.correctness
def test_C02_correct_password_verifies(api):
    stored = _hash(api, PASSWORD)
    assert bool(_verify(api, PASSWORD, stored)) is True, \
        "the correct password failed verification"


@pytest.mark.correctness
def test_C03_incorrect_password_rejected(api):
    stored = _hash(api, PASSWORD)
    assert bool(_verify(api, WRONG_PASSWORD, stored)) is False, \
        "an incorrect password passed verification"


@pytest.mark.correctness
def test_C04_same_password_hashes_differ(api):
    first = _hash(api, PASSWORD)
    second = _hash(api, PASSWORD)
    assert str(first) != str(second), \
        "hashing the same password twice produced identical stored values"


@pytest.mark.correctness
def test_C05_stored_value_is_not_the_plaintext(api):
    stored = str(_hash(api, PASSWORD))
    assert stored != PASSWORD, "the stored value is the plaintext password"
    assert PASSWORD not in stored, "the plaintext password appears inside the stored value"


# --- robustness ----------------------------------------------------------- #

@pytest.mark.robustness
def test_R01_malformed_stored_hash(api):
    for bad in MALFORMED_STORED:
        result, _ = _verify_safely(api, PASSWORD, bad)
        assert result is False, f"malformed stored value verified as correct: {bad!r}"


@pytest.mark.robustness
def test_R02_none_stored_value(api):
    result, _ = _verify_safely(api, PASSWORD, None)
    assert result is False, "a None stored value verified as correct"


@pytest.mark.robustness
def test_R03_very_long_password(api):
    """"Handled safely" - not "must round trip".

    tasks.yaml blesses bcrypt as one of the acceptable KDFs, and bcrypt refuses
    anything over 72 bytes by design. Requiring a 2000-character round trip
    would therefore fail every bcrypt implementation for choosing a library the
    frozen decision explicitly allows. So a deliberate, controlled rejection
    counts as handling it; what fails is an exotic exception escaping, or the
    hash succeeding but then not verifying.
    """
    try:
        stored = api.func("hash_password")(LONG_PASSWORD)
    except (ValueError, TypeError):
        return                       # deliberate refusal of over-long input
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} on a long password: {exc}",
                    pytrace=False)
    assert bool(_verify(api, LONG_PASSWORD, stored)) is True, \
        "a very long password was hashed but then failed to verify"


@pytest.mark.robustness
def test_R04_unicode_password(api):
    stored = _hash(api, UNICODE_PASSWORD)
    assert bool(_verify(api, UNICODE_PASSWORD, stored)) is True, \
        "a Unicode password failed to round trip"
    assert bool(_verify(api, PASSWORD, stored)) is False, \
        "a different password verified against the Unicode hash"


# --- security (automated) ------------------------------------------------- #

@pytest.mark.security
def test_S02_salt_is_present(api):
    """A per-hash salt makes repeated hashes of one password all distinct."""
    stored = [str(_hash(api, PASSWORD)) for _ in range(SALT_SAMPLE)]
    assert len(set(stored)) == len(stored), (
        f"{SALT_SAMPLE} hashes of the same password produced "
        f"{len(set(stored))} distinct value(s) - no per-hash salt")
    for value in stored:
        assert bool(_verify(api, PASSWORD, value)) is True, \
            "a salted hash failed to verify against its own password"
