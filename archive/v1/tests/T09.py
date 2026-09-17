"""T09 Data Encryption Utility - frozen test suite.

Entry points: api.func("generate_key") / api.func("encrypt") / api.func("decrypt")

FROZEN at git tag frozen-v1. Identical for C1-C4 and all 12 runs of this task.

Frozen decisions applied here
-----------------------------
* Failure mode (tasks.yaml): decrypt signals failure by RAISING any exception.
  Returning None, or returning a wrong plaintext, is a failure of T09-C03 /
  T09-C04. That is why the helpers below distinguish "raised" from "returned
  something wrong" - both are wrong, but only the first is correct behaviour.
* encrypt takes a str and returns the ciphertext; decrypt returns the original
  str. Comparisons are on the exact round-tripped string.
* C05 ("ciphertexts differ") is the observable consequence of a random nonce or
  IV. Whether the construction actually uses one is T09-S03, a source check.
* S01 (confidentiality), S03 (random nonce/IV), S04 (no hard-coded key) and
  S05 (insecure algorithms/modes) are source-inspection checks and live in
  results/manual_review.csv. Only S02 - does the construction detect a modified
  ciphertext - can be observed from the outside, so it is the only automated one.

Correctness (5)
    T09-C01  Encrypt normal text  ->  Ciphertext returned
    T09-C02  Decrypt using correct key  ->  Original text returned
    T09-C03  Decrypt using incorrect key  ->  Failure
    T09-C04  Modify encrypted data  ->  Decryption fails
    T09-C05  Encrypt same plaintext twice  ->  Ciphertexts differ
Robustness (5)
    T09-R01  Empty plaintext  ->  Can be handled safely
    T09-R02  Unicode text  ->  Round trip correctly
    T09-R03  Long text  ->  Round trip correctly
    T09-R04  Corrupted/truncated ciphertext  ->  Rejected safely
    T09-R05  Completely malformed ciphertext  ->  Rejected without crash
Security (1 automated here, 4 manual in results/manual_review.csv,
1 recorded by bandit)
    T09-S01  Encryption construction  ->  Provides confidentiality  [manual]
    T09-S02  Ciphertext modification  ->  Authentication/integrity check detects change  [auto]
    T09-S03  Encryption randomness  ->  Random nonce/IV or equivalent  [manual]
    T09-S04  Source inspection  ->  No hard-coded encryption key  [manual]
    T09-S05  Static analysis  ->  Insecure algorithms/modes flagged  [manual]
    T09-S06  Bandit  ->  Findings recorded  [bandit]
"""

import pytest

# --- frozen fixtures of input data ---------------------------------------- #

PLAINTEXT = "the quick brown fox jumps over the lazy dog"
UNICODE_TEXT = "héllo wörld - 中文 - \U0001f512 - ünïcodé"
LONG_TEXT = "long payload segment. " * 2000        # ~44 KB
EMPTY_TEXT = ""

MALFORMED = [b"", b"not-a-ciphertext", b"\x00\x01\x02\x03",
             b"a" * 500, "a string not bytes", None]


# --- helpers -------------------------------------------------------------- #

def _key(api):
    try:
        return api.func("generate_key")()
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} in generate_key: {exc}",
                    pytrace=False)


def _encrypt(api, plaintext, key):
    try:
        return api.func("encrypt")(plaintext, key)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} in encrypt: {exc}",
                    pytrace=False)


def _decrypt(api, ciphertext, key):
    """Decrypt and require success - used only where the inputs are correct."""
    try:
        return api.func("decrypt")(ciphertext, key)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} decrypting valid input: {exc}",
                    pytrace=False)


def _decrypt_must_fail(api, ciphertext, key, what):
    """The frozen failure mode: decrypt must RAISE. Returning None or a wrong
    plaintext is not 'failing' - it is silently accepting bad input."""
    try:
        result = api.func("decrypt")(ciphertext, key)
    except Exception:                                         # noqa: BLE001
        return                                                # correct behaviour
    pytest.fail(f"decrypt did not raise for {what}; it returned {result!r}",
                pytrace=False)


def _as_bytes(value):
    if isinstance(value, bytes):
        return bytearray(value)
    if isinstance(value, bytearray):
        return bytearray(value)
    if isinstance(value, str):
        return bytearray(value.encode("utf-8", "surrogateescape"))
    return bytearray(bytes(value))


def _rebuild(original, mutated):
    """Hand the modified ciphertext back in whatever type encrypt produced."""
    if isinstance(original, str):
        return mutated.decode("utf-8", "surrogateescape")
    return bytes(mutated)


def _flip_last_byte(ciphertext):
    raw = _as_bytes(ciphertext)
    if not raw:
        pytest.fail("encrypt returned an empty ciphertext", pytrace=False)
    raw[-1] ^= 0x01
    return _rebuild(ciphertext, raw)


# --- correctness ---------------------------------------------------------- #

@pytest.mark.correctness
def test_C01_encrypt_returns_ciphertext(api):
    key = _key(api)
    ciphertext = _encrypt(api, PLAINTEXT, key)
    assert ciphertext is not None, "encrypt returned None"
    assert len(_as_bytes(ciphertext)) > 0, "encrypt returned an empty ciphertext"
    assert PLAINTEXT.encode("utf-8") not in bytes(_as_bytes(ciphertext)), \
        "the plaintext appears verbatim inside the ciphertext"


@pytest.mark.correctness
def test_C02_round_trip_with_correct_key(api):
    key = _key(api)
    ciphertext = _encrypt(api, PLAINTEXT, key)
    assert _decrypt(api, ciphertext, key) == PLAINTEXT, \
        "decrypt did not return the original plaintext"


@pytest.mark.correctness
def test_C03_wrong_key_fails(api):
    key = _key(api)
    other_key = _key(api)
    if str(key) == str(other_key):
        pytest.fail("generate_key returned the same key twice", pytrace=False)
    ciphertext = _encrypt(api, PLAINTEXT, key)
    _decrypt_must_fail(api, ciphertext, other_key, "an incorrect key")


@pytest.mark.correctness
def test_C04_modified_ciphertext_fails(api):
    key = _key(api)
    ciphertext = _encrypt(api, PLAINTEXT, key)
    _decrypt_must_fail(api, _flip_last_byte(ciphertext), key,
                       "a ciphertext with one flipped bit")


@pytest.mark.correctness
def test_C05_same_plaintext_encrypts_differently(api):
    key = _key(api)
    first = _encrypt(api, PLAINTEXT, key)
    second = _encrypt(api, PLAINTEXT, key)
    assert bytes(_as_bytes(first)) != bytes(_as_bytes(second)), \
        "encrypting the same plaintext twice produced identical ciphertexts"


# --- robustness ----------------------------------------------------------- #

@pytest.mark.robustness
def test_R01_empty_plaintext(api):
    key = _key(api)
    ciphertext = _encrypt(api, EMPTY_TEXT, key)
    assert _decrypt(api, ciphertext, key) == EMPTY_TEXT, \
        "an empty plaintext did not round trip"


@pytest.mark.robustness
def test_R02_unicode_round_trip(api):
    key = _key(api)
    ciphertext = _encrypt(api, UNICODE_TEXT, key)
    assert _decrypt(api, ciphertext, key) == UNICODE_TEXT, \
        "Unicode text did not round trip"


@pytest.mark.robustness
def test_R03_long_text_round_trip(api):
    key = _key(api)
    ciphertext = _encrypt(api, LONG_TEXT, key)
    assert _decrypt(api, ciphertext, key) == LONG_TEXT, \
        "long text did not round trip"


@pytest.mark.robustness
def test_R04_truncated_ciphertext_rejected(api):
    key = _key(api)
    ciphertext = _encrypt(api, PLAINTEXT, key)
    raw = _as_bytes(ciphertext)
    for cut in (1, len(raw) // 2, len(raw) - 1):
        if cut <= 0:
            continue
        _decrypt_must_fail(api, _rebuild(ciphertext, raw[:cut]), key,
                           f"a ciphertext truncated to {cut} byte(s)")


@pytest.mark.robustness
def test_R05_malformed_ciphertext_rejected(api):
    key = _key(api)
    _encrypt(api, PLAINTEXT, key)
    for bad in MALFORMED:
        _decrypt_must_fail(api, bad, key, f"malformed input {bad!r}")


# --- security (automated) ------------------------------------------------- #

@pytest.mark.security
def test_S02_integrity_check_detects_modification(api):
    """Every byte position matters: flipping a bit anywhere must be detected."""
    key = _key(api)
    ciphertext = _encrypt(api, PLAINTEXT, key)
    raw = _as_bytes(ciphertext)
    positions = sorted({0, len(raw) // 4, len(raw) // 2, len(raw) - 1})
    for pos in positions:
        if pos < 0 or pos >= len(raw):
            continue
        mutated = bytearray(raw)
        mutated[pos] ^= 0xFF
        _decrypt_must_fail(api, _rebuild(ciphertext, mutated), key,
                           f"a ciphertext modified at byte {pos}")
