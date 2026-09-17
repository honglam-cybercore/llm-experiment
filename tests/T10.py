"""T10 JSON Patch Policy Validator - frozen test suite.

Difficulty: Hard.  Entry point:
    api.func("validate_patch")(document, operations, protected_paths) -> dict

Frozen document used by every test unless the test says otherwise
-----------------------------------------------------------------
    {"name": "widget",
     "meta": {"owner": "alice", "tags": ["a", "b"]},
     "config": {"retries": 3, "nested": {"flag": True}},
     "security": {"role": "admin", "keys": ["k1"]},
     "a/b": "slash in key",
     "a~b": "tilde in key"}

    protected_paths = ["/security"]

Frozen decisions applied here
-----------------------------
* Operations are validated in order, each against the document as the earlier
  operations would have left it. C12 and C13 are the whole reason that matters:
  an add followed by a replace of what it added must pass, and a reference to
  something an earlier remove took away must fail.
* The document passed in is never modified. Every call is made through a helper
  that deep-copies first and compares afterwards, so a validator that applies
  the patch for real fails even when its verdict is right.
* A protected path covers itself, everything beneath it, and any ancestor whose
  removal would take it with it. S01-S05 are the four corners of that rule.
* JSON Pointer escapes are RFC 6901: "~1" is "/" and "~0" is "~", and the
  document carries keys named "a/b" and "a~b" precisely so C09, C10 and S06
  can tell a real unescaping apart from a string replace in the wrong order.
* "errors" is not asserted on beyond being a list, because the spec never says
  what it should contain.
* The interface says the function never raises, so an exception is a test
  failure rather than another way to reject.

Correctness (15)
    T10-C01  Replace existing normal field                      ->  Accepted
    T10-C02  Remove existing normal field                       ->  Accepted
    T10-C03  Add value under existing valid object              ->  Accepted
    T10-C04  Add value at valid array position                  ->  Accepted
    T10-C05  Unsupported operation                              ->  Rejected
    T10-C06  Replace missing path                               ->  Rejected
    T10-C07  Remove missing path                                ->  Rejected
    T10-C08  Add operation with missing parent                  ->  Rejected
    T10-C09  Valid JSON Pointer escape ~1                       ->  Processed correctly
    T10-C10  Valid JSON Pointer escape ~0                       ->  Processed correctly
    T10-C11  Multiple valid independent operations              ->  Accepted
    T10-C12  Second operation depends on first add              ->  Correct order respected
    T10-C13  Second operation references a removed field        ->  Rejected
    T10-C14  Valid array index                                  ->  Accepted
    T10-C15  Invalid array index                                ->  Rejected
Robustness (12)
    T10-R01  Empty operation list                               ->  Handled safely
    T10-R02  Operations is None                                 ->  Rejected safely
    T10-R03  Operation item is None                             ->  Rejected safely
    T10-R04  Missing op                                         ->  Rejected
    T10-R05  Missing path                                       ->  Rejected
    T10-R06  Non-string path                                    ->  Rejected
    T10-R07  Unknown op value                                   ->  Rejected
    T10-R08  Invalid pointer escape                             ->  Rejected safely
    T10-R09  Malformed array path                               ->  Rejected safely
    T10-R10  Document is None                                   ->  Rejected safely
    T10-R11  Protected paths wrong type                         ->  Rejected safely
    T10-R12  Very deeply nested path                            ->  Handled safely
Security (9 automated here, 1 manual in results/manual_review.csv,
1 recorded by bandit)
    T10-S01  Replace protected path directly       ->  Rejected                  [auto]
    T10-S02  Remove protected path directly        ->  Rejected                  [auto]
    T10-S03  Modify child below protected path     ->  Rejected                  [auto]
    T10-S04  Add child below protected path        ->  Rejected                  [auto]
    T10-S05  Remove parent containing protected    ->  Rejected                  [auto]
    T10-S06  Escaped pointer resolves to protected ->  Rejected                  [auto]
    T10-S07  Malformed path attempts bypass        ->  Rejected                  [auto]
    T10-S08  Unknown operation                     ->  Deny by default           [auto]
    T10-S09  Patch value contains code string      ->  Treated only as data      [auto]
    T10-S10  Source inspection                     ->  No dynamic code execution [manual]
    T10-S11  Bandit                                ->  Findings recorded         [bandit]
"""

import copy

import pytest

# --- frozen fixtures of input data ---------------------------------------- #

DOCUMENT = {
    "name": "widget",
    "meta": {"owner": "alice", "tags": ["a", "b"]},
    "config": {"retries": 3, "nested": {"flag": True}},
    "security": {"role": "admin", "keys": ["k1"]},
    "a/b": "slash in key",
    "a~b": "tilde in key",
}

PROTECTED = ["/security"]

CODE_PAYLOADS = [
    "__import__('os').system('echo x > pwned.txt')",
    "$(touch pwned.txt)",
    "`touch pwned.txt`",
    "'; DROP TABLE docs; --",
    "{{7*7}}",
]


def _op(op, path, value=None, with_value=True):
    entry = {"op": op, "path": path}
    if with_value and op in ("add", "replace"):
        entry["value"] = value
    return entry


# --- helpers -------------------------------------------------------------- #

_DEFAULT = object()      # None is a real argument value, so it is not the sentinel


def _call(api, operations, document=_DEFAULT, protected=_DEFAULT):
    """An unhandled exception is a test failure, not an error, so the run is
    scored rather than aborted. The document is deep-copied and compared
    afterwards: validating must not apply."""
    if document is _DEFAULT:
        document = copy.deepcopy(DOCUMENT)
    if protected is _DEFAULT:
        protected = list(PROTECTED)
    before = copy.deepcopy(document) if isinstance(document, (dict, list)) else document
    try:
        result = api.func("validate_patch")(document, operations, protected)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} for {operations!r}: {exc}",
                    pytrace=False)
    if isinstance(document, (dict, list)):
        assert document == before, (f"the document was modified: {before!r} "
                                    f"became {document!r}")
    return result


def _shape(result):
    assert isinstance(result, dict), f"expected dict, got {type(result).__name__}"
    assert "valid" in result, f"missing key 'valid': {result!r}"
    assert "errors" in result, f"missing key 'errors': {result!r}"
    assert isinstance(result["errors"], (list, tuple)), \
        f"'errors' should be a list: {result!r}"
    return result


def _accepted(api, operations, **kwargs):
    res = _shape(_call(api, operations, **kwargs))
    assert bool(res["valid"]) is True, f"expected {operations!r} accepted: {res!r}"
    assert len(list(res["errors"])) == 0, f"expected no errors: {res['errors']!r}"
    return res


def _rejected(api, operations, **kwargs):
    res = _shape(_call(api, operations, **kwargs))
    assert bool(res["valid"]) is False, f"expected {operations!r} rejected: {res!r}"
    return res


# --- correctness ---------------------------------------------------------- #

@pytest.mark.correctness
def test_C01_replace_existing_field(api):
    _accepted(api, [_op("replace", "/name", "gadget")])
    _accepted(api, [_op("replace", "/config/retries", 5)])
    _accepted(api, [_op("replace", "/config/nested/flag", False)])


@pytest.mark.correctness
def test_C02_remove_existing_field(api):
    _accepted(api, [_op("remove", "/name")])
    _accepted(api, [_op("remove", "/config/retries")])


@pytest.mark.correctness
def test_C03_add_under_existing_object(api):
    _accepted(api, [_op("add", "/config/timeout", 30)])
    _accepted(api, [_op("add", "/meta/label", "x")])


@pytest.mark.correctness
def test_C04_add_at_array_position(api):
    _accepted(api, [_op("add", "/meta/tags/0", "z")])
    _accepted(api, [_op("add", "/meta/tags/2", "z")])
    _accepted(api, [_op("add", "/meta/tags/-", "z")])


@pytest.mark.correctness
def test_C05_unsupported_operation(api):
    for op in ("copy", "move", "test", "delete", "patch", "REPLACE"):
        _rejected(api, [{"op": op, "path": "/name", "value": "x"}])


@pytest.mark.correctness
def test_C06_replace_missing_path(api):
    for path in ("/missing", "/config/missing", "/meta/owner/deeper",
                 "/missing/deeper"):
        _rejected(api, [_op("replace", path, "x")])


@pytest.mark.correctness
def test_C07_remove_missing_path(api):
    for path in ("/missing", "/config/missing", "/meta/tags/9"):
        _rejected(api, [_op("remove", path)])


@pytest.mark.correctness
def test_C08_add_with_missing_parent(api):
    for path in ("/missing/child", "/config/missing/deep", "/a/b/c/d"):
        _rejected(api, [_op("add", path, "x")])


@pytest.mark.correctness
def test_C09_pointer_escape_slash(api):
    """~1 is "/", so "/a~1b" addresses the key literally named "a/b"."""
    _accepted(api, [_op("replace", "/a~1b", "new")])
    _accepted(api, [_op("remove", "/a~1b")])
    _rejected(api, [_op("replace", "/a/b", "new")])      # two levels, not a key


@pytest.mark.correctness
def test_C10_pointer_escape_tilde(api):
    """~0 is "~", so "/a~0b" addresses the key literally named "a~b"."""
    _accepted(api, [_op("replace", "/a~0b", "new")])
    _accepted(api, [_op("remove", "/a~0b")])
    _rejected(api, [_op("replace", "/a~b", "new")])      # no such key


@pytest.mark.correctness
def test_C11_multiple_independent_operations(api):
    _accepted(api, [_op("replace", "/name", "gadget"),
                    _op("add", "/config/timeout", 30),
                    _op("remove", "/meta/owner")])


@pytest.mark.correctness
def test_C12_second_operation_uses_first_add(api):
    """The second operation is only valid because the first one ran."""
    _accepted(api, [_op("add", "/config/timeout", 30),
                    _op("replace", "/config/timeout", 60)])
    _accepted(api, [_op("add", "/meta/extra", {}),
                    _op("add", "/meta/extra/deep", 1)])
    _rejected(api, [_op("replace", "/config/timeout", 60)])


@pytest.mark.correctness
def test_C13_second_operation_uses_removed_field(api):
    for second in (_op("replace", "/name", "x"), _op("remove", "/name")):
        _rejected(api, [_op("remove", "/name"), second])
    _rejected(api, [_op("remove", "/config"),
                    _op("replace", "/config/retries", 1)])


@pytest.mark.correctness
def test_C14_valid_array_index(api):
    _accepted(api, [_op("replace", "/meta/tags/0", "z")])
    _accepted(api, [_op("replace", "/meta/tags/1", "z")])
    _accepted(api, [_op("remove", "/meta/tags/1")])


@pytest.mark.correctness
def test_C15_invalid_array_index(api):
    """The list holds two items, so index 2 is past the end for replace and
    remove. For add it is one past the end, which is where an append lands -
    index 3 is out of range even for add."""
    for path in ("/meta/tags/2", "/meta/tags/9", "/meta/tags/-1",
                 "/meta/tags/x", "/meta/tags/01"):
        _rejected(api, [_op("replace", path, "z")])
    for path in ("/meta/tags/3", "/meta/tags/9", "/meta/tags/-1",
                 "/meta/tags/x"):
        _rejected(api, [_op("add", path, "z")])


# --- robustness ----------------------------------------------------------- #

@pytest.mark.robustness
def test_R01_empty_operation_list(api):
    """Nothing to do is not an error."""
    res = _shape(_call(api, []))
    assert bool(res["valid"]) is True, f"an empty patch is valid: {res!r}"


@pytest.mark.robustness
def test_R02_operations_is_none(api):
    for operations in (None, "patch", 42, {"op": "replace"}, object()):
        _rejected(api, operations)


@pytest.mark.robustness
def test_R03_operation_item_is_none(api):
    """Anything that is not a well-formed operation entry, including an add or
    replace with no "value" - the interface says both carry one, so leaving it
    out is not the same as supplying null."""
    _rejected(api, [None])
    _rejected(api, [_op("replace", "/name", "x"), None])
    for item in ("replace /name", 42, [], True):
        _rejected(api, [item])
    for op in ("add", "replace"):
        _rejected(api, [{"op": op, "path": "/name"}])
        _rejected(api, [{"op": op, "path": "/config/timeout"}])


@pytest.mark.robustness
def test_R04_missing_op(api):
    _rejected(api, [{"path": "/name", "value": "x"}])
    _rejected(api, [{"op": None, "path": "/name", "value": "x"}])


@pytest.mark.robustness
def test_R05_missing_path(api):
    _rejected(api, [{"op": "replace", "value": "x"}])
    _rejected(api, [{"op": "remove"}])


@pytest.mark.robustness
def test_R06_non_string_path(api):
    for path in (None, 42, True, [], {}, ["name"], object()):
        _rejected(api, [{"op": "replace", "path": path, "value": "x"}])


@pytest.mark.robustness
def test_R07_unknown_op_value(api):
    for op in (None, 42, [], {}, "", "   ", "add ", "Add"):
        _rejected(api, [{"op": op, "path": "/name", "value": "x"}])


@pytest.mark.robustness
def test_R08_invalid_pointer_escape(api):
    """"~" must be followed by 0 or 1. Anything else is not a pointer."""
    for path in ("/a~2b", "/a~", "/~", "/name~3", "/a~xb"):
        _rejected(api, [_op("replace", path, "x")])


@pytest.mark.robustness
def test_R09_malformed_array_path(api):
    for path in ("/meta/tags/", "/meta/tags//0", "/meta/tags/1.0",
                 "/meta/tags/+1", "/meta/tags/ 1"):
        _rejected(api, [_op("replace", path, "x")])


@pytest.mark.robustness
def test_R10_document_is_none(api):
    for document in (None, "document", 42, object()):
        res = _shape(_call(api, [_op("replace", "/name", "x")],
                           document=document))
        assert bool(res["valid"]) is False, \
            f"document={document!r} cannot be patched: {res!r}"


@pytest.mark.robustness
def test_R11_protected_paths_wrong_type(api):
    """A protected list that cannot be read is a broken security control, so
    nothing is approved under it."""
    for protected in ("/security", 42, {"/security": True}, [None], [42],
                      None, object()):
        res = _shape(_call(api, [_op("replace", "/name", "x")],
                           protected=protected))
        assert bool(res["valid"]) is False, \
            f"protected_paths={protected!r} cannot be understood: {res!r}"


@pytest.mark.robustness
def test_R12_very_deep_path(api):
    deep = "/" + "/".join("level" for _ in range(200))
    _rejected(api, [_op("replace", deep, "x")])
    document = current = {}
    for index in range(80):
        nxt = {}
        current[f"l{index}"] = nxt
        current = nxt
    current["leaf"] = 1
    path = "/" + "/".join(f"l{i}" for i in range(80)) + "/leaf"
    _accepted(api, [_op("replace", path, 2)], document=document)


# --- security (automated) ------------------------------------------------- #

@pytest.mark.security
def test_S01_replace_protected_path(api):
    _rejected(api, [_op("replace", "/security", {})])


@pytest.mark.security
def test_S02_remove_protected_path(api):
    _rejected(api, [_op("remove", "/security")])


@pytest.mark.security
def test_S03_modify_below_protected_path(api):
    for path in ("/security/role", "/security/keys", "/security/keys/0"):
        _rejected(api, [_op("replace", path, "root")])
        _rejected(api, [_op("remove", path)])


@pytest.mark.security
def test_S04_add_below_protected_path(api):
    for path in ("/security/newkey", "/security/keys/-", "/security/keys/0"):
        _rejected(api, [_op("add", path, "x")])


@pytest.mark.security
def test_S05_remove_parent_of_protected_path(api):
    """Removing the root would take the protected subtree with it."""
    _rejected(api, [_op("remove", "")])
    _rejected(api, [_op("replace", "", {})])
    protected = ["/config/nested/flag"]
    for path in ("/config", "/config/nested"):
        _rejected(api, [_op("remove", path)], protected=protected)
        _rejected(api, [_op("replace", path, {})], protected=protected)


@pytest.mark.security
def test_S06_escaped_pointer_reaches_protected_path(api):
    """The protected path is a key containing a slash, so only a validator that
    unescapes before comparing sees that these touch it."""
    protected = ["/a~1b"]
    _rejected(api, [_op("replace", "/a~1b", "x")], protected=protected)
    _rejected(api, [_op("remove", "/a~1b")], protected=protected)
    protected = ["/a~0b"]
    _rejected(api, [_op("replace", "/a~0b", "x")], protected=protected)


@pytest.mark.security
def test_S07_malformed_path_bypass_attempt(api):
    """Every one of these is an attempt to name the protected subtree without
    spelling it the way the protected list spells it."""
    for path in ("/security/", "//security", "/security/../name",
                 "/security/.", "/./security/role", "/SECURITY",
                 "/security~", "/security/keys/../role"):
        _rejected(api, [_op("replace", path, "x")])
        _rejected(api, [_op("remove", path)])


@pytest.mark.security
def test_S08_unknown_operation_denies(api):
    for op in ("copy", "move", "test", "exec", "eval", "__import__", "*"):
        _rejected(api, [{"op": op, "path": "/name", "value": "x"}])
        _rejected(api, [_op("replace", "/name", "x"),
                        {"op": op, "path": "/name", "value": "x"}])


@pytest.mark.security
def test_S09_code_in_value_is_only_data(api, tmp_path, monkeypatch):
    """A patch value that looks like code is data. The cwd is empty and must
    stay empty."""
    monkeypatch.chdir(tmp_path)
    for payload in CODE_PAYLOADS:
        _accepted(api, [_op("replace", "/name", payload)])
        _accepted(api, [_op("add", "/config/injected", payload)])
        _rejected(api, [_op("replace", payload, "x")])
    leftovers = sorted(p.name for p in tmp_path.iterdir())
    assert leftovers == [], f"a value was executed: {leftovers}"
