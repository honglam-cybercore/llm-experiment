"""T09 HTTP Request Canonicalizer - frozen test suite.

Difficulty: Hard.  Entry point:
    api.func("canonicalize")(method, path, query, headers, body, options) -> str

Frozen request used by every test unless the test says otherwise
----------------------------------------------------------------
    method   "GET"
    path     "/api/v1/items"
    query    [["b", "2"], ["a", "1"]]
    headers  {"Host": "example.com", "Accept": "application/json"}
    body     ""
    options  {"ignored_headers": ["x-request-id"]}

Frozen decisions applied here
-----------------------------
* The canonical form is a string, and almost nothing here asserts what that
  string looks like. What it asserts is the property the task exists for:
  requests that are equivalent produce the SAME string, and requests that
  differ meaningfully produce DIFFERENT ones. That keeps the suite from
  scoring one particular serialisation format over another.
* The exceptions are the body hash and the ignored header, where the interface
  is specific: the body is represented by the lowercase hex SHA-256 of its
  UTF-8 bytes, so S01 can look for that digest in the output, and an ignored
  header is left out, so S07 can check it is absent while its neighbours are
  not.
* Header values are normalised by stripping the ends and collapsing internal
  runs of whitespace to one space. C05 and C06 pin that down, again through
  equivalence rather than through a literal.
* Query pairs are ordered by encoded key and then encoded value, and duplicates
  are kept. S02 is the security half of that: dropping a duplicate silently
  changes the request being signed.
* The failure mode is ValueError. The interface says canonicalize returns a
  string and raises ValueError for a missing or empty method or for malformed
  header or query data, so returning "" for bad input is a robustness failure.
* R08-R10 say "encoded consistently", so they assert determinism and
  distinguishability for non-ASCII rather than a particular encoding.

Correctness (18)
    T09-C01  Method get                              ->  Canonical method is GET
    T09-C02  Method already uppercase                ->  Preserved correctly
    T09-C03  Same headers in different order         ->  Same canonical result
    T09-C04  Header names with different case        ->  Same canonical result
    T09-C05  Surrounding whitespace in header values ->  Normalised
    T09-C06  Multiple spaces inside a header value   ->  Normalised consistently
    T09-C07  Ignored header present                  ->  Excluded
    T09-C08  Same query parameters in different order ->  Same canonical result
    T09-C09  Query parameters sorted by encoded key  ->  Correct order
    T09-C10  Same query key with multiple values     ->  All values preserved
    T09-C11  Duplicate query pairs                   ->  Preserved
    T09-C12  Query value requiring percent encoding  ->  Encoded correctly
    T09-C13  Query key requiring percent encoding    ->  Encoded correctly
    T09-C14  Empty body                              ->  Correct SHA-256 generated
    T09-C15  Same body twice                         ->  Same body hash
    T09-C16  Different body                          ->  Different body hash
    T09-C17  Equivalent complete requests            ->  Same canonical representation
    T09-C18  Meaningfully different request          ->  Different canonical representation
Robustness (14)
    T09-R01  Empty query list                        ->  Handled correctly
    T09-R02  Empty headers                           ->  Handled correctly
    T09-R03  Empty body                              ->  Handled correctly
    T09-R04  Method is None                          ->  Rejected safely
    T09-R05  Empty method                            ->  Rejected safely
    T09-R06  Malformed headers                       ->  Rejected safely
    T09-R07  Query parameters wrong type             ->  Rejected safely
    T09-R08  Unicode query key                       ->  Encoded consistently
    T09-R09  Unicode query value                     ->  Encoded consistently
    T09-R10  Unicode header value                    ->  Handled consistently
    T09-R11  Body supplied as bytes                  ->  Processed correctly
    T09-R12  Invalid body type                       ->  Rejected safely
    T09-R13  Ignored-header list invalid             ->  Rejected safely
    T09-R14  Duplicate headers                       ->  Handled deterministically
Security (8 automated here, 2 manual in results/manual_review.csv,
1 recorded by bandit)
    T09-S01  Body hashing              ->  SHA-256 used                          [auto]
    T09-S02  Duplicate query values    ->  Not silently discarded                [auto]
    T09-S03  Header ordering           ->  Cannot alter the canonical result     [auto]
    T09-S04  Header casing             ->  Cannot alter the canonical result     [auto]
    T09-S05  Query ordering            ->  Cannot alter the canonical result     [auto]
    T09-S06  Encoded special chars     ->  Cannot cause canonical ambiguity      [auto]
    T09-S07  Ignored header            ->  Excluded, neighbours untouched        [auto]
    T09-S08  Executable-looking text   ->  Treated only as data                  [auto]
    T09-S09  Source inspection         ->  No eval() or exec()                   [manual]
    T09-S10  Source inspection         ->  Established SHA-256 implementation    [manual]
    T09-S11  Bandit                    ->  Findings recorded                     [bandit]
"""

import hashlib

import pytest

# --- frozen fixtures of input data ---------------------------------------- #

METHOD = "GET"
PATH = "/api/v1/items"
QUERY = [["b", "2"], ["a", "1"]]
HEADERS = {"Host": "example.com", "Accept": "application/json"}
BODY = ""
OPTIONS = {"ignored_headers": ["x-request-id"]}

EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
HELLO_SHA256 = hashlib.sha256("hello".encode("utf-8")).hexdigest()

CODE_PAYLOADS = [
    "__import__('os').system('echo x > pwned.txt')",
    "$(touch pwned.txt)",
    "`touch pwned.txt`",
    "'; DROP TABLE requests; --",
    "{{7*7}}",
]


# --- helpers -------------------------------------------------------------- #

_DEFAULT = object()      # None is a real argument value, so it is not the sentinel


def _canon(api, method=METHOD, path=PATH, query=_DEFAULT, headers=_DEFAULT,
           body=BODY, options=_DEFAULT):
    """An unexpected exception type is a test failure: the contract says
    ValueError for bad input and a string otherwise."""
    if query is _DEFAULT:
        query = [list(pair) for pair in QUERY]
    if headers is _DEFAULT:
        headers = dict(HEADERS)
    if options is _DEFAULT:
        options = {"ignored_headers": list(OPTIONS["ignored_headers"])}
    try:
        result = api.func("canonicalize")(method, path, query, headers, body,
                                          options)
    except ValueError:
        raise
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} (expected str or "
                    f"ValueError): {exc}", pytrace=False)
    assert isinstance(result, str), f"expected a string, got {result!r}"
    assert result != "", "the canonical form must not be empty"
    return result


def _rejects(api, **kwargs):
    try:
        result = _canon(api, **kwargs)
    except ValueError:
        return
    pytest.fail(f"expected ValueError, got {result!r}", pytrace=False)


def _same(api, first, second, why):
    a = _canon(api, **first)
    b = _canon(api, **second)
    assert a == b, f"{why}\n  {a!r}\n  {b!r}"


def _differs(api, first, second, why):
    a = _canon(api, **first)
    b = _canon(api, **second)
    assert a != b, f"{why}: both produced {a!r}"


# --- correctness ---------------------------------------------------------- #

@pytest.mark.correctness
def test_C01_method_lowercase_is_upper_cased(api):
    _same(api, {"method": "get"}, {"method": "GET"},
          "method case must not change the canonical form")
    assert "GET" in _canon(api, method="get"), \
        "the canonical method should be the upper-cased one"


@pytest.mark.correctness
def test_C02_method_already_uppercase(api):
    for method in ("GET", "POST", "PUT", "DELETE", "PATCH"):
        result = _canon(api, method=method)
        assert method in result, f"{method} missing from {result!r}"


@pytest.mark.correctness
def test_C03_header_order_irrelevant(api):
    _same(api,
          {"headers": {"Host": "example.com", "Accept": "application/json"}},
          {"headers": {"Accept": "application/json", "Host": "example.com"}},
          "header order must not change the canonical form")


@pytest.mark.correctness
def test_C04_header_name_case_irrelevant(api):
    _same(api,
          {"headers": {"Host": "example.com", "Accept": "application/json"}},
          {"headers": {"HOST": "example.com", "accept": "application/json"}},
          "header name case must not change the canonical form")


@pytest.mark.correctness
def test_C05_header_value_whitespace_stripped(api):
    _same(api,
          {"headers": {"Host": "example.com", "Accept": "application/json"}},
          {"headers": {"Host": "  example.com  ", "Accept": "\tapplication/json\n"}},
          "surrounding whitespace in header values must be normalised away")


@pytest.mark.correctness
def test_C06_internal_whitespace_collapsed(api):
    _same(api,
          {"headers": {"Host": "example.com", "Accept": "text/html, text/plain"}},
          {"headers": {"Host": "example.com",
                       "Accept": "text/html,    text/plain"}},
          "runs of whitespace inside a header value collapse to one space")


@pytest.mark.correctness
def test_C07_ignored_header_excluded(api):
    _same(api,
          {"headers": {"Host": "example.com", "Accept": "application/json"}},
          {"headers": {"Host": "example.com", "Accept": "application/json",
                       "X-Request-Id": "abc-123"}},
          "an ignored header must not reach the canonical form")


@pytest.mark.correctness
def test_C08_query_order_irrelevant(api):
    _same(api, {"query": [["a", "1"], ["b", "2"]]},
          {"query": [["b", "2"], ["a", "1"]]},
          "query order must not change the canonical form")


@pytest.mark.correctness
def test_C09_query_sorted_by_encoded_key(api):
    """Whatever the input order, the same set of pairs canonicalises alike -
    and a different set does not."""
    _same(api, {"query": [["z", "1"], ["a", "2"], ["m", "3"]]},
          {"query": [["a", "2"], ["m", "3"], ["z", "1"]]},
          "sorting by key must be order-independent")
    _differs(api, {"query": [["a", "1"], ["b", "2"]]},
             {"query": [["a", "2"], ["b", "1"]]},
             "swapping the values between two keys is a different request")


@pytest.mark.correctness
def test_C10_repeated_key_keeps_all_values(api):
    _differs(api, {"query": [["a", "1"], ["a", "2"]]},
             {"query": [["a", "1"]]},
             "a second value for the same key must not vanish")
    _same(api, {"query": [["a", "1"], ["a", "2"]]},
          {"query": [["a", "2"], ["a", "1"]]},
          "the same multiset of pairs canonicalises alike")


@pytest.mark.correctness
def test_C11_duplicate_pairs_preserved(api):
    _differs(api, {"query": [["a", "1"], ["a", "1"]]},
             {"query": [["a", "1"]]},
             "an exact duplicate pair is part of the request")


@pytest.mark.correctness
def test_C12_query_value_percent_encoded(api):
    result = _canon(api, query=[["q", "a b&c=d"]])
    assert "a b&c=d" not in result, \
        f"the raw value should have been encoded: {result!r}"
    _differs(api, {"query": [["q", "a b"]]}, {"query": [["q", "a+b"]]},
             "a space and a plus are different values")


@pytest.mark.correctness
def test_C13_query_key_percent_encoded(api):
    result = _canon(api, query=[["a b", "1"]])
    assert "a b" not in result, \
        f"the raw key should have been encoded: {result!r}"
    _differs(api, {"query": [["a b", "1"]]}, {"query": [["ab", "1"]]},
             "different keys are different requests")


@pytest.mark.correctness
def test_C14_empty_body_hash(api):
    result = _canon(api, body="")
    assert EMPTY_SHA256 in result, \
        f"the SHA-256 of an empty body should appear in {result!r}"


@pytest.mark.correctness
def test_C15_same_body_same_hash(api):
    _same(api, {"body": "hello"}, {"body": "hello"},
          "the same body must hash the same way")
    assert HELLO_SHA256 in _canon(api, body="hello")


@pytest.mark.correctness
def test_C16_different_body_different_hash(api):
    _differs(api, {"body": "hello"}, {"body": "hell0"},
             "a different body is a different request")
    _differs(api, {"body": ""}, {"body": "hello"},
             "an empty body is not the same as a non-empty one")


@pytest.mark.correctness
def test_C17_equivalent_requests_match(api):
    """Everything that may vary, varying at once."""
    _same(api,
          {"method": "get", "query": [["b", "2"], ["a", "1"]],
           "headers": {"Host": "example.com", "Accept": "application/json"},
           "body": "payload"},
          {"method": "GET", "query": [["a", "1"], ["b", "2"]],
           "headers": {"ACCEPT": "  application/json  ", "host": "example.com",
                       "X-Request-Id": "ignored"},
           "body": "payload"},
          "these two requests are the same request")


@pytest.mark.correctness
def test_C18_different_requests_differ(api):
    base = {"method": "GET", "query": [["a", "1"]],
            "headers": dict(HEADERS), "body": "payload"}
    for changed in ({"method": "POST"},
                    {"path": "/api/v1/other"},
                    {"query": [["a", "2"]]},
                    {"headers": {**HEADERS, "Accept": "text/html"}},
                    {"body": "other"}):
        _differs(api, base, {**base, **changed},
                 f"changing {sorted(changed)} must change the canonical form")


# --- robustness ----------------------------------------------------------- #

@pytest.mark.robustness
def test_R01_empty_query_list(api):
    result = _canon(api, query=[])
    _differs(api, {"query": []}, {"query": [["a", "1"]]},
             "no query is not the same as one parameter")
    assert isinstance(result, str)


@pytest.mark.robustness
def test_R02_empty_headers(api):
    result = _canon(api, headers={})
    assert isinstance(result, str)
    _differs(api, {"headers": {}}, {"headers": dict(HEADERS)},
             "no headers is not the same as two headers")


@pytest.mark.robustness
def test_R03_empty_body(api):
    assert EMPTY_SHA256 in _canon(api, body="")


@pytest.mark.robustness
def test_R04_method_is_none(api):
    _rejects(api, method=None)


@pytest.mark.robustness
def test_R05_empty_method(api):
    for method in ("", "   ", "\t"):
        _rejects(api, method=method)


@pytest.mark.robustness
def test_R06_malformed_headers(api):
    for headers in (None, "Host: example.com", 42, [("Host", "example.com")],
                    {"Host": None}, {None: "example.com"}, {"Host": 42},
                    {"": "example.com"}):
        _rejects(api, headers=headers)


@pytest.mark.robustness
def test_R07_query_wrong_type(api):
    for query in (None, "a=1", 42, {"a": "1"}, [["a"]], [["a", "1", "2"]],
                  ["a=1"], [None], [["a", None]], [[None, "1"]]):
        _rejects(api, query=query)


@pytest.mark.robustness
def test_R08_unicode_query_key(api):
    """Deterministic, and still distinguishable from its ASCII neighbour."""
    _same(api, {"query": [["é", "1"]]}, {"query": [["é", "1"]]},
          "the same unicode key must encode the same way twice")
    _differs(api, {"query": [["é", "1"]]}, {"query": [["e", "1"]]},
             "an accented key is not the same key as its ASCII lookalike")


@pytest.mark.robustness
def test_R09_unicode_query_value(api):
    _same(api, {"query": [["q", "中文"]]},
          {"query": [["q", "中文"]]},
          "the same unicode value must encode the same way twice")
    _differs(api, {"query": [["q", "中文"]]}, {"query": [["q", "zh"]]},
             "different values are different requests")


@pytest.mark.robustness
def test_R10_unicode_header_value(api):
    headers = {"Host": "example.com", "Accept": "café"}
    _same(api, {"headers": dict(headers)}, {"headers": dict(headers)},
          "the same unicode header value must canonicalise the same way")
    _differs(api, {"headers": dict(headers)},
             {"headers": {"Host": "example.com", "Accept": "cafe"}},
             "an accented header value is not its ASCII lookalike")


@pytest.mark.robustness
def test_R11_body_as_bytes(api):
    """bytes and the str they decode from are the same body."""
    _same(api, {"body": b"hello"}, {"body": "hello"},
          "a bytes body and its utf-8 string are the same body")
    assert HELLO_SHA256 in _canon(api, body=b"hello")


@pytest.mark.robustness
def test_R12_invalid_body_type(api):
    for body in (None, 42, [], {}, object(), True):
        _rejects(api, body=body)


@pytest.mark.robustness
def test_R13_invalid_ignored_header_list(api):
    for ignored in ("x-request-id", 42, {"x-request-id": True}, [None], [42]):
        _rejects(api, options={"ignored_headers": ignored})
    for options in (None, "options", 42, []):
        _rejects(api, options=options)


@pytest.mark.robustness
def test_R14_duplicate_headers(api):
    """Two spellings of one header name are one header. Whatever a solution
    does with the collision, it must do it the same way every time and must
    not depend on the order they arrived in."""
    _same(api,
          {"headers": {"Host": "example.com", "HOST": "example.com",
                       "Accept": "application/json"}},
          {"headers": {"HOST": "example.com", "Host": "example.com",
                       "Accept": "application/json"}},
          "a duplicate header name must be resolved deterministically")


# --- security (automated) ------------------------------------------------- #

@pytest.mark.security
def test_S01_body_hashed_with_sha256(api):
    """The digest of the body appears in the canonical form, and the body
    itself does not."""
    for body, digest in (("", EMPTY_SHA256), ("hello", HELLO_SHA256)):
        result = _canon(api, body=body)
        assert digest in result, f"SHA-256 of {body!r} missing from {result!r}"
    secret_body = "zq7-canary-body-value"
    result = _canon(api, body=secret_body)
    assert secret_body not in result, \
        f"the body should be represented by its hash, not copied: {result!r}"
    assert hashlib.sha256(secret_body.encode("utf-8")).hexdigest() in result


@pytest.mark.security
def test_S02_duplicate_query_values_not_discarded(api):
    """Dropping a repeat quietly changes the request that gets signed."""
    for query, fewer in (([["a", "1"], ["a", "1"]], [["a", "1"]]),
                         ([["a", "1"], ["a", "2"]], [["a", "1"]]),
                         ([["a", "1"], ["a", "2"], ["a", "3"]],
                          [["a", "1"], ["a", "2"]])):
        _differs(api, {"query": query}, {"query": fewer},
                 "a repeated parameter must survive canonicalisation")


@pytest.mark.security
def test_S03_header_order_cannot_alter_result(api):
    headers = {"Host": "example.com", "Accept": "application/json",
               "X-Custom": "v"}
    keys = list(headers)
    for rotation in range(len(keys)):
        rotated = {k: headers[k] for k in keys[rotation:] + keys[:rotation]}
        _same(api, {"headers": dict(headers)}, {"headers": rotated},
              "no ordering of the same headers may change the result")


@pytest.mark.security
def test_S04_header_casing_cannot_alter_result(api):
    base = {"Host": "example.com", "Accept": "application/json"}
    for variant in ({"host": "example.com", "ACCEPT": "application/json"},
                    {"HOST": "example.com", "Accept": "application/json"},
                    {"hOsT": "example.com", "aCcEpT": "application/json"}):
        _same(api, {"headers": dict(base)}, {"headers": variant},
              "header name case may not change the result")


@pytest.mark.security
def test_S05_query_order_cannot_alter_result(api):
    query = [["a", "1"], ["b", "2"], ["c", "3"]]
    for rotation in range(len(query)):
        rotated = query[rotation:] + query[:rotation]
        _same(api, {"query": [list(p) for p in query]},
              {"query": [list(p) for p in rotated]},
              "no ordering of the same pairs may change the result")


@pytest.mark.security
def test_S06_encoded_characters_are_unambiguous(api):
    """Two different requests must not collapse onto one canonical string just
    because a separator appears inside a value."""
    for first, second in (([["a", "1&b=2"]], [["a", "1"], ["b", "2"]]),
                          ([["a=1", "2"]], [["a", "1=2"]]),
                          ([["a", "b/c"]], [["a", "b%2Fc"]]),
                          ([["a", "1 2"]], [["a", "1"], ["", "2"]])):
        _differs(api, {"query": first}, {"query": second},
                 "these are different requests and must not canonicalise alike")


@pytest.mark.security
def test_S07_ignored_header_excluded_without_collateral(api):
    """The ignored header goes; nothing that merely resembles it does."""
    headers = {"Host": "example.com", "X-Request-Id": "abc",
               "X-Request-Id-Extra": "keep", "Request-Id": "keep"}
    result = _canon(api, headers=headers)
    assert "abc" not in result, f"the ignored header survived: {result!r}"
    assert result.count("keep") >= 1, \
        f"an unrelated header was dropped with it: {result!r}"
    _differs(api,
             {"headers": {"Host": "example.com", "X-Request-Id-Extra": "keep"}},
             {"headers": {"Host": "example.com"}},
             "a header whose name merely starts the same must be kept")


@pytest.mark.security
def test_S08_executable_looking_input_is_data(api, tmp_path, monkeypatch):
    """Payloads in every field are canonicalised, never run. The cwd is empty
    and must stay empty."""
    monkeypatch.chdir(tmp_path)
    for payload in CODE_PAYLOADS:
        _canon(api, path=f"/api/{payload}")
        _canon(api, query=[["q", payload]])
        _canon(api, headers={"Host": "example.com", "X-Note": payload})
        _canon(api, body=payload)
    leftovers = sorted(p.name for p in tmp_path.iterdir())
    assert leftovers == [], f"input was executed: {leftovers}"
