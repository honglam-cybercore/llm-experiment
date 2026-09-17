"""T03 Email Header Validator - frozen test suite.

Difficulty: Easy.  Entry point:
    api.func("validate_email_headers")(sender, recipients, subject, headers, config) -> dict

Frozen configuration used by every test unless the test says otherwise
----------------------------------------------------------------------
    max_recipients       3
    max_subject_length   40
    allow_empty_subject  True

Frozen decisions applied here
-----------------------------
* A failed check is named in "errors" by the check that failed: "sender",
  "recipients", "subject" or "headers".
* "Invalid email structure" is kept to cases no reasonable rule accepts: no
  "@", more than one "@", an empty local part, an empty domain, a domain with
  no dot, or whitespace inside the address. Nothing in the suite depends on a
  contested corner of RFC 5322 such as quoted local parts or IP-literal
  domains, so a simple validator and a strict one both pass.
* CRLF is the point of this task. S01-S06 treat any CR or LF anywhere in a
  sender, recipient, subject, header name or header value as header injection
  and require rejection. A solution that strips the newline and carries on
  fails: the spec says rejected, and stripping quietly changes what the caller
  asked to send.
* R06 and R09 say "handled safely", not "rejected", so they assert only that a
  missing subject or missing header map is answered without raising, and that
  it does not turn into a bypass. allow_empty_subject=True is the frozen
  default, so a None subject behaves like an empty one.
* The interface says the function never raises, so an exception is a test
  failure rather than another way to reject.

Correctness (12)
    T03-C01  Valid sender, one valid recipient and valid subject  ->  Accepted
    T03-C02  Multiple valid recipients below limit                ->  Accepted
    T03-C03  Recipient count exactly at maximum                   ->  Accepted
    T03-C04  Recipient count above maximum                        ->  Rejected
    T03-C05  Invalid sender email structure                       ->  Rejected
    T03-C06  Invalid recipient email structure                    ->  Rejected
    T03-C07  One invalid address among multiple recipients        ->  Rejected
    T03-C08  Subject exactly at maximum length                    ->  Accepted
    T03-C09  Subject above maximum length                         ->  Rejected
    T03-C10  Empty subject when empty subjects are allowed        ->  Accepted
    T03-C11  Valid custom headers                                 ->  Accepted
    T03-C12  Multiple valid custom headers                        ->  Accepted
Robustness (12)
    T03-R01  Empty sender                                         ->  Rejected safely
    T03-R02  Sender is None                                       ->  Rejected safely
    T03-R03  Empty recipient list                                 ->  Rejected safely
    T03-R04  Recipient list is None                               ->  Rejected safely
    T03-R05  Recipients value is wrong type                       ->  Rejected safely
    T03-R06  Subject is None                                      ->  Handled safely
    T03-R07  Subject is non-string                                ->  Rejected safely
    T03-R08  Custom headers are malformed                         ->  Rejected safely
    T03-R09  Custom headers are None                              ->  Handled safely
    T03-R10  Unicode subject                                      ->  Processed consistently
    T03-R11  Unicode display characters in email                  ->  Handled safely
    T03-R12  Invalid maximum recipient configuration              ->  Rejected safely
Security (7 automated here, 1 manual in results/manual_review.csv,
1 recorded by bandit)
    T03-S01  Subject contains CR LF Bcc:                          ->  Rejected  [auto]
    T03-S02  Custom header value contains CR LF                   ->  Rejected  [auto]
    T03-S03  Custom header name contains newline                  ->  Rejected  [auto]
    T03-S04  Sender contains CRLF injection                       ->  Rejected  [auto]
    T03-S05  Recipient contains CRLF injection                    ->  Rejected  [auto]
    T03-S06  Header value contains multiple injected headers      ->  Rejected  [auto]
    T03-S07  Input contains code-like text                        ->  Treated only as data  [auto]
    T03-S08  Source inspection                                    ->  No command or code execution  [manual]
    T03-S09  Bandit                                               ->  Findings recorded  [bandit]
"""

import pytest

# --- frozen fixtures of input data ---------------------------------------- #

MAX_RECIPIENTS = 3
MAX_SUBJECT = 40

BASE_CONFIG = {
    "max_recipients": MAX_RECIPIENTS,
    "max_subject_length": MAX_SUBJECT,
    "allow_empty_subject": True,
}

SENDER = "alice@example.com"
RECIPIENT = "bob@example.com"
RECIPIENTS_2 = ["bob@example.com", "carol@example.com"]
RECIPIENTS_AT_MAX = ["bob@example.com", "carol@example.com", "dave@example.com"]
RECIPIENTS_OVER_MAX = RECIPIENTS_AT_MAX + ["erin@example.com"]

SUBJECT = "Quarterly report"
SUBJECT_AT_MAX = "x" * MAX_SUBJECT
SUBJECT_OVER_MAX = "x" * (MAX_SUBJECT + 1)

HEADERS = {"X-Campaign": "spring-2026"}
HEADERS_MANY = {
    "X-Campaign": "spring-2026",
    "X-Priority": "3",
    "Reply-To": "noreply@example.com",
}

# Unambiguously malformed under any reasonable rule.
BAD_ADDRESSES = [
    "no-at-sign.example.com",
    "two@@example.com",
    "two@signs@example.com",
    "@example.com",
    "alice@",
    "alice@localdomain",
    "alice bob@example.com",
    "alice@exa mple.com",
    "",
    "   ",
]

CRLF_PAYLOADS = [
    "\r\nBcc: attacker@evil.com",
    "\nBcc: attacker@evil.com",
    "\rBcc: attacker@evil.com",
    "\r\n\r\nInjected body",
    chr(13) + chr(10) + "X-Injected: 1",
]

NON_STRING = [0, 1, True, False, [], {}, b"alice@example.com", object()]


# --- helpers -------------------------------------------------------------- #

_DEFAULT = object()      # None is a real argument value, so it is not the sentinel


def _config(**overrides):
    merged = dict(BASE_CONFIG)
    merged.update(overrides)
    return merged


def _call(api, sender=SENDER, recipients=_DEFAULT, subject=SUBJECT,
          headers=_DEFAULT, config=_DEFAULT):
    """An unhandled exception is a test failure, not an error, so the run is
    scored rather than aborted."""
    if recipients is _DEFAULT:
        recipients = [RECIPIENT]
    if headers is _DEFAULT:
        headers = dict(HEADERS)
    if config is _DEFAULT:
        config = _config()
    try:
        return api.func("validate_email_headers")(
            sender, recipients, subject, headers, config)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} for sender={sender!r} "
                    f"recipients={recipients!r} subject={subject!r} "
                    f"headers={headers!r}: {exc}", pytrace=False)


def _shape(result):
    assert isinstance(result, dict), f"expected dict, got {type(result).__name__}"
    assert "valid" in result, f"missing key 'valid': {result!r}"
    assert "errors" in result, f"missing key 'errors': {result!r}"
    return result


def _accepted(api, **kwargs):
    res = _shape(_call(api, **kwargs))
    assert bool(res["valid"]) is True, f"expected accepted, got {res!r}"
    assert len(list(res["errors"])) == 0, f"expected no errors, got {res['errors']!r}"
    return res


def _rejected(api, **kwargs):
    res = _shape(_call(api, **kwargs))
    assert bool(res["valid"]) is False, f"expected rejected, got {res!r}"
    return res


def _checks_named(result, *names):
    try:
        text = " ".join(str(e) for e in result["errors"]).lower()
    except TypeError:
        text = str(result["errors"]).lower()
    missing = [n for n in names if n.lower() not in text]
    assert not missing, (f"failed check(s) {missing} not identified in "
                         f"errors={result['errors']!r}")


# --- correctness ---------------------------------------------------------- #

@pytest.mark.correctness
def test_C01_valid_single_recipient(api):
    _accepted(api)


@pytest.mark.correctness
def test_C02_multiple_recipients_below_limit(api):
    _accepted(api, recipients=RECIPIENTS_2)


@pytest.mark.correctness
def test_C03_recipients_exactly_at_maximum(api):
    _accepted(api, recipients=RECIPIENTS_AT_MAX)


@pytest.mark.correctness
def test_C04_recipients_above_maximum(api):
    _checks_named(_rejected(api, recipients=RECIPIENTS_OVER_MAX), "recipients")


@pytest.mark.correctness
def test_C05_invalid_sender(api):
    for bad in BAD_ADDRESSES:
        _checks_named(_rejected(api, sender=bad), "sender")


@pytest.mark.correctness
def test_C06_invalid_recipient(api):
    for bad in BAD_ADDRESSES:
        _checks_named(_rejected(api, recipients=[bad]), "recipients")


@pytest.mark.correctness
def test_C07_one_invalid_among_many(api):
    """One bad address spoils the whole set - it is not silently dropped."""
    for bad in ("no-at-sign.example.com", "@example.com", "two@@example.com"):
        _checks_named(_rejected(api, recipients=[RECIPIENT, bad, "carol@example.com"]),
                      "recipients")


@pytest.mark.correctness
def test_C08_subject_exactly_at_maximum(api):
    _accepted(api, subject=SUBJECT_AT_MAX)


@pytest.mark.correctness
def test_C09_subject_above_maximum(api):
    _checks_named(_rejected(api, subject=SUBJECT_OVER_MAX), "subject")


@pytest.mark.correctness
def test_C10_empty_subject_when_allowed(api):
    _accepted(api, subject="", config=_config(allow_empty_subject=True))
    _checks_named(_rejected(api, subject="", config=_config(allow_empty_subject=False)),
                  "subject")


@pytest.mark.correctness
def test_C11_valid_custom_header(api):
    _accepted(api, headers=HEADERS)


@pytest.mark.correctness
def test_C12_multiple_valid_custom_headers(api):
    _accepted(api, headers=HEADERS_MANY)


# --- robustness ----------------------------------------------------------- #

@pytest.mark.robustness
def test_R01_empty_sender(api):
    for sender in ("", "   ", "\t"):
        _checks_named(_rejected(api, sender=sender), "sender")


@pytest.mark.robustness
def test_R02_sender_is_none(api):
    _checks_named(_rejected(api, sender=None), "sender")


@pytest.mark.robustness
def test_R03_empty_recipient_list(api):
    """An email with nowhere to go is not valid."""
    _checks_named(_rejected(api, recipients=[]), "recipients")


@pytest.mark.robustness
def test_R04_recipient_list_is_none(api):
    _checks_named(_rejected(api, recipients=None), "recipients")


@pytest.mark.robustness
def test_R05_recipients_wrong_type(api):
    """A bare string is a common mistake and is not a list of one."""
    for bad in (RECIPIENT, 42, True, {"to": RECIPIENT}, object(), [None], [42]):
        _checks_named(_rejected(api, recipients=bad), "recipients")


@pytest.mark.robustness
def test_R06_subject_is_none(api):
    """Handled, not crashed. With empty subjects allowed, a missing subject is
    an empty one; with them forbidden, it is rejected."""
    _accepted(api, subject=None, config=_config(allow_empty_subject=True))
    _rejected(api, subject=None, config=_config(allow_empty_subject=False))


@pytest.mark.robustness
def test_R07_subject_is_non_string(api):
    for bad in (42, True, [], {}, object(), b"subject"):
        _checks_named(_rejected(api, subject=bad), "subject")


@pytest.mark.robustness
def test_R08_malformed_custom_headers(api):
    for bad in ([("X-A", "1")], "X-A: 1", 42, {"": "value"}, {"   ": "value"},
                {"X-A": None}, {None: "value"}, {"X-A": []}, {42: "value"}):
        _checks_named(_rejected(api, headers=bad), "headers")


@pytest.mark.robustness
def test_R09_headers_are_none(api):
    """No custom headers is a normal email, not a malformed one."""
    _accepted(api, headers=None)
    _accepted(api, headers={})


@pytest.mark.robustness
def test_R10_unicode_subject(api):
    """Length is counted in characters, so a non-ASCII subject is measured the
    same way an ASCII one is."""
    _accepted(api, subject="季度報告")
    _accepted(api, subject="é" * MAX_SUBJECT)
    _checks_named(_rejected(api, subject="é" * (MAX_SUBJECT + 1)), "subject")


@pytest.mark.robustness
def test_R11_unicode_in_addresses(api):
    """Non-ASCII in an address is answered rather than crashed on. Whichever
    way a solution rules on it, a CRLF payload beside it is still rejected."""
    for address in ("élise@example.com", "alice@éxample.com",
                    "张三@example.com"):
        res = _shape(_call(api, sender=address))
        assert isinstance(bool(res["valid"]), bool)
    _rejected(api, sender="élise@example.com\r\nBcc: attacker@evil.com")


@pytest.mark.robustness
def test_R12_invalid_max_recipients(api):
    for value in (-1, 0, "three", None, [], 1.5):
        res = _shape(_call(api, config=_config(max_recipients=value)))
        assert bool(res["valid"]) is False, \
            f"max_recipients={value!r} is not a usable limit: {res!r}"


# --- security (automated) ------------------------------------------------- #

@pytest.mark.security
def test_S01_crlf_in_subject(api):
    for payload in CRLF_PAYLOADS:
        _rejected(api, subject=f"Report{payload}")
        _rejected(api, subject=payload)


@pytest.mark.security
def test_S02_crlf_in_header_value(api):
    for payload in CRLF_PAYLOADS:
        _rejected(api, headers={"X-Campaign": f"spring{payload}"})


@pytest.mark.security
def test_S03_newline_in_header_name(api):
    for name in ("X-Camp\naign", "X-Camp\r\naign", "X-Campaign\r\nBcc",
                 "\nX-Campaign"):
        _rejected(api, headers={name: "spring-2026"})


@pytest.mark.security
def test_S04_crlf_in_sender(api):
    for payload in CRLF_PAYLOADS:
        _rejected(api, sender=f"alice@example.com{payload}")


@pytest.mark.security
def test_S05_crlf_in_recipient(api):
    for payload in CRLF_PAYLOADS:
        _rejected(api, recipients=[f"bob@example.com{payload}"])
        _rejected(api, recipients=[RECIPIENT, f"carol@example.com{payload}"])


@pytest.mark.security
def test_S06_multiple_injected_headers(api):
    """A payload carrying a whole block of headers is the same attack, larger.
    A solution that only looks for one newline still has to reject it."""
    payload = ("spring-2026\r\nBcc: a@evil.com\r\nX-Priority: 1\r\n"
               "Content-Type: text/html")
    _rejected(api, headers={"X-Campaign": payload})
    _rejected(api, subject=f"Report\r\nBcc: a@evil.com\r\nX-Priority: 1")


@pytest.mark.security
def test_S07_code_like_input_is_only_data(api, tmp_path, monkeypatch):
    """Text that looks like code is text. The cwd is empty and must stay
    empty: anything appearing in it means the input was executed."""
    monkeypatch.chdir(tmp_path)
    payloads = ("$(touch pwned.txt)", "`touch pwned.txt`",
                "__import__('os').system('echo x > pwned.txt')",
                "'; DROP TABLE mail; --", "{{7*7}}")
    for payload in payloads:
        for kwargs in ({"subject": payload},
                       {"headers": {"X-Campaign": payload}},
                       {"sender": f"{payload}@example.com"},
                       {"recipients": [f"{payload}@example.com"]}):
            res = _shape(_call(api, **kwargs))
            assert isinstance(bool(res["valid"]), bool)
    leftovers = sorted(p.name for p in tmp_path.iterdir())
    assert leftovers == [], f"input was executed, not validated: {leftovers}"
