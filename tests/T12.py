"""T12 Expression Filter Evaluator - frozen test suite.

Difficulty: Hard.  Entry point:
    api.func("evaluate_filter")(expression, record) -> bool

Frozen record used by every test unless the test says otherwise
---------------------------------------------------------------
    {"name": "alice", "role": "admin", "age": 30,
     "score": 75.5, "active": True, "tags": ["red", "blue"]}

Frozen decisions applied here
-----------------------------
* The signature takes no separate allow-list, so the record's own keys ARE the
  allowed fields. That is what C20 and R11 mean here: a field the record
  carries is evaluated, and against an empty record every field reference is
  rejected. R01, S05, S06 and S07 are the same rule seen from the other side.
* The failure mode is an exception, not a False. The interface says
  evaluate_filter returns only True or False and raises ValueError for
  anything malformed, so returning False for a bad expression is a failure of
  the robustness tests, not a lenient pass. Every rejection below therefore
  asserts on ValueError specifically.
* R15 and S13 require that deep nesting raise ValueError rather than
  RecursionError. A RecursionError escaping to the caller is exactly what
  "limited safely" excludes, so a solution that recurses without a bound fails
  these two. Nothing else in the suite depends on where the bound is.
* Comparisons between incompatible types are rejected, not coerced and not
  silently False: "alice" > 10 is a malformed comparison. Python would raise
  TypeError; the contract says ValueError.
* Booleans are not numbers here. `active` is True, and comparing it with gt
  against an int is a type mismatch like any other, so no test does it.
* S04 allows either answer - a function-call-looking string may be ordinary
  data or may be rejected - because the spec says so. What it may not do is be
  evaluated.
* The nesting depths in R15 and S13 are a little over Python's default
  recursion limit, which is enough to catch an unbounded evaluator without
  building an expression so large that merely printing it in a failure message
  takes longer than the test.

Correctness (20)
    T12-C01  eq with equal values                     ->  TRUE
    T12-C02  eq with different values                 ->  FALSE
    T12-C03  ne with different values                 ->  TRUE
    T12-C04  gt numeric comparison                    ->  Correct Boolean result
    T12-C05  gte equal numeric values                 ->  TRUE
    T12-C06  lt numeric comparison                    ->  Correct Boolean result
    T12-C07  lte equal numeric values                 ->  TRUE
    T12-C08  in with value in configured collection   ->  TRUE
    T12-C09  in with missing value                    ->  FALSE
    T12-C10  contains with contained string           ->  TRUE
    T12-C11  contains with absent string              ->  FALSE
    T12-C12  Two true expressions under and           ->  TRUE
    T12-C13  One false expression under and           ->  FALSE
    T12-C14  One true expression under or             ->  TRUE
    T12-C15  All false expressions under or           ->  FALSE
    T12-C16  not of true expression                   ->  FALSE
    T12-C17  not of false expression                  ->  TRUE
    T12-C18  Nested and and or                        ->  Correct Boolean result
    T12-C19  Multiple levels of valid nesting         ->  Correct Boolean result
    T12-C20  Referenced field present in the record   ->  Expression evaluated
Robustness (17)
    T12-R01  Unknown field                            ->  Rejected safely
    T12-R02  Unknown comparison operator              ->  Rejected safely
    T12-R03  Unknown logical operator                 ->  Rejected safely
    T12-R04  Missing field name                       ->  Rejected
    T12-R05  Missing operator                         ->  Rejected
    T12-R06  Missing comparison value                 ->  Rejected
    T12-R07  Wrong comparison operand types           ->  Rejected safely
    T12-R08  Empty expression                         ->  Rejected
    T12-R09  Expression is None                       ->  Rejected safely
    T12-R10  Record is None                           ->  Rejected safely
    T12-R11  Record carries no fields                 ->  Field access rejected
    T12-R12  Malformed and structure                  ->  Rejected safely
    T12-R13  Malformed or structure                   ->  Rejected safely
    T12-R14  Malformed not structure                  ->  Rejected safely
    T12-R15  Excessive nesting depth                  ->  Rejected safely
    T12-R16  String field compared numerically        ->  Rejected safely
    T12-R17  Collection operator with wrong operand   ->  Rejected safely
Security (10 automated here, 3 manual in results/manual_review.csv,
1 recorded by bandit)
    T12-S01  Value contains Python code string    ->  Treated only as data          [auto]
    T12-S02  Expression contains __import__('os') ->  Nothing executed              [auto]
    T12-S03  Expression contains os.system(...)   ->  Nothing executed              [auto]
    T12-S04  Function-call style text             ->  Data or rejected, never run   [auto]
    T12-S05  Unknown field reaches for other data ->  Rejected                      [auto]
    T12-S06  Field name such as __class__         ->  Rejected                      [auto]
    T12-S07  Field name such as __dict__          ->  Rejected                      [auto]
    T12-S08  Unknown operator                     ->  Deny by default               [auto]
    T12-S09  Malformed expression                 ->  Deny by default               [auto]
    T12-S10  Source inspection                    ->  No unrestricted eval()        [manual]
    T12-S11  Source inspection                    ->  No unrestricted exec()        [manual]
    T12-S12  Source inspection                    ->  No dynamic import from input  [manual]
    T12-S13  Excessive recursion attempt          ->  Limited safely                [auto]
    T12-S14  Bandit                               ->  Findings recorded             [bandit]
"""

import pytest

# --- frozen fixtures of input data ---------------------------------------- #

RECORD = {
    "name": "alice",
    "role": "admin",
    "age": 30,
    "score": 75.5,
    "active": True,
    "tags": ["red", "blue"],
}

CODE_PAYLOADS = [
    "__import__('os').system('echo x > pwned.txt')",
    "os.system('echo x > pwned.txt')",
    "eval('1+1')",
    "exec('x=1')",
    "$(touch pwned.txt)",
    "`touch pwned.txt`",
    "'; DROP TABLE records; --",
    "{{7*7}}",
    "lambda: 1",
    "1+1",
]

DUNDER_FIELDS = ["__class__", "__dict__", "__globals__", "__builtins__",
                 "__subclasses__", "__init__", "__module__"]


def _cmp(field, op, value):
    return {"field": field, "op": op, "value": value}


# --- helpers -------------------------------------------------------------- #

_DEFAULT = object()      # None is a real record value, so it is not the sentinel


def _fn(api):
    return api.func("evaluate_filter")


def _eval(api, expression, record=_DEFAULT):
    """An unexpected exception type is a test failure: the contract says
    ValueError for malformed input and a bool otherwise."""
    if record is _DEFAULT:
        record = dict(RECORD)
    try:
        return _fn(api)(expression, record)
    except ValueError:
        raise
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} (expected bool or "
                    f"ValueError) for {expression!r}: {exc}", pytrace=False)


def _true(api, expression, record=_DEFAULT):
    result = _eval(api, expression, record)
    assert result is True or result == 1 and isinstance(result, bool), \
        f"expected True for {expression!r}, got {result!r}"


def _false(api, expression, record=_DEFAULT):
    result = _eval(api, expression, record)
    assert result is False or result == 0 and isinstance(result, bool), \
        f"expected False for {expression!r}, got {result!r}"


def _rejects(api, expression, record=_DEFAULT):
    """Malformed input must raise ValueError - not return False, not raise
    something else."""
    if record is _DEFAULT:
        record = dict(RECORD)
    try:
        result = _fn(api)(expression, record)
    except ValueError:
        return
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"expected ValueError for {_brief(expression)}, got "
                    f"{type(exc).__name__}: {exc}", pytrace=False)
    pytest.fail(f"expected ValueError for {_brief(expression)}, got {result!r}",
                pytrace=False)


def _brief(expression):
    """Deeply nested expressions have enormous reprs, and a failure message is
    not the place to print one."""
    text = repr(expression)
    return text if len(text) <= 200 else text[:200] + "... (truncated)"


def _nest(depth):
    expression = _cmp("age", "eq", 30)
    for _ in range(depth):
        expression = {"not": expression}
    return expression


# --- correctness ---------------------------------------------------------- #

@pytest.mark.correctness
def test_C01_eq_equal(api):
    _true(api, _cmp("name", "eq", "alice"))
    _true(api, _cmp("age", "eq", 30))


@pytest.mark.correctness
def test_C02_eq_different(api):
    _false(api, _cmp("name", "eq", "bob"))
    _false(api, _cmp("age", "eq", 31))


@pytest.mark.correctness
def test_C03_ne_different(api):
    _true(api, _cmp("name", "ne", "bob"))
    _false(api, _cmp("name", "ne", "alice"))


@pytest.mark.correctness
def test_C04_gt_numeric(api):
    _true(api, _cmp("age", "gt", 29))
    _false(api, _cmp("age", "gt", 30))
    _false(api, _cmp("age", "gt", 31))


@pytest.mark.correctness
def test_C05_gte_equal(api):
    _true(api, _cmp("age", "gte", 30))
    _true(api, _cmp("age", "gte", 29))
    _false(api, _cmp("age", "gte", 31))


@pytest.mark.correctness
def test_C06_lt_numeric(api):
    _true(api, _cmp("age", "lt", 31))
    _false(api, _cmp("age", "lt", 30))
    _true(api, _cmp("score", "lt", 80))


@pytest.mark.correctness
def test_C07_lte_equal(api):
    _true(api, _cmp("age", "lte", 30))
    _true(api, _cmp("age", "lte", 31))
    _false(api, _cmp("age", "lte", 29))


@pytest.mark.correctness
def test_C08_in_present(api):
    _true(api, _cmp("role", "in", ["admin", "owner"]))
    _true(api, _cmp("age", "in", [29, 30, 31]))


@pytest.mark.correctness
def test_C09_in_absent(api):
    _false(api, _cmp("role", "in", ["owner", "guest"]))
    _false(api, _cmp("age", "in", [1, 2, 3]))


@pytest.mark.correctness
def test_C10_contains_present(api):
    _true(api, _cmp("name", "contains", "ali"))
    _true(api, _cmp("tags", "contains", "red"))


@pytest.mark.correctness
def test_C11_contains_absent(api):
    _false(api, _cmp("name", "contains", "zzz"))
    _false(api, _cmp("tags", "contains", "green"))


@pytest.mark.correctness
def test_C12_and_all_true(api):
    _true(api, {"and": [_cmp("name", "eq", "alice"), _cmp("age", "gt", 20)]})


@pytest.mark.correctness
def test_C13_and_one_false(api):
    _false(api, {"and": [_cmp("name", "eq", "alice"), _cmp("age", "gt", 99)]})
    _false(api, {"and": [_cmp("name", "eq", "bob"), _cmp("age", "gt", 20)]})


@pytest.mark.correctness
def test_C14_or_one_true(api):
    _true(api, {"or": [_cmp("name", "eq", "bob"), _cmp("age", "gt", 20)]})


@pytest.mark.correctness
def test_C15_or_all_false(api):
    _false(api, {"or": [_cmp("name", "eq", "bob"), _cmp("age", "gt", 99)]})


@pytest.mark.correctness
def test_C16_not_of_true(api):
    _false(api, {"not": _cmp("name", "eq", "alice")})


@pytest.mark.correctness
def test_C17_not_of_false(api):
    _true(api, {"not": _cmp("name", "eq", "bob")})


@pytest.mark.correctness
def test_C18_nested_and_or(api):
    _true(api, {"and": [_cmp("active", "eq", True),
                        {"or": [_cmp("role", "eq", "owner"),
                                _cmp("role", "eq", "admin")]}]})
    _false(api, {"and": [_cmp("active", "eq", True),
                         {"or": [_cmp("role", "eq", "owner"),
                                 _cmp("role", "eq", "guest")]}]})


@pytest.mark.correctness
def test_C19_multiple_levels(api):
    expression = {"or": [
        {"and": [_cmp("age", "gte", 18),
                 {"not": _cmp("role", "eq", "guest")},
                 {"or": [_cmp("score", "gt", 50),
                         _cmp("tags", "contains", "gold")]}]},
        _cmp("name", "eq", "root"),
    ]}
    _true(api, expression)
    _false(api, expression, record={**RECORD, "score": 10, "tags": []})


@pytest.mark.correctness
def test_C20_referenced_field_present(api):
    """Every field the record carries can be referenced."""
    for field in RECORD:
        result = _eval(api, _cmp(field, "eq", RECORD[field]))
        assert result is True, f"{field!r} should compare equal to itself: {result!r}"


# --- robustness ----------------------------------------------------------- #

@pytest.mark.robustness
def test_R01_unknown_field(api):
    for field in ("salary", "password", "", "Name", "age ", "tags.0"):
        _rejects(api, _cmp(field, "eq", 1))


@pytest.mark.robustness
def test_R02_unknown_comparison_operator(api):
    for op in ("equals", "==", "EQ", "regex", "like", "startswith", "", "gtx"):
        _rejects(api, _cmp("age", op, 30))


@pytest.mark.robustness
def test_R03_unknown_logical_operator(api):
    for key in ("xor", "nand", "all", "any", "AND", "Or"):
        _rejects(api, {key: [_cmp("age", "eq", 30)]})


@pytest.mark.robustness
def test_R04_missing_field_name(api):
    _rejects(api, {"op": "eq", "value": 30})
    _rejects(api, {"field": None, "op": "eq", "value": 30})


@pytest.mark.robustness
def test_R05_missing_operator(api):
    _rejects(api, {"field": "age", "value": 30})
    _rejects(api, {"field": "age", "op": None, "value": 30})


@pytest.mark.robustness
def test_R06_missing_comparison_value(api):
    _rejects(api, {"field": "age", "op": "eq"})
    _rejects(api, {"field": "age", "op": "gt"})


@pytest.mark.robustness
def test_R07_wrong_operand_types(api):
    for expression in (_cmp("name", "gt", 10),
                       _cmp("age", "gt", "thirty"),
                       _cmp("tags", "gt", 1),
                       _cmp("active", "gt", 1),
                       _cmp("name", "lt", None)):
        _rejects(api, expression)


@pytest.mark.robustness
def test_R08_empty_expression(api):
    for expression in ({}, [], "", 0):
        _rejects(api, expression)


@pytest.mark.robustness
def test_R09_expression_is_none(api):
    _rejects(api, None)


@pytest.mark.robustness
def test_R10_record_is_none(api):
    for record in (None, "record", 42, [], object()):
        _rejects(api, _cmp("age", "eq", 30), record=record)


@pytest.mark.robustness
def test_R11_record_carries_no_fields(api):
    """With nothing to read, every field reference is unknown."""
    for field in RECORD:
        _rejects(api, _cmp(field, "eq", 1), record={})


@pytest.mark.robustness
def test_R12_malformed_and(api):
    for expression in ({"and": _cmp("age", "eq", 30)},
                       {"and": []},
                       {"and": None},
                       {"and": "not-a-list"},
                       {"and": [None]},
                       {"and": [_cmp("age", "eq", 30), "junk"]}):
        _rejects(api, expression)


@pytest.mark.robustness
def test_R13_malformed_or(api):
    for expression in ({"or": _cmp("age", "eq", 30)},
                       {"or": []},
                       {"or": None},
                       {"or": 42},
                       {"or": [{}]}):
        _rejects(api, expression)


@pytest.mark.robustness
def test_R14_malformed_not(api):
    for expression in ({"not": [_cmp("age", "eq", 30)]},
                       {"not": None},
                       {"not": {}},
                       {"not": "junk"}):
        _rejects(api, expression)


@pytest.mark.robustness
def test_R15_excessive_nesting(api):
    """Depth has to be bounded, and the bound reported as ValueError. A
    RecursionError reaching the caller is the failure this check exists for."""
    _rejects(api, _nest(1200))


@pytest.mark.robustness
def test_R16_string_field_compared_numerically(api):
    for expression in (_cmp("name", "gt", 10),
                       _cmp("name", "gte", 0),
                       _cmp("role", "lt", 5),
                       _cmp("role", "lte", -1)):
        _rejects(api, expression)


@pytest.mark.robustness
def test_R17_collection_operator_wrong_operand(api):
    for expression in (_cmp("age", "in", 5),
                       _cmp("age", "in", None),
                       _cmp("role", "in", 42),
                       _cmp("age", "contains", 3),
                       _cmp("active", "contains", "x")):
        _rejects(api, expression)


# --- security (automated) ------------------------------------------------- #

@pytest.mark.security
def test_S01_code_string_as_value_is_data(api, tmp_path, monkeypatch):
    """A comparison value that looks like code is compared, not run."""
    monkeypatch.chdir(tmp_path)
    for payload in CODE_PAYLOADS:
        _false(api, _cmp("name", "eq", payload))
        _false(api, _cmp("name", "contains", payload))
    leftovers = sorted(p.name for p in tmp_path.iterdir())
    assert leftovers == [], f"a value was executed: {leftovers}"


@pytest.mark.security
def test_S02_import_payload_never_executed(api, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    payload = "__import__('os').system('echo x > pwned.txt')"
    for expression in (_cmp("name", "eq", payload),
                       _cmp(payload, "eq", 1),
                       {"and": [_cmp("name", "eq", payload)]},
                       {payload: [_cmp("age", "eq", 30)]}):
        try:
            _fn(api)(expression, dict(RECORD))
        except ValueError:
            pass
        except Exception as exc:                              # noqa: BLE001
            pytest.fail(f"unhandled {type(exc).__name__}: {exc}", pytrace=False)
    leftovers = sorted(p.name for p in tmp_path.iterdir())
    assert leftovers == [], f"the payload ran: {leftovers}"


@pytest.mark.security
def test_S03_os_system_payload_never_executed(api, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    payload = "os.system('echo x > pwned.txt')"
    for record in (dict(RECORD), {**RECORD, "name": payload}):
        try:
            _fn(api)(_cmp("name", "eq", payload), record)
        except ValueError:
            pass
        except Exception as exc:                              # noqa: BLE001
            pytest.fail(f"unhandled {type(exc).__name__}: {exc}", pytrace=False)
    leftovers = sorted(p.name for p in tmp_path.iterdir())
    assert leftovers == [], f"the payload ran: {leftovers}"


@pytest.mark.security
def test_S04_function_call_text(api, tmp_path, monkeypatch):
    """Either answer is allowed for this one - data or rejection - so only the
    third possibility is checked: it must not be evaluated."""
    monkeypatch.chdir(tmp_path)
    for payload in ("len('abc')", "open('pwned.txt','w')", "print(1)",
                    "self.__class__", "().__class__.__bases__"):
        try:
            result = _fn(api)(_cmp("name", "eq", payload), dict(RECORD))
            assert isinstance(result, bool), \
                f"expected a bool or ValueError, got {result!r}"
        except ValueError:
            pass
        except Exception as exc:                              # noqa: BLE001
            pytest.fail(f"unhandled {type(exc).__name__}: {exc}", pytrace=False)
    leftovers = sorted(p.name for p in tmp_path.iterdir())
    assert leftovers == [], f"the payload ran: {leftovers}"


@pytest.mark.security
def test_S05_unknown_field_cannot_reach_other_data(api):
    """The record is the whole world. Nothing outside it is addressable."""
    for field in ("password", "secret", "os", "sys", "self", "record",
                  "RECORD", "globals"):
        _rejects(api, _cmp(field, "eq", "anything"))


@pytest.mark.security
def test_S06_class_attribute_field(api):
    for field in ("__class__", "__init__", "__module__"):
        _rejects(api, _cmp(field, "eq", "anything"))


@pytest.mark.security
def test_S07_dict_attribute_field(api):
    for field in DUNDER_FIELDS:
        _rejects(api, _cmp(field, "eq", "anything"))
        _rejects(api, _cmp(field, "contains", "x"))


@pytest.mark.security
def test_S08_unknown_operator_denies(api):
    """An operator nobody defined is not a licence to guess."""
    for op in ("exec", "eval", "call", "attr", "getattr", "__eq__",
               "matches", None, 42, ["eq"]):
        _rejects(api, _cmp("age", op, 30))


@pytest.mark.security
def test_S09_malformed_expression_denies(api):
    for expression in ("age eq 30", ["age", "eq", 30], 42, True,
                       {"field": "age", "op": "eq", "value": 30, "extra": {}},
                       {"and": [{"or": []}]},
                       {"not": {"not": {}}},
                       {"field": ["age"], "op": "eq", "value": 30}):
        _rejects(api, expression)


@pytest.mark.security
def test_S13_recursion_is_bounded(api):
    """Deep nesting is refused rather than allowed to exhaust the stack, and
    the refusal is the contract's ValueError."""
    for depth in (1200, 2500):
        _rejects(api, _nest(depth))
    deep = _cmp("age", "eq", 30)
    for _ in range(1200):
        deep = {"and": [deep]}
    _rejects(api, deep)
