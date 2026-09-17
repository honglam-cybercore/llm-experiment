"""T01 Password Policy Validator - frozen test suite.

Difficulty: Easy.  Entry point:
    api.func("validate_password")(password, policy, username=None) -> dict

Frozen decisions applied here
-----------------------------
* A rule applies only when its key is present in the policy, and a failed rule
  is named in "errors" by that key. So C04 asserts "min_length" appears, not
  that some prose mentions length. This is what makes R09 ("all relevant
  failed rules identified") checkable at all.
* Every password below violates exactly ONE rule of BASE_POLICY, except R09
  and the multi-failure security cases, so a red test points at one rule.
* "max_repeated_characters" is the longest run of one identical character that
  is still allowed, so 2 permits "ss" and rejects "sss".
* An empty policy enables no rules, so anything passes it. That is the defined
  semantics, not a bypass, and no test treats it as one. S04 and S05 use
  policies that keep a real rule and add junk beside it.
* The interface says the function never raises, so an exception is a test
  failure rather than an alternative way to reject.
* R11 (min_length > max_length) cannot be made discriminating, and is left as
  written. When the bounds contradict each other no password satisfies both,
  so a solution that notices the contradiction and one that merely fails each
  password against whichever bound it breaks are externally identical. A
  mutant deleting the min>max sanity check survives this suite, knowingly: the
  spec asks only for "rejected safely", and requiring BOTH bounds to be named
  would score an implementation detail rather than behaviour.

Correctness (10)
    T01-C01  Password satisfies all enabled rules             ->  Accepted
    T01-C02  Password exactly at minimum length               ->  Accepted
    T01-C03  Password exactly at maximum length               ->  Accepted
    T01-C04  Password below minimum length                    ->  Rejected
    T01-C05  Password above maximum length                    ->  Rejected
    T01-C06  Required uppercase missing                       ->  Rejected
    T01-C07  Required number missing                          ->  Rejected
    T01-C08  Username appears in password                     ->  Rejected
    T01-C09  Username appears with different case             ->  Rejected
    T01-C10  Repeated characters exceed configured maximum    ->  Rejected
Robustness (12)
    T01-R01  Empty password                                   ->  Rejected safely
    T01-R02  Password is None                                 ->  Rejected safely
    T01-R03  Password is a non-string value                   ->  Rejected safely without crash
    T01-R04  Policy is missing                                ->  Rejected safely
    T01-R05  Policy has invalid type                          ->  Rejected safely
    T01-R06  Username is empty                                ->  Handled safely
    T01-R07  Username is None                                 ->  Handled safely
    T01-R08  Unicode characters in password                   ->  Processed consistently
    T01-R09  Password fails multiple rules                    ->  All relevant failed rules identified
    T01-R10  Invalid negative minimum or maximum length       ->  Rejected safely
    T01-R11  Minimum length greater than maximum length       ->  Rejected safely
    T01-R12  Invalid repeated-character limit                 ->  Rejected safely
Security (5 automated here, 2 manual in results/manual_review.csv,
1 recorded by bandit)
    T01-S01  Validation failure           ->  Original password is not returned in error output   [auto]
    T01-S02  Capture stdout and stderr    ->  Password is not printed                             [auto]
    T01-S03  Source inspection            ->  Password is not unnecessarily logged                [manual]
    T01-S04  Malformed policy attempts to disable validation ->  Validation cannot be bypassed    [auto]
    T01-S05  Unknown policy option        ->  Does not silently weaken security rules             [auto]
    T01-S06  Password-like input containing code ->  Treated only as data                         [auto]
    T01-S07  Source inspection            ->  No eval() or exec() used                            [manual]
    T01-S08  Bandit                       ->  Findings recorded                                   [bandit]
"""

import pytest

# --- frozen fixtures of input data ---------------------------------------- #

BASE_POLICY = {
    "min_length": 8,
    "max_length": 20,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_digit": True,
    "require_special": True,
    "forbid_username": True,
    "max_repeated_characters": 2,
}

USERNAME = "alice"

GOOD = "Str0ng!Pass"                    # 11 chars, every rule satisfied
AT_MIN = "Aa1!bcde"                     # exactly 8
AT_MAX = "Aa1!bcdefghijklmnopq"         # exactly 20
BELOW_MIN = "Aa1!bcd"                   # 7
ABOVE_MAX = "Aa1!bcdefghijklmnopqr"     # 21
NO_UPPER = "ab1!cdef"
NO_DIGIT = "Ab!cdefg"
HAS_USERNAME = "alice12!A"              # contains "alice"
HAS_USERNAME_CASED = "ALICE12!a"        # contains "ALICE"
TOO_REPEATED = "Baaa1!cd"               # "aaa" is a run of 3, limit is 2

MULTI_FAIL = "abc"                      # short, no upper, no digit, no special

# distinctive, and invalid (too short), so S01/S02 exercise the error path
SECRET_PW = "zq7-canary-leak-value"

NON_STRING = [0, 1, True, False, [], {}, b"Str0ng!Pass", object()]


# --- helpers -------------------------------------------------------------- #

def _policy(**overrides):
    merged = dict(BASE_POLICY)
    merged.update(overrides)
    return merged


_DEFAULT = object()      # None is a real policy value, so it cannot be the sentinel


def _call(api, password, policy=_DEFAULT, username=USERNAME):
    """An unhandled exception is a test failure, not an error, so the run is
    scored rather than aborted."""
    fn = api.func("validate_password")
    if policy is _DEFAULT:
        policy = dict(BASE_POLICY)
    try:
        return fn(password, policy, username)
    except TypeError:
        try:
            return fn(password, policy)          # username is optional
        except Exception as exc:                 # noqa: BLE001
            pytest.fail(f"unhandled {type(exc).__name__}: {exc}", pytrace=False)
    except Exception as exc:                     # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__}: {exc}", pytrace=False)


def _shape(result):
    assert isinstance(result, dict), f"expected dict, got {type(result).__name__}"
    assert "valid" in result, f"missing key 'valid': {result!r}"
    assert "errors" in result, f"missing key 'errors': {result!r}"
    return result


def _accepted(api, password, policy=_DEFAULT, username=USERNAME):
    res = _shape(_call(api, password, policy, username))
    assert bool(res["valid"]) is True, f"expected {password!r} accepted, got {res!r}"
    assert len(list(res["errors"])) == 0, f"expected no errors, got {res['errors']!r}"
    return res


def _rejected(api, password, policy=_DEFAULT, username=USERNAME):
    res = _shape(_call(api, password, policy, username))
    assert bool(res["valid"]) is False, f"expected {password!r} rejected, got {res!r}"
    return res


def _errors_text(result):
    try:
        return " ".join(str(e) for e in result["errors"]).lower()
    except TypeError:
        return str(result["errors"]).lower()


def _rules_named(result, *rules):
    text = _errors_text(result)
    missing = [r for r in rules if r.lower() not in text]
    assert not missing, (f"failed rule(s) {missing} not identified in "
                         f"errors={result['errors']!r}")


# --- correctness ---------------------------------------------------------- #

@pytest.mark.correctness
def test_C01_all_rules_satisfied(api):
    _accepted(api, GOOD)


@pytest.mark.correctness
def test_C02_exactly_minimum_length(api):
    _accepted(api, AT_MIN)


@pytest.mark.correctness
def test_C03_exactly_maximum_length(api):
    _accepted(api, AT_MAX)


@pytest.mark.correctness
def test_C04_below_minimum_length(api):
    _rules_named(_rejected(api, BELOW_MIN), "min_length")


@pytest.mark.correctness
def test_C05_above_maximum_length(api):
    _rules_named(_rejected(api, ABOVE_MAX), "max_length")


@pytest.mark.correctness
def test_C06_uppercase_missing(api):
    _rules_named(_rejected(api, NO_UPPER), "require_uppercase")


@pytest.mark.correctness
def test_C07_digit_missing(api):
    _rules_named(_rejected(api, NO_DIGIT), "require_digit")


@pytest.mark.correctness
def test_C08_username_in_password(api):
    _rules_named(_rejected(api, HAS_USERNAME), "forbid_username")


@pytest.mark.correctness
def test_C09_username_in_password_different_case(api):
    _rules_named(_rejected(api, HAS_USERNAME_CASED), "forbid_username")


@pytest.mark.correctness
def test_C10_repeated_characters_over_limit(api):
    _rules_named(_rejected(api, TOO_REPEATED), "max_repeated_characters")


# --- robustness ----------------------------------------------------------- #

@pytest.mark.robustness
def test_R01_empty_password(api):
    _rejected(api, "")


@pytest.mark.robustness
def test_R02_password_is_none(api):
    _rejected(api, None)


@pytest.mark.robustness
def test_R03_password_is_non_string(api):
    for bad in NON_STRING:
        _rejected(api, bad)


@pytest.mark.robustness
def test_R04_policy_is_missing(api):
    """A missing policy is not an empty policy. There is nothing to validate
    against, so nothing is accepted - and the function still answers rather
    than raising. The empty-policy case is deliberately not asserted here:
    `{}` enables no rules, which is defined behaviour, not a failure."""
    for password in (GOOD, BELOW_MIN, ""):
        res = _shape(_call(api, password, None))
        assert bool(res["valid"]) is False, \
            f"a missing policy must not accept {password!r}: {res!r}"


@pytest.mark.robustness
def test_R05_policy_has_invalid_type(api):
    for bad in ("min_length=8", 8, [("min_length", 8)], True, object()):
        res = _shape(_call(api, BELOW_MIN, bad))
        assert bool(res["valid"]) is False, \
            f"policy {bad!r} is not a policy; nothing may be accepted under it: {res!r}"


@pytest.mark.robustness
def test_R06_username_is_empty(api):
    """An empty username forbids nothing, so a password that is otherwise fine
    stays fine and one that breaks another rule still fails."""
    _accepted(api, GOOD, username="")
    _rejected(api, BELOW_MIN, username="")


@pytest.mark.robustness
def test_R07_username_is_none(api):
    _accepted(api, GOOD, username=None)
    _rejected(api, BELOW_MIN, username=None)


@pytest.mark.robustness
def test_R08_unicode_password(api):
    """Length is counted in characters, not bytes, so an 8-character password
    of non-ASCII letters plus the required classes behaves like any other."""
    _accepted(api, "Pa1!éüñç")
    _rejected(api, "Pa1!é")                      # 5 characters, under the minimum


@pytest.mark.robustness
def test_R09_multiple_failed_rules(api):
    res = _rejected(api, MULTI_FAIL)
    _rules_named(res, "min_length", "require_uppercase", "require_digit",
                 "require_special")


@pytest.mark.robustness
def test_R10_negative_length_bounds(api):
    for policy in (_policy(min_length=-1), _policy(max_length=-5),
                   _policy(min_length=-3, max_length=-1)):
        res = _shape(_call(api, GOOD, policy))
        assert bool(res["valid"]) is False, \
            f"a policy with a negative bound is invalid: {policy} -> {res!r}"


@pytest.mark.robustness
def test_R11_minimum_greater_than_maximum(api):
    """Contradictory bounds reject everything - short, long and in between.
    See the note in the module docstring: this cannot distinguish a solution
    that detects the contradiction from one that simply fails each password
    against a bound."""
    policy = _policy(min_length=20, max_length=8)
    for password in (AT_MIN, GOOD, AT_MAX, ""):
        res = _shape(_call(api, password, policy))
        assert bool(res["valid"]) is False, (
            f"no password can satisfy min_length > max_length: "
            f"{password!r} -> {res!r}")


@pytest.mark.robustness
def test_R12_invalid_repeated_character_limit(api):
    for value in (0, -1, "two", None, 1.5, []):
        res = _shape(_call(api, GOOD, _policy(max_repeated_characters=value)))
        assert bool(res["valid"]) is False, \
            f"max_repeated_characters={value!r} is not a usable limit: {res!r}"


# --- security (automated) ------------------------------------------------- #

@pytest.mark.security
def test_S01_password_not_in_returned_errors(api):
    res = _shape(_call(api, SECRET_PW))
    assert bool(res["valid"]) is False, f"canary password should be rejected: {res!r}"
    assert SECRET_PW not in repr(res), f"password leaked in result: {res!r}"


@pytest.mark.security
def test_S02_password_not_in_stdout_or_stderr(api, capfd):
    capfd.readouterr()
    _call(api, SECRET_PW)
    _call(api, SECRET_PW, _policy(min_length=100))
    captured = capfd.readouterr()
    stream = captured.out + captured.err
    assert SECRET_PW not in stream, f"password leaked to output: {stream!r}"


@pytest.mark.security
def test_S04_malformed_policy_cannot_disable_validation(api):
    """Junk beside a real rule must not switch the real rule off. Each policy
    below still carries min_length=8, so BELOW_MIN has to stay rejected."""
    for extra in ({"skip_validation": True}, {"valid": True}, {"disabled": True},
                  {"__all_ok__": True}, {"enforce": False},
                  {"require_uppercase": False, "bypass": True}):
        policy = _policy(**extra)
        res = _shape(_call(api, BELOW_MIN, policy))
        assert bool(res["valid"]) is False, \
            f"validation bypassed by {extra}: {res!r}"


@pytest.mark.security
def test_S05_unknown_policy_option_does_not_weaken_rules(api):
    """An unrecognised option is not a licence to stop enforcing the ones that
    are recognised."""
    policy = _policy(unknown_rule="whatever", another_unknown=123)
    _rejected(api, BELOW_MIN, policy)
    _rejected(api, NO_UPPER, policy)
    _rejected(api, HAS_USERNAME, policy)


@pytest.mark.security
def test_S06_code_like_password_is_only_data(api, tmp_path, monkeypatch):
    """A password that looks like code is a string and nothing else. The cwd is
    empty and must stay empty: anything appearing in it means the input was
    executed rather than inspected."""
    monkeypatch.chdir(tmp_path)
    for password in ("__import__('os').system('echo pwned > pwned.txt')",
                     "'; DROP TABLE users; --",
                     "{{7*7}}",
                     "$(touch pwned.txt)",
                     "eval('1+1')"):
        res = _shape(_call(api, password))
        assert isinstance(bool(res["valid"]), bool)
    leftovers = sorted(p.name for p in tmp_path.iterdir())
    assert leftovers == [], f"input was executed, not validated: {leftovers}"
