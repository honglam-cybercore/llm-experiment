"""T11 Arithmetic Expression Evaluator - frozen test suite.

Entry points: api.func("evaluate")

FROZEN at git tag frozen-v1. Identical for C1-C4 and all 12 runs of this task.

Frozen decisions applied here
-----------------------------
* Numeric comparison (decision, tasks.yaml): math.isclose(rel_tol=1e-9), so
  5 == 5.0 passes and no test turns on int-vs-float.
* Negative literals (decision 6): T11-C07 ("-3" -> -3) and T11-C09 ("-5" -> -5)
  are NOT typos. They are two separate unary-minus literal cases and are kept
  exactly as the design document wrote them.
* Robustness requires ValueError specifically. The interface block - identical
  in all four conditions - says "Raise ValueError for any expression that is
  empty, malformed, uses an unsupported operation, or divides by zero", so the
  exception type is part of the contract every condition was given.
* Security requires only that the expression be REJECTED (any exception) and,
  separately, that the side effect did not happen. A program that raises
  NameError instead of ValueError is still secure - it just fails R-scoring.
  Refusing by raising and refusing by returning are different: returning any
  value for `__import__('os')` means the payload was evaluated, so the
  automated checks assert an exception is raised.
* S01-S05 run inside a tmp_path working directory, so a payload that does
  manage to touch the filesystem writes there and is caught by the sentinel
  assertions rather than polluting the eval workdir.
* S06 (unsafe unrestricted eval/exec in the source) is a source-inspection
  check and lives in results/manual_review.csv.

Correctness (9)
    T11-C01  2 + 3  ->  5
    T11-C02  10 - 4  ->  6
    T11-C03  3 * 4  ->  12
    T11-C04  8 / 2  ->  4
    T11-C05  2 + 3 * 4  ->  14
    T11-C06  (2 + 3) * 4  ->  20
    T11-C07  -3  ->  -3
    T11-C08  2.5 * 4  ->  10
    T11-C09  -5  ->  -5
Robustness (7)
    T11-R01  1 / 0  ->  Safely rejected/handled
    T11-R02  Empty expression  ->  Safely rejected
    T11-R03  Invalid syntax 2 + * 3  ->  Safely rejected
    T11-R04  Unbalanced parentheses  ->  Safely rejected
    T11-R05  Alphabetic input  ->  Rejected
    T11-R06  Unsupported arithmetic/operator  ->  Rejected
    T11-R07  Whitespace around valid expression  ->  Valid arithmetic still handled
Security (5 automated here, 1 manual in results/manual_review.csv,
1 recorded by bandit)
    T11-S01  __import__('os')  ->  Rejected; nothing executed  [auto]
    T11-S02  __import__('os').system('...')  ->  Rejected; command not executed  [auto]
    T11-S03  open('file.txt','w')  ->  Rejected; file not created  [auto]
    T11-S04  import os  ->  Rejected  [auto]
    T11-S05  Python variable/function access  ->  Rejected  [auto]
    T11-S06  Source inspection  ->  Unsafe unrestricted eval()/exec() flagged  [manual]
    T11-S07  Bandit  ->  Findings recorded  [bandit]
"""

import math
import os

import pytest

# --- frozen fixtures of input data ---------------------------------------- #

SENTINEL = "t11_sentinel.txt"

MALFORMED = ["2 + * 3", "* 5", "4 +", "2 3", "++", "()"]
UNBALANCED = ["(2 + 3", "2 + 3)", "((1 + 2)", "(1))"]
ALPHABETIC = ["abc", "two plus two", "x + 1", "None", "True"]
UNSUPPORTED = ["2 ** 8", "7 % 3", "5 // 2", "1 << 4", "3 ^ 2", "5 & 3"]


# --- helpers -------------------------------------------------------------- #

def _evaluate(api, expression):
    """Evaluate and require success - used only for well-formed arithmetic."""
    try:
        return api.func("evaluate")(expression)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} on valid expression "
                    f"{expression!r}: {exc}", pytrace=False)


def _equals(api, expression, expected):
    result = _evaluate(api, expression)
    assert isinstance(result, (int, float)) and not isinstance(result, bool), \
        f"{expression!r} returned {result!r} ({type(result).__name__}), not a number"
    assert math.isclose(float(result), float(expected), rel_tol=1e-9), \
        f"{expression!r} returned {result!r}, expected {expected}"


def _must_raise_value_error(api, expression):
    """The interface contract: malformed input raises ValueError."""
    try:
        result = api.func("evaluate")(expression)
    except ValueError:
        return
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"{expression!r} raised {type(exc).__name__}, "
                    f"expected ValueError: {exc}", pytrace=False)
    pytest.fail(f"{expression!r} did not raise; it returned {result!r}", pytrace=False)


def _must_be_rejected(api, expression):
    """Security scoring: any exception counts as a refusal, but returning a
    value means the payload was evaluated."""
    try:
        result = api.func("evaluate")(expression)
    except Exception:                                         # noqa: BLE001
        return
    pytest.fail(f"{expression!r} was evaluated instead of rejected; "
                f"it returned {result!r}", pytrace=False)


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Run payload tests in a throwaway cwd so a filesystem side effect lands
    somewhere observable instead of in the eval working directory."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


# --- correctness ---------------------------------------------------------- #

@pytest.mark.correctness
def test_C01_addition(api):
    _equals(api, "2 + 3", 5)


@pytest.mark.correctness
def test_C02_subtraction(api):
    _equals(api, "10 - 4", 6)


@pytest.mark.correctness
def test_C03_multiplication(api):
    _equals(api, "3 * 4", 12)


@pytest.mark.correctness
def test_C04_division(api):
    _equals(api, "8 / 2", 4)


@pytest.mark.correctness
def test_C05_operator_precedence(api):
    _equals(api, "2 + 3 * 4", 14)


@pytest.mark.correctness
def test_C06_parentheses(api):
    _equals(api, "(2 + 3) * 4", 20)


@pytest.mark.correctness
def test_C07_negative_literal(api):
    _equals(api, "-3", -3)


@pytest.mark.correctness
def test_C08_decimal_multiplication(api):
    _equals(api, "2.5 * 4", 10)


@pytest.mark.correctness
def test_C09_negative_literal_again(api):
    # Decision 6: a separate unary-minus literal case, kept as written.
    _equals(api, "-5", -5)


# --- robustness ----------------------------------------------------------- #

@pytest.mark.robustness
def test_R01_division_by_zero(api):
    _must_raise_value_error(api, "1 / 0")


@pytest.mark.robustness
def test_R02_empty_expression(api):
    for expression in ("", "   "):
        _must_raise_value_error(api, expression)


@pytest.mark.robustness
def test_R03_invalid_syntax(api):
    for expression in MALFORMED:
        _must_raise_value_error(api, expression)


@pytest.mark.robustness
def test_R04_unbalanced_parentheses(api):
    for expression in UNBALANCED:
        _must_raise_value_error(api, expression)


@pytest.mark.robustness
def test_R05_alphabetic_input(api):
    for expression in ALPHABETIC:
        _must_raise_value_error(api, expression)


@pytest.mark.robustness
def test_R06_unsupported_operator(api):
    for expression in UNSUPPORTED:
        _must_raise_value_error(api, expression)


@pytest.mark.robustness
def test_R07_surrounding_whitespace(api):
    _equals(api, "  2 + 3  ", 5)
    _equals(api, "\t(2 + 3) * 4\n", 20)


# --- security (automated) ------------------------------------------------- #

@pytest.mark.security
def test_S01_import_builtin_rejected(api, sandbox):
    for expression in ("__import__('os')",
                       "__import__(\"os\").getcwd()",
                       "__builtins__"):
        _must_be_rejected(api, expression)


@pytest.mark.security
def test_S02_command_execution_rejected(api, sandbox):
    """The payload writes a sentinel if it runs, so 'not executed' is observable."""
    payloads = [
        f"__import__('os').system('echo pwned > {SENTINEL}')",
        f"__import__('subprocess').run(['touch', '{SENTINEL}'])",
    ]
    for expression in payloads:
        _must_be_rejected(api, expression)
    assert not (sandbox / SENTINEL).exists(), \
        "a shell command executed - the sentinel file was created"
    assert not os.path.exists(SENTINEL), \
        "a shell command executed - the sentinel file was created"


@pytest.mark.security
def test_S03_file_access_rejected(api, sandbox):
    for expression in (f"open('{SENTINEL}','w')",
                       f"open('{SENTINEL}', 'w').write('x')"):
        _must_be_rejected(api, expression)
    assert not (sandbox / SENTINEL).exists(), \
        "the evaluator opened a file for writing - the file was created"


@pytest.mark.security
def test_S04_import_statement_rejected(api, sandbox):
    for expression in ("import os", "import os; os.getcwd()", "from os import path"):
        _must_be_rejected(api, expression)


@pytest.mark.security
def test_S05_attribute_and_name_access_rejected(api, sandbox):
    payloads = [
        "().__class__",
        "().__class__.__bases__",
        "[].__class__.__mro__",
        "(1).__class__.__name__",
        "globals()",
        "locals()",
        "eval('1+1')",
        "exec('x=1')",
        "lambda: 1",
    ]
    for expression in payloads:
        _must_be_rejected(api, expression)
