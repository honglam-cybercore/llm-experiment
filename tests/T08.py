"""T08 Log Redaction Engine - frozen test suite.

Difficulty: Medium.  Entry point:
    api.func("redact")(data, sensitive_keys, sensitive_patterns) -> object

Frozen configuration used by every test unless the test says otherwise
----------------------------------------------------------------------
    sensitive_keys      ["password", "token", "api_key", "secret"]
    sensitive_patterns  [r"Bearer [A-Za-z0-9._-]+", r"[0-9]{16}"]
    placeholder         "[REDACTED]"

Frozen decisions applied here
-----------------------------
* The placeholder is the exact string "[REDACTED]", which is what lets a test
  assert both halves of the job: the original value is gone AND something took
  its place. A solution that deletes the key instead fails, and so does one
  that leaves the value untouched.
* A sensitive KEY replaces its whole value. A sensitive PATTERN replaces only
  the matching part of a string value. C09 and C10 depend on that difference.
* Key matching is case-insensitive (C02, S05). Pattern matching is not
  case-folded, because the patterns are regular expressions and the caller
  controls their flags.
* The input must come back unmodified (C12). This is asserted by deep-copying
  the input before the call and comparing afterwards, so a solution that
  redacts in place fails even when its return value looks right.
* R08 (an invalid pattern) asserts only that the call is answered and that a
  broken pattern does not switch off key-based redaction. Whether the bad
  pattern is skipped or the whole pattern list is refused is the solution's
  choice; silently redacting nothing at all is not.
* R12 (an unsupported value type) likewise asserts no crash, and that a
  sensitive key still hides whatever odd object it holds.
* R08 deliberately leaves one thing open: given a broken pattern beside a good
  one, a solution may apply the good one or refuse the whole pattern list.
  Both are "handled safely" under the spec, so a mutant that drops every
  pattern on the first compile error survives this suite. What is not open is
  the key half of the job, which R08 does assert.
* The interface says the function never raises, so an exception is a test
  failure rather than a way to signal bad input.

Correctness (14)
    T08-C01  Top-level password field                      ->  Value redacted
    T08-C02  Top-level Password with different case        ->  Value redacted
    T08-C03  Nested token field                            ->  Value redacted
    T08-C04  Sensitive key inside a dict inside a list     ->  Value redacted
    T08-C05  Non-sensitive text field                      ->  Preserved
    T08-C06  Non-sensitive numeric field                   ->  Preserved
    T08-C07  Boolean value                                 ->  Preserved
    T08-C08  Null value                                    ->  Preserved
    T08-C09  Sensitive pattern inside a string             ->  Sensitive portion redacted
    T08-C10  Two sensitive patterns in one string          ->  Both redacted
    T08-C11  Nested list of strings                        ->  Patterns redacted correctly
    T08-C12  Original input checked after operation        ->  Original input unchanged
    T08-C13  Empty string value                            ->  Preserved
    T08-C14  Multiple sensitive keys at different levels   ->  All redacted
Robustness (12)
    T08-R01  Empty dictionary                              ->  Returned safely
    T08-R02  Empty list                                    ->  Returned safely
    T08-R03  Input is None                                 ->  Handled safely
    T08-R04  Input is a plain string                       ->  Processed safely
    T08-R05  Input is numeric                              ->  Preserved safely
    T08-R06  Empty sensitive-key list                      ->  No key-based redaction
    T08-R07  Empty pattern list                            ->  No pattern-based redaction
    T08-R08  Invalid pattern                               ->  Handled safely
    T08-R09  Deep nested object                            ->  Processed without failure
    T08-R10  Unicode values                                ->  Preserved/redacted consistently
    T08-R11  Repeated reference to same nested object      ->  Handled safely
    T08-R12  Unsupported object type                       ->  Handled safely
Security (7 automated here, 1 manual in results/manual_review.csv,
1 recorded by bandit)
    T08-S01  Password field                    ->  Original value absent from output  [auto]
    T08-S02  API key field                     ->  Original value absent from output  [auto]
    T08-S03  Bearer token inside text          ->  Token redacted                     [auto]
    T08-S04  Sensitive field nested deeply     ->  Still redacted                     [auto]
    T08-S05  Sensitive key with different case ->  Cannot bypass redaction            [auto]
    T08-S06  Processing failure                ->  Sensitive input not printed        [auto]
    T08-S07  Pattern containing code-like text ->  Treated as data/pattern only       [auto]
    T08-S08  Source inspection                 ->  No unsafe execution                [manual]
    T08-S09  Bandit                            ->  Findings recorded                  [bandit]
"""

import copy

import pytest

# --- frozen fixtures of input data ---------------------------------------- #

SENSITIVE_KEYS = ["password", "token", "api_key", "secret"]
SENSITIVE_PATTERNS = ["Bearer [A-Za-z0-9._-]+", "[0-9]{16}"]
REDACTED = "[REDACTED]"

PASSWORD = "zq7-canary-password"
TOKEN = "zq7-canary-token"
API_KEY = "zq7-canary-api-key"
BEARER = "Bearer abc123.def456-ghi"
CARD = "4111111111111111"


# --- helpers -------------------------------------------------------------- #

_DEFAULT = object()      # None is a real argument value, so it is not the sentinel


def _call(api, data, keys=_DEFAULT, patterns=_DEFAULT):
    """An unhandled exception is a test failure, not an error, so the run is
    scored rather than aborted."""
    if keys is _DEFAULT:
        keys = list(SENSITIVE_KEYS)
    if patterns is _DEFAULT:
        patterns = list(SENSITIVE_PATTERNS)
    try:
        return api.func("redact")(data, keys, patterns)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} for {data!r}: {exc}",
                    pytrace=False)


def _redact_unchanged(api, data, keys=_DEFAULT, patterns=_DEFAULT):
    """Redact, and prove the caller's structure was not touched on the way."""
    before = copy.deepcopy(data)
    result = _call(api, data, keys, patterns)
    assert data == before, (f"the input was modified in place: {before!r} "
                            f"became {data!r}")
    return result


def _text(value):
    return repr(value)


def _gone(result, *secrets):
    blob = _text(result)
    leaked = [s for s in secrets if s in blob]
    assert not leaked, f"secret(s) {leaked} still present in output: {blob}"


def _has_placeholder(result):
    assert REDACTED in _text(result), \
        f"nothing was replaced - expected {REDACTED!r} somewhere in {result!r}"


# --- correctness ---------------------------------------------------------- #

@pytest.mark.correctness
def test_C01_top_level_password(api):
    out = _redact_unchanged(api, {"password": PASSWORD, "user": "alice"})
    assert out["password"] == REDACTED, f"password not redacted: {out!r}"
    assert out["user"] == "alice", f"non-sensitive value changed: {out!r}"


@pytest.mark.correctness
def test_C02_key_case_insensitive(api):
    """Both sides are folded, not just the data. The configured list is
    lowercase in the frozen fixture, so the second half configures it in mixed
    case instead - a solution that folds only one side fails there."""
    for key in ("Password", "PASSWORD", "PassWord", "Api_Key", "TOKEN"):
        out = _redact_unchanged(api, {key: PASSWORD})
        assert out[key] == REDACTED, f"{key!r} not redacted: {out!r}"
    for configured in (["Password"], ["PASSWORD"], ["PassWord"]):
        out = _redact_unchanged(api, {"password": PASSWORD}, keys=configured)
        assert out["password"] == REDACTED, (
            f"configured as {configured!r}, data key 'password': {out!r}")


@pytest.mark.correctness
def test_C03_nested_token(api):
    data = {"session": {"token": TOKEN, "expires": 3600}}
    out = _redact_unchanged(api, data)
    assert out["session"]["token"] == REDACTED, f"nested token kept: {out!r}"
    assert out["session"]["expires"] == 3600


@pytest.mark.correctness
def test_C04_sensitive_key_in_dict_in_list(api):
    data = {"accounts": [{"name": "alice", "password": PASSWORD},
                         {"name": "bob", "password": "other-secret"}]}
    out = _redact_unchanged(api, data)
    assert out["accounts"][0]["password"] == REDACTED
    assert out["accounts"][1]["password"] == REDACTED
    assert out["accounts"][0]["name"] == "alice"


@pytest.mark.correctness
def test_C05_non_sensitive_text_preserved(api):
    data = {"message": "user alice signed in", "path": "/api/v1/login"}
    out = _redact_unchanged(api, data)
    assert out == data, f"non-sensitive text changed: {out!r}"


@pytest.mark.correctness
def test_C06_numeric_preserved(api):
    data = {"count": 42, "ratio": 1.5, "negative": -7}
    out = _redact_unchanged(api, data)
    assert out == data, f"numeric values changed: {out!r}"


@pytest.mark.correctness
def test_C07_boolean_preserved(api):
    data = {"ok": True, "failed": False}
    out = _redact_unchanged(api, data)
    assert out == data, f"booleans changed: {out!r}"
    assert out["ok"] is True and out["failed"] is False


@pytest.mark.correctness
def test_C08_null_preserved(api):
    data = {"result": None, "nested": {"value": None}}
    out = _redact_unchanged(api, data)
    assert out == data, f"nulls changed: {out!r}"


@pytest.mark.correctness
def test_C09_pattern_inside_string(api):
    data = {"message": f"calling api with {BEARER} now"}
    out = _redact_unchanged(api, data)
    _gone(out, BEARER)
    _has_placeholder(out)
    assert out["message"].startswith("calling api with "), \
        f"the surrounding text should survive: {out!r}"
    assert out["message"].endswith(" now"), \
        f"the surrounding text should survive: {out!r}"


@pytest.mark.correctness
def test_C10_two_patterns_in_one_string(api):
    """Two different patterns, and then the same pattern twice - a solution
    that replaces only the first match of each fails the second half."""
    data = {"message": f"{BEARER} paid with {CARD}"}
    out = _redact_unchanged(api, data)
    _gone(out, BEARER, CARD)
    assert out["message"].count(REDACTED) == 2, (
        f"expected both matches replaced: {out!r}")

    second = "Bearer zzz111.yyy222-xxx"
    data = {"message": f"first {BEARER} then {second}"}
    out = _redact_unchanged(api, data)
    _gone(out, BEARER, second)
    assert out["message"].count(REDACTED) == 2, (
        f"every match of a pattern is replaced, not just the first: {out!r}")


@pytest.mark.correctness
def test_C11_nested_list_of_strings(api):
    data = {"lines": [f"auth: {BEARER}", "plain line", [f"card {CARD}"]]}
    out = _redact_unchanged(api, data)
    _gone(out, BEARER, CARD)
    assert out["lines"][1] == "plain line", f"plain line changed: {out!r}"


@pytest.mark.correctness
def test_C12_input_unchanged(api):
    """The whole point of returning a new structure."""
    data = {"password": PASSWORD,
            "nested": {"token": TOKEN, "list": [{"secret": "s"}]},
            "message": f"auth {BEARER}"}
    before = copy.deepcopy(data)
    out = _call(api, data)
    assert data == before, f"input mutated: {before!r} -> {data!r}"
    assert out != data, "nothing was redacted at all"


@pytest.mark.correctness
def test_C13_empty_string_preserved(api):
    data = {"message": "", "nested": {"note": ""}}
    out = _redact_unchanged(api, data)
    assert out == data, f"empty strings changed: {out!r}"


@pytest.mark.correctness
def test_C14_multiple_keys_at_different_levels(api):
    data = {"password": PASSWORD,
            "a": {"token": TOKEN,
                  "b": {"api_key": API_KEY,
                        "c": [{"secret": "deep-secret"}]}}}
    out = _redact_unchanged(api, data)
    _gone(out, PASSWORD, TOKEN, API_KEY, "deep-secret")
    assert out["password"] == REDACTED
    assert out["a"]["token"] == REDACTED
    assert out["a"]["b"]["api_key"] == REDACTED
    assert out["a"]["b"]["c"][0]["secret"] == REDACTED


# --- robustness ----------------------------------------------------------- #

@pytest.mark.robustness
def test_R01_empty_dictionary(api):
    assert _redact_unchanged(api, {}) == {}


@pytest.mark.robustness
def test_R02_empty_list(api):
    assert _redact_unchanged(api, []) == []


@pytest.mark.robustness
def test_R03_input_is_none(api):
    assert _redact_unchanged(api, None) is None


@pytest.mark.robustness
def test_R04_input_is_plain_string(api):
    """A bare string is still scanned for patterns."""
    assert _redact_unchanged(api, "plain text") == "plain text"
    out = _redact_unchanged(api, f"auth {BEARER}")
    _gone(out, BEARER)


@pytest.mark.robustness
def test_R05_input_is_numeric(api):
    for value in (0, 42, -7, 1.5, True, False):
        assert _redact_unchanged(api, value) == value


@pytest.mark.robustness
def test_R06_empty_sensitive_key_list(api):
    """No keys configured means no key-based redaction - but the patterns
    still apply, so this cannot be mistaken for "redact nothing"."""
    data = {"password": PASSWORD, "message": f"auth {BEARER}"}
    out = _redact_unchanged(api, data, keys=[])
    assert out["password"] == PASSWORD, f"nothing configured it: {out!r}"
    _gone({"m": out["message"]}, BEARER)


@pytest.mark.robustness
def test_R07_empty_pattern_list(api):
    data = {"password": PASSWORD, "message": f"auth {BEARER}"}
    out = _redact_unchanged(api, data, patterns=[])
    assert out["message"] == f"auth {BEARER}", f"nothing configured it: {out!r}"
    assert out["password"] == REDACTED


@pytest.mark.robustness
def test_R08_invalid_pattern(api):
    """A pattern that will not compile is answered rather than raised, and it
    does not switch off the key-based half of the job."""
    for patterns in (["[", "Bearer [A-Za-z0-9._-]+"],
                     ["(unclosed"],
                     ["*"],
                     [None],
                     [42],
                     "Bearer"):
        data = {"password": PASSWORD, "message": f"auth {BEARER}"}
        out = _call(api, data, patterns=patterns)
        assert isinstance(out, dict), f"expected a dict back, got {out!r}"
        assert out.get("password") == REDACTED, \
            f"a broken pattern list must not disable key redaction: {out!r}"


@pytest.mark.robustness
def test_R09_deep_nesting(api):
    data = current = {}
    for _ in range(60):
        nxt = {}
        current["next"] = nxt
        current = nxt
    current["password"] = PASSWORD
    out = _redact_unchanged(api, data)
    probe = out
    for _ in range(60):
        probe = probe["next"]
    assert probe["password"] == REDACTED, "deep value not redacted"


@pytest.mark.robustness
def test_R10_unicode_values(api):
    data = {"message": "密碼是秘密",
            "password": "密碼-canary",
            "note": "café über"}
    out = _redact_unchanged(api, data)
    assert out["message"] == data["message"], f"unicode text changed: {out!r}"
    assert out["note"] == data["note"]
    assert out["password"] == REDACTED


@pytest.mark.robustness
def test_R11_repeated_reference(api):
    """The same dict appearing twice is redacted in both places."""
    shared = {"password": PASSWORD, "name": "alice"}
    data = {"first": shared, "second": shared, "list": [shared]}
    out = _redact_unchanged(api, data)
    for place in (out["first"], out["second"], out["list"][0]):
        assert place["password"] == REDACTED, f"missed one copy: {out!r}"
        assert place["name"] == "alice"


@pytest.mark.robustness
def test_R12_unsupported_object_type(api):
    """An odd value is answered, and a sensitive key still hides it."""
    for value in ({1, 2, 3}, object(), (1, 2), b"bytes-value"):
        out = _call(api, {"password": value, "other": value})
        assert isinstance(out, dict), f"expected a dict back, got {out!r}"
        assert out.get("password") == REDACTED, \
            f"a sensitive key must hide any value: {out!r}"


# --- security (automated) ------------------------------------------------- #

@pytest.mark.security
def test_S01_password_absent_from_output(api):
    out = _redact_unchanged(api, {"password": PASSWORD,
                                  "nested": {"password": PASSWORD}})
    _gone(out, PASSWORD)
    _has_placeholder(out)


@pytest.mark.security
def test_S02_api_key_absent_from_output(api):
    out = _redact_unchanged(api, {"api_key": API_KEY,
                                  "config": {"api_key": API_KEY}})
    _gone(out, API_KEY)
    _has_placeholder(out)


@pytest.mark.security
def test_S03_bearer_token_in_text(api):
    for message in (f"Authorization: {BEARER}",
                    f"retrying with {BEARER} after 401",
                    BEARER):
        out = _redact_unchanged(api, {"log": message})
        _gone(out, BEARER)


@pytest.mark.security
def test_S04_deeply_nested_sensitive_field(api):
    data = {"a": {"b": {"c": {"d": {"e": {"password": PASSWORD}}}}},
            "list": [[[{"token": TOKEN}]]]}
    out = _redact_unchanged(api, data)
    _gone(out, PASSWORD, TOKEN)


@pytest.mark.security
def test_S05_case_variant_key_cannot_bypass(api):
    """Changing the case of the key is the cheapest bypass there is."""
    for key in ("PASSWORD", "Password", "pAsSwOrD", "Api_Key", "API_KEY",
                "Token", "SECRET"):
        out = _redact_unchanged(api, {key: PASSWORD})
        _gone(out, PASSWORD)


@pytest.mark.security
def test_S06_failure_does_not_print_secrets(api, capfd):
    """Whatever goes wrong, the secret does not reach stdout or stderr."""
    capfd.readouterr()
    hostile = [
        {"password": PASSWORD, "bad": object()},
        {"password": PASSWORD, "cycle": None},
        [PASSWORD, {"token": TOKEN}],
        {"password": {"nested": PASSWORD}},
    ]
    for data in hostile:
        _call(api, data)
    _call(api, {"password": PASSWORD}, patterns=["["])
    _call(api, {"password": PASSWORD}, keys=None)
    _call(api, {"password": PASSWORD}, keys=42)
    captured = capfd.readouterr()
    stream = captured.out + captured.err
    for secret in (PASSWORD, TOKEN):
        assert secret not in stream, f"secret leaked to output: {stream!r}"


@pytest.mark.security
def test_S07_code_like_pattern_is_only_a_pattern(api, tmp_path, monkeypatch):
    """A pattern that looks like code is compiled, or refused, but never run.
    The cwd is empty and must stay empty."""
    monkeypatch.chdir(tmp_path)
    payloads = ["__import__('os').system('echo x > pwned.txt')",
                "$(touch pwned.txt)",
                "`touch pwned.txt`",
                "'; DROP TABLE logs; --",
                "{{7*7}}"]
    for payload in payloads:
        out = _call(api, {"password": PASSWORD, "message": "hello"},
                    patterns=[payload])
        assert isinstance(out, dict), f"expected a dict back, got {out!r}"
        out = _call(api, {"message": payload})
        assert isinstance(out, dict)
    leftovers = sorted(p.name for p in tmp_path.iterdir())
    assert leftovers == [], f"a pattern was executed, not matched: {leftovers}"
