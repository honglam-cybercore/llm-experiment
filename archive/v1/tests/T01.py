"""T01 User Registration Validator - frozen test suite.

Entry point: api.func("validate_registration")(username, email, password) -> dict
             {"valid": bool, "errors": list[str]}

FROZEN at git tag frozen-v1. Identical for C1-C4 and all 12 runs of this task.

Frozen decisions applied here
-----------------------------
* Email rule (decision 1): valid iff exactly one "@", non-empty local part,
  and a domain containing at least one ".". Every email used below is
  unambiguous under that rule.
* Password rule: >= 8 characters AND at least one uppercase, one lowercase,
  one digit, one special character. Each password case below violates exactly
  one sub-rule so a failure points at one rule only.
* "Rule identified" is checked by substring, not by exact string equality:
  the design document asks that the *failed validation rule* be identifiable,
  so both "username" and "username must be 3 to 20 characters" count. Checked
  only where the document asks for it (C04, C05, R05).
* C06-C11 assert rejection only, as written in the design document. They do
  not additionally require the field name, so a model that rejects without
  naming the rule still scores those.

Correctness (11)
    T01-C01  Valid username, email and password  ->  Accepted
    T01-C02  Username exactly 3 characters  ->  Accepted
    T01-C03  Username exactly 20 characters  ->  Accepted
    T01-C04  Username with 2 characters  ->  Rejected with username rule identified
    T01-C05  Username with 21 characters  ->  Rejected with username rule identified
    T01-C06  Password shorter than 8 characters  ->  Rejected
    T01-C07  Password without uppercase  ->  Rejected
    T01-C08  Password without lowercase  ->  Rejected
    T01-C09  Password without number  ->  Rejected
    T01-C10  Password without special character  ->  Rejected
    T01-C11  Clearly invalid email, e.g. missing @  ->  Rejected

Robustness (5)
    T01-R01  Empty username  ->  Rejected without crash
    T01-R02  Empty email  ->  Rejected without crash
    T01-R03  Empty password  ->  Rejected without crash
    T01-R04  None/missing required value  ->  Rejected without unhandled exception
    T01-R05  Multiple invalid fields  ->  Rejected and failed rules identified

Security (2 automated here, 1 manual in results/manual_review.csv,
1 recorded by bandit)
    T01-S01  Invalid password produces an error  ->  Original password does not appear in error   [auto]
    T01-S02  Capture stdout/stderr  ->  Password does not appear   [auto]
    T01-S03  Static review  ->  Password is not unnecessarily logged/printed   [manual]
    T01-S04  Bandit  ->  Findings recorded   [bandit]
"""

import pytest

# --- frozen fixtures of input data ---------------------------------------- #

GOOD_USER = "alice"
GOOD_EMAIL = "alice@example.com"
GOOD_PASSWORD = "Passw0rd!"

USER_MIN = "abc"                    # exactly 3
USER_MAX = "a" * 20                 # exactly 20
USER_SHORT = "ab"                   # 2
USER_LONG = "a" * 21                # 21

PW_TOO_SHORT = "Ab1!xyz"            # 7 chars, all four classes present
PW_NO_UPPER = "passw0rd!"
PW_NO_LOWER = "PASSW0RD!"
PW_NO_DIGIT = "Password!"
PW_NO_SPECIAL = "Password1"

BAD_EMAIL_NO_AT = "aliceexample.com"

# distinctive, and invalid (no uppercase), so S01/S02 exercise the error path
SECRET_PW = "zq7-canary-leak-value"


# --- helpers -------------------------------------------------------------- #

def _call(api, username, email, password):
    """Call the entry point. An unhandled exception is a test failure, not an
    error, so the run is scored rather than aborted."""
    fn = api.func("validate_registration")
    try:
        return fn(username, email, password)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__}: {exc}", pytrace=False)


def _shape(result):
    assert isinstance(result, dict), f"expected dict, got {type(result).__name__}"
    assert "valid" in result, f"missing key 'valid': {result!r}"
    assert "errors" in result, f"missing key 'errors': {result!r}"
    return result


def _accepted(api, username, email, password):
    res = _shape(_call(api, username, email, password))
    assert bool(res["valid"]) is True, f"expected accepted, got {res!r}"
    assert len(list(res["errors"])) == 0, f"expected no errors, got {res['errors']!r}"
    return res


def _rejected(api, username, email, password):
    res = _shape(_call(api, username, email, password))
    assert bool(res["valid"]) is False, f"expected rejected, got {res!r}"
    return res


def _errors_text(result):
    try:
        return " ".join(str(e) for e in result["errors"]).lower()
    except TypeError:
        return str(result["errors"]).lower()


def _names_identified(result, *fields):
    text = _errors_text(result)
    missing = [f for f in fields if f not in text]
    assert not missing, (f"failed rule(s) {missing} not identified in "
                         f"errors={result['errors']!r}")


# --- correctness ---------------------------------------------------------- #

@pytest.mark.correctness
def test_C01_all_valid(api):
    _accepted(api, GOOD_USER, GOOD_EMAIL, GOOD_PASSWORD)


@pytest.mark.correctness
def test_C02_username_exactly_3(api):
    _accepted(api, USER_MIN, GOOD_EMAIL, GOOD_PASSWORD)


@pytest.mark.correctness
def test_C03_username_exactly_20(api):
    _accepted(api, USER_MAX, GOOD_EMAIL, GOOD_PASSWORD)


@pytest.mark.correctness
def test_C04_username_too_short(api):
    res = _rejected(api, USER_SHORT, GOOD_EMAIL, GOOD_PASSWORD)
    _names_identified(res, "username")


@pytest.mark.correctness
def test_C05_username_too_long(api):
    res = _rejected(api, USER_LONG, GOOD_EMAIL, GOOD_PASSWORD)
    _names_identified(res, "username")


@pytest.mark.correctness
def test_C06_password_too_short(api):
    _rejected(api, GOOD_USER, GOOD_EMAIL, PW_TOO_SHORT)


@pytest.mark.correctness
def test_C07_password_no_uppercase(api):
    _rejected(api, GOOD_USER, GOOD_EMAIL, PW_NO_UPPER)


@pytest.mark.correctness
def test_C08_password_no_lowercase(api):
    _rejected(api, GOOD_USER, GOOD_EMAIL, PW_NO_LOWER)


@pytest.mark.correctness
def test_C09_password_no_number(api):
    _rejected(api, GOOD_USER, GOOD_EMAIL, PW_NO_DIGIT)


@pytest.mark.correctness
def test_C10_password_no_special_character(api):
    _rejected(api, GOOD_USER, GOOD_EMAIL, PW_NO_SPECIAL)


@pytest.mark.correctness
def test_C11_email_missing_at(api):
    _rejected(api, GOOD_USER, BAD_EMAIL_NO_AT, GOOD_PASSWORD)


# --- robustness ----------------------------------------------------------- #

@pytest.mark.robustness
def test_R01_empty_username(api):
    _rejected(api, "", GOOD_EMAIL, GOOD_PASSWORD)


@pytest.mark.robustness
def test_R02_empty_email(api):
    _rejected(api, GOOD_USER, "", GOOD_PASSWORD)


@pytest.mark.robustness
def test_R03_empty_password(api):
    _rejected(api, GOOD_USER, GOOD_EMAIL, "")


@pytest.mark.robustness
def test_R04_none_values(api):
    for username, email, password in (
        (None, GOOD_EMAIL, GOOD_PASSWORD),
        (GOOD_USER, None, GOOD_PASSWORD),
        (GOOD_USER, GOOD_EMAIL, None),
        (None, None, None),
    ):
        _rejected(api, username, email, password)


@pytest.mark.robustness
def test_R05_multiple_invalid_fields(api):
    res = _rejected(api, USER_SHORT, BAD_EMAIL_NO_AT, PW_NO_SPECIAL)
    _names_identified(res, "username", "email", "password")


# --- security (automated) ------------------------------------------------- #

@pytest.mark.security
def test_S01_password_not_in_returned_errors(api):
    res = _shape(_call(api, GOOD_USER, GOOD_EMAIL, SECRET_PW))
    assert bool(res["valid"]) is False, f"canary password should be rejected: {res!r}"
    assert SECRET_PW not in repr(res), f"password leaked in result: {res!r}"


@pytest.mark.security
def test_S02_password_not_in_stdout_or_stderr(api, capfd):
    capfd.readouterr()
    _call(api, GOOD_USER, GOOD_EMAIL, SECRET_PW)
    _call(api, USER_SHORT, BAD_EMAIL_NO_AT, SECRET_PW)
    captured = capfd.readouterr()
    stream = captured.out + captured.err
    assert SECRET_PW not in stream, f"password leaked to output: {stream!r}"
