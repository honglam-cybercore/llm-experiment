"""Fixtures for the Task 13B suite.

run.py eval T13B runs this suite once per (implementation, dataset, data seed)
in an empty temp directory that holds only solution.py. Environment:

    LLME_SOLUTION  absolute path to the generated program
    LLME_RUN_ID    e.g. T13B_C1_r2
    LLME_DATASET   D0 | D1 | D2 | D3
    LLME_SEED      13 | 37 | 73
    LLME_OUT       directory that receives pairs.json, group.json, meta.json

The generated program never sees any of this: it only sees the records the
tests pass to train_model and score_candidates.
"""
from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from task13b import datagen, fixtures, harness          # noqa: E402

DATASET = os.environ.get("LLME_DATASET", "D0")
SEED = int(os.environ.get("LLME_SEED", "13"))
OUT = Path(os.environ["LLME_OUT"]) if os.environ.get("LLME_OUT") else None
CANARY_ID = "ZQ7-CANARY-CANDIDATE-ID"

_BASELINE_FILES = set(os.listdir("."))
_STATE: dict = {"load_error": "", "interface_error": "", "attempted": False,
                "pairs": {}, "group": None, "trace": None, "schema_notes": [],
                "api": None}


def pytest_configure(config):
    for marker in ("correctness", "robustness", "security", "gender", "channel",
                   "combined", "group", "invariance", "evaluator"):
        config.addinivalue_line("markers", f"{marker}: {marker} test")


# --------------------------------------------------------------------------- #
# program and data
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="session")
def api():
    if not _STATE["attempted"]:
        _STATE["attempted"] = True
        try:
            module = harness.load_solution(os.environ.get("LLME_SOLUTION", "solution.py"))
        except BaseException as exc:                      # noqa: BLE001
            _STATE["load_error"] = f"{type(exc).__name__}: {str(exc)[:300]}"
        else:
            try:
                _STATE["api"] = harness.Api(module)
            except harness.InterfaceError as exc:
                _STATE["interface_error"] = str(exc)[:300]
    if _STATE["api"] is None:
        pytest.fail(f"load_error: {_STATE['load_error']}" if _STATE["load_error"]
                    else f"interface_error: {_STATE['interface_error']}", pytrace=False)
    return _STATE["api"]


@pytest.fixture(scope="session")
def data():
    return datagen.load_bundle(SEED)


@pytest.fixture(scope="session")
def training_rows(data):
    return data["training"][DATASET]


@pytest.fixture(scope="session")
def fit_result(api, training_rows):
    """Fit once on the current dataset with random_state=42, traced. Everything
    that needs the full fit shares this one; failures surface in those tests."""
    rows = copy.deepcopy(training_rows)
    before = copy.deepcopy(rows)
    out = {"bundle": None, "error": None, "input_unchanged": None, "trace": None}
    with harness.LRTrace() as trace:
        try:
            out["bundle"] = api.train(rows, 42)
        except BaseException as exc:                      # noqa: BLE001
            out["error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
    out["input_unchanged"] = rows == before
    out["trace"] = trace
    _STATE["trace"] = {"fits": trace.fits,
                       "fit_seconds": list(api.fit_seconds)}
    return out


@pytest.fixture(scope="session")
def bundle(fit_result):
    if fit_result["bundle"] is None:
        pytest.fail(f"train_model failed on {DATASET}/seed {SEED}: {fit_result['error']}",
                    pytrace=False)
    return fit_result["bundle"]


@pytest.fixture(scope="session")
def minimal_bundle(api):
    try:
        return api.train(fixtures.minimal_train(), 42)
    except BaseException as exc:                          # noqa: BLE001
        pytest.fail(f"train_model failed on MINIMAL_TRAIN: "
                    f"{type(exc).__name__}: {str(exc)[:200]}", pytrace=False)


@pytest.fixture(scope="session")
def profiles(data):
    return data["profiles"]


def _pairs(kind, fn, api, bundle, profiles):
    if kind not in _STATE["pairs"]:
        _STATE["pairs"][kind] = fn(api, bundle, copy.deepcopy(profiles))
    return _STATE["pairs"][kind]


@pytest.fixture(scope="session")
def g_rows(api, bundle, profiles):
    return _pairs("G", harness.gender_pairs, api, bundle, profiles)


@pytest.fixture(scope="session")
def p_rows(api, bundle, profiles):
    return _pairs("P", harness.channel_pairs, api, bundle, profiles)


@pytest.fixture(scope="session")
def j_rows(api, bundle, profiles):
    return _pairs("J", harness.combined_pairs, api, bundle, profiles)


@pytest.fixture(scope="session")
def group_result(api, bundle, data):
    if _STATE["group"] is None:
        records = copy.deepcopy(data["group_records"])
        out, err = harness.safe_score(api, bundle, records)
        problem = None if err else harness.check_output(out, records)
        result = harness.group_metrics(data["group_records"], data["group_sidecar"],
                                       None if (err or problem) else out)
        result["error"] = err or (f"invalid output: {problem}" if problem else None)
        result["predictions"] = []
        if not (err or problem):
            for rec, side, row in zip(data["group_records"], data["group_sidecar"], out):
                result["predictions"].append({
                    "candidate_id": rec["candidate_id"], "gender": rec["gender"],
                    "channel": rec["recruitment_channel"],
                    "reference_merit": side["reference_merit_score"],
                    "reference_qualified": side["reference_qualified"],
                    "eligible": row["eligible"], "probability": row["hiring_probability"],
                    "selected": row["selected"], "valid": True, "error": ""})
        _STATE["group"] = result
    return _STATE["group"]


# --------------------------------------------------------------------------- #
# small helpers shared by the test modules
# --------------------------------------------------------------------------- #

def note_schema_problem(problem):
    if problem and problem not in _STATE["schema_notes"]:
        _STATE["schema_notes"].append(problem)


@pytest.fixture
def check():
    """check(out, records, expect_eligible=None): assert the schema, remember
    why it failed for the report."""
    def _check(out, records, expect_eligible=None):
        problem = harness.check_output(out, records, expect_eligible=expect_eligible)
        note_schema_problem(problem)
        assert problem is None, problem
        return out
    return _check


@pytest.fixture
def expect_value_error():
    """Invalid input raises ValueError - never a normal result, a silent
    coercion, a raw TypeError or a partial output."""
    def _expect(fn, note=""):
        try:
            result = fn()
        except ValueError:
            return
        except BaseException as exc:                      # noqa: BLE001
            pytest.fail(f"expected ValueError{note}, got {type(exc).__name__}: "
                        f"{str(exc)[:160]}", pytrace=False)
        pytest.fail(f"expected ValueError{note}, got a normal result: "
                    f"{repr(result)[:160]}", pytrace=False)
    return _expect


# --------------------------------------------------------------------------- #
# handing results to run.py
# --------------------------------------------------------------------------- #

def pytest_sessionfinish(session, exitstatus):
    if OUT is None:
        return
    try:
        OUT.mkdir(parents=True, exist_ok=True)
        api = _STATE["api"]
        meta = {
            "run_id": os.environ.get("LLME_RUN_ID", ""),
            "dataset": DATASET, "data_seed": SEED,
            "attempted": _STATE["attempted"],
            "load_error": bool(_STATE["load_error"]),
            "load_error_message": _STATE["load_error"],
            "interface_error": bool(_STATE["interface_error"]),
            "interface_message": _STATE["interface_error"],
            "schema_notes": _STATE["schema_notes"][:20],
            "files_written": sorted(set(os.listdir(".")) - _BASELINE_FILES
                                    - {"__pycache__"}),
            "fit_seconds": list(api.fit_seconds) if api else [],
            "max_score_seconds": max(api.score_seconds) if api and api.score_seconds else None,
            "trace": _STATE["trace"],
        }
        (OUT / "meta.json").write_text(json.dumps(meta, default=str), encoding="utf-8")
        rows = []
        for kind in ("G", "P", "J"):
            rows.extend(_STATE["pairs"].get(kind, []))
        (OUT / "pairs.json").write_text(json.dumps(rows), encoding="utf-8")
        if _STATE["group"] is not None:
            (OUT / "group.json").write_text(json.dumps(_STATE["group"], default=str),
                                            encoding="utf-8")
    except OSError:
        pass
