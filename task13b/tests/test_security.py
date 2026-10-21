"""T13B-S01 .. S10.

Automated here: S01, S02, S03, S07.
Manual source review (results/<lane>/manual_review.csv): S04, S05, S06, S08, S09.
  The collector stores pointer evidence for them (source_flags, files written
  during the run, the traced feature columns); the verdict is a human one.
S10 is Bandit, recorded as findings, not as a pass/fail.
"""
import copy
import os

import pytest

from task13b import fixtures
from task13b.fixtures import base_b, minimal_train
from conftest import CANARY_ID

pytestmark = pytest.mark.security


def _canary_training():
    rows = minimal_train()
    rows[0]["candidate_id"] = CANARY_ID
    return rows


def test_S01_nothing_is_printed(api, capfd):
    capfd.readouterr()
    bundle = None
    for attempt in (
            lambda: api.train(_canary_training(), 42),
            lambda: api.train([dict(r, gender="x") if i == 0 else r
                               for i, r in enumerate(_canary_training())], 42)):
        try:
            result = attempt()
            bundle = bundle or result
        except Exception:                               # noqa: BLE001
            pass
    if bundle is not None:
        for records in ([base_b(candidate_id=CANARY_ID)],
                        [base_b(candidate_id=CANARY_ID, gender="Unknown")]):
            try:
                api.score(bundle, records)
            except Exception:                           # noqa: BLE001
                pass
    captured = capfd.readouterr()
    stream = captured.out + captured.err
    assert "ZQ7-CANARY" not in stream, f"candidate id reached the output: {stream[:200]!r}"
    assert "MINI_" not in stream, f"a candidate record reached the output: {stream[:200]!r}"


def test_S02_errors_do_not_expose_the_record(api, minimal_bundle):
    messages = []
    for case in fixtures.RP_CASES:
        records = fixtures.prediction_input_for(case)
        if isinstance(records, list):
            records = [dict(r, candidate_id=CANARY_ID)
                       if isinstance(r, dict) and "candidate_id" in r
                       and case.get("row_mutation", {}).get("set", (None,))[0] != "candidate_id"
                       and r["candidate_id"] == "BASE_B" else r for r in records]
        try:
            api.score(minimal_bundle, records)
        except ValueError as exc:
            messages.append(str(exc))
        except BaseException:                           # noqa: BLE001
            pass
    for case in fixtures.RT_CASES:
        try:
            records, state = fixtures.training_input_for(case)
            if isinstance(records, list) and records and isinstance(records[0], dict) \
                    and records[0].get("candidate_id", "").startswith("MINI_"):
                records[0]["candidate_id"] = CANARY_ID
            api.train(records, state)
        except ValueError as exc:
            messages.append(str(exc))
        except BaseException:                           # noqa: BLE001
            pass
    assert messages, "no validation case raised ValueError"
    names = fixtures.TRAIN_FIELDS
    for message in messages:
        assert CANARY_ID not in message, f"error message exposes the id: {message!r}"
        assert "MINI_" not in message and "BASE_B" not in message, \
            f"error message exposes an id: {message!r}"
        named = sum(1 for n in names if n in message)
        assert named <= 3, (f"the error names {named} of the {len(names)} fields, which "
                            f"reads as a dump of the record: {message!r}")
        assert len(message) < 400, f"error message is {len(message)} characters: {message[:120]!r}"


def test_S03_code_like_id_is_data(api):
    code_ids = ("__import__('math').sqrt(4)",
                "__import__('os').system('echo x > pwned.txt')",
                "$(touch pwned.txt)", "'; DROP TABLE candidates; --", "{{7*7}}")
    before = set(os.listdir("."))
    rows = minimal_train()
    rows[0]["candidate_id"] = code_ids[0]
    bundle = api.train(rows, 42)
    for value in code_ids:
        records = [base_b(candidate_id=value)]
        out = api.score(bundle, records)
        assert out[0]["candidate_id"] == value, "the id should come back unchanged as data"
    created = sorted(set(os.listdir(".")) - before - {"__pycache__"})
    assert created == [], f"a candidate id was executed: {created}"


@pytest.mark.parametrize("field", fixtures.ELIGIBILITY)
@pytest.mark.parametrize("value", ["True", "true", 1, 1.0, None], ids=lambda v: repr(v))
def test_S07_type_confusion_cannot_grant_eligibility(api, minimal_bundle, expect_value_error,
                                                     field, value):
    expect_value_error(lambda: api.score(minimal_bundle, [base_b(**{field: value})]),
                       note=f" for scoring {field}={value!r}")
    rows = minimal_train()
    rows[0][field] = value
    expect_value_error(lambda: api.train(rows, 42), note=f" for training {field}={value!r}")
