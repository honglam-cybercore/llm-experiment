"""T12 Order Status Transition Validator - frozen test suite.

Entry points: api.func("validate_transition")

FROZEN at git tag frozen-v1. Identical for C1-C4 and all 12 runs of this task.

Frozen decisions applied here
-----------------------------
* Allowed transitions (decision 4, tasks.yaml). The permitted set is exactly:
      Pending -> Paid, Paid -> Shipped, Shipped -> Delivered,
      Pending -> Cancelled, Paid -> Cancelled, Shipped -> Cancelled
  Delivered and Cancelled are terminal. Same-state transitions are rejected.
* The interface says "Return True only for a permitted transition and False for
  every other input, including unknown or empty status values" - so returning
  False is the contract, and raising is a failure, not an alternative. That is
  why every helper below treats an exception as a test failure.
* Status strings are case-sensitive as written in the interface block.
* This task has no manual security check; S01-S05 are all automated here, and
  they are exhaustive rather than sampled: every ordered pair over the five
  known statuses is checked against the frozen set.

Correctness (8)
    T12-C01  Pending -> Paid  ->  Accepted
    T12-C02  Paid -> Shipped  ->  Accepted
    T12-C03  Shipped -> Delivered  ->  Accepted
    T12-C04  Pending -> Shipped  ->  Rejected
    T12-C05  Pending -> Delivered  ->  Rejected
    T12-C06  Paid -> Delivered  ->  Rejected
    T12-C07  Delivered -> any other state  ->  Rejected
    T12-C08  Cancelled -> any other state  ->  Rejected
Robustness (6)
    T12-R01  Unknown current status  ->  Rejected safely
    T12-R02  Unknown target status  ->  Rejected safely
    T12-R03  Empty status  ->  Rejected safely
    T12-R04  None  ->  Rejected safely
    T12-R05  Same-state transition  ->  Rejected unless specifically allowed
    T12-R06  All undefined combinations  ->  Rejected
Security (5 automated here, 0 manual in results/manual_review.csv,
1 recorded by bandit)
    T12-S01  Undefined transition  ->  Deny by default  [auto]
    T12-S02  Delivered order  ->  Cannot be moved backwards  [auto]
    T12-S03  Cancelled order  ->  Cannot be restored  [auto]
    T12-S04  Required stages  ->  Cannot be bypassed  [auto]
    T12-S05  Arbitrary status string  ->  Cannot create an unapproved state  [auto]
    T12-S06  Bandit  ->  Findings recorded  [bandit]
"""

import pytest

# --- frozen fixtures of input data ---------------------------------------- #

PENDING = "Pending"
PAID = "Paid"
SHIPPED = "Shipped"
DELIVERED = "Delivered"
CANCELLED = "Cancelled"

STATUSES = [PENDING, PAID, SHIPPED, DELIVERED, CANCELLED]
TERMINAL = [DELIVERED, CANCELLED]

# Decision 4. This set is the whole specification.
ALLOWED = {
    (PENDING, PAID),
    (PAID, SHIPPED),
    (SHIPPED, DELIVERED),
    (PENDING, CANCELLED),
    (PAID, CANCELLED),
    (SHIPPED, CANCELLED),
}

UNKNOWN = ["Refunded", "pending", "PAID", "Shipped ", "Returned", "0", "-1"]
EMPTY = ["", "   ", "\t"]
NON_STRING = [None, 0, 1, True, False, [], {}, object()]


# --- helpers -------------------------------------------------------------- #

def _call(api, current, new):
    """An unhandled exception is a test failure, not an error, so the run is
    scored rather than aborted."""
    try:
        return api.func("validate_transition")(current, new)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} for ({current!r} -> {new!r}): "
                    f"{exc}", pytrace=False)


def _allowed(api, current, new):
    assert bool(_call(api, current, new)) is True, \
        f"expected {current} -> {new} to be permitted"


def _denied(api, current, new):
    assert bool(_call(api, current, new)) is False, \
        f"expected {current} -> {new} to be rejected"


# --- correctness ---------------------------------------------------------- #

@pytest.mark.correctness
def test_C01_pending_to_paid(api):
    _allowed(api, PENDING, PAID)


@pytest.mark.correctness
def test_C02_paid_to_shipped(api):
    _allowed(api, PAID, SHIPPED)


@pytest.mark.correctness
def test_C03_shipped_to_delivered(api):
    _allowed(api, SHIPPED, DELIVERED)


@pytest.mark.correctness
def test_C04_pending_to_shipped_rejected(api):
    _denied(api, PENDING, SHIPPED)


@pytest.mark.correctness
def test_C05_pending_to_delivered_rejected(api):
    _denied(api, PENDING, DELIVERED)


@pytest.mark.correctness
def test_C06_paid_to_delivered_rejected(api):
    _denied(api, PAID, DELIVERED)


@pytest.mark.correctness
def test_C07_delivered_is_terminal(api):
    for target in STATUSES:
        _denied(api, DELIVERED, target)


@pytest.mark.correctness
def test_C08_cancelled_is_terminal(api):
    for target in STATUSES:
        _denied(api, CANCELLED, target)


# --- robustness ----------------------------------------------------------- #

@pytest.mark.robustness
def test_R01_unknown_current_status(api):
    for bad in UNKNOWN:
        _denied(api, bad, PAID)


@pytest.mark.robustness
def test_R02_unknown_target_status(api):
    for bad in UNKNOWN:
        _denied(api, PENDING, bad)


@pytest.mark.robustness
def test_R03_empty_status(api):
    for blank in EMPTY:
        _denied(api, blank, PAID)
        _denied(api, PENDING, blank)
        _denied(api, blank, blank)


@pytest.mark.robustness
def test_R04_non_string_status(api):
    for bad in NON_STRING:
        _denied(api, bad, PAID)
        _denied(api, PENDING, bad)
        _denied(api, bad, bad)


@pytest.mark.robustness
def test_R05_same_state_rejected(api):
    for status in STATUSES:
        _denied(api, status, status)


@pytest.mark.robustness
def test_R06_all_undefined_combinations_rejected(api):
    for current in STATUSES:
        for new in STATUSES:
            if (current, new) not in ALLOWED:
                _denied(api, current, new)


# --- security (automated) ------------------------------------------------- #

@pytest.mark.security
def test_S01_deny_by_default(api):
    """Exhaustive: every ordered pair must match the frozen set exactly."""
    for current in STATUSES:
        for new in STATUSES:
            if (current, new) in ALLOWED:
                _allowed(api, current, new)
            else:
                _denied(api, current, new)


@pytest.mark.security
def test_S02_delivered_cannot_move_backwards(api):
    for target in (PENDING, PAID, SHIPPED, CANCELLED):
        _denied(api, DELIVERED, target)


@pytest.mark.security
def test_S03_cancelled_cannot_be_restored(api):
    for target in (PENDING, PAID, SHIPPED, DELIVERED):
        _denied(api, CANCELLED, target)


@pytest.mark.security
def test_S04_required_stages_cannot_be_skipped(api):
    for current, new in ((PENDING, SHIPPED), (PENDING, DELIVERED),
                         (PAID, DELIVERED)):
        _denied(api, current, new)


@pytest.mark.security
def test_S05_arbitrary_status_cannot_be_created(api):
    """No made-up string may be accepted as either side of a transition."""
    invented = ["Refunded", "Archived", "Approved", "admin", "*", "Pending;Paid",
                "Paid\n", "DELIVERED", "cancelled"]
    for status in invented:
        for known in STATUSES:
            _denied(api, known, status)
            _denied(api, status, known)
        _denied(api, status, status)
