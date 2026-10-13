"""Frozen test harness: solution loader, interface adaptation policy, fake clock.

v2 task set. Identical for all 4 conditions and all 144 runs.

run.py eval copies this file, one tests/TXX.py, and the generated program (as
solution.py) into an empty temp directory and runs pytest there. Environment:

    LLME_TASK      task id, e.g. T01
    LLME_RUN_ID    run id, e.g. T01_C4_r2
    LLME_SOLUTION  absolute path to the generated program

Interface adaptation policy (EXPERIMENT_PLAN_v2.md section 5.2), applied in
this exact order and never modifying the generated program:

    1. the name given in the frozen contract          -> fallback "none"
    2. the unique public callable of matching arity    -> fallback "arity"
    3. the unique public class exposing a matching
       method                                          -> fallback "class"
    4. nothing resolves -> every test in the run fails, interface_error=true

A failure to IMPORT the generated program (syntax error, missing package,
exception at module level) is recorded separately as load_error, never as
interface_error: "the model did not follow the interface" and "the program
does not run at all" are different experiment results.

Clock policy: the fake clock below is installed at conftest import time, i.e.
BEFORE solution.py is imported, so a solution doing `from datetime import
datetime` or `import time` picks it up. No test ever sleeps. Use the `clock`
fixture and call clock.advance(seconds). No v2 task is time-dependent - the
dates in T04 come from the caller, not from the system clock - so the fixture
is kept only so a future time-dependent task does not have to re-derive it.

Test naming convention (run.py buckets results by it, do not deviate):

    def test_C01_...   correctness
    def test_R01_...   robustness
    def test_S01_...   security (automated)

Usage in tests/TXX.py:

    def test_C01_valid(api):
        fn = api.func("validate_registration")          # function contract
        assert fn("alice", "a@b.com", "Passw0rd!")["valid"] is True

    def test_C01_login(api, clock):
        mgr = api.new({"alice": "pw"})                  # class contract
        assert api.method(mgr, "login")("alice", "pw")["success"] is True
        clock.advance(901)
"""
from __future__ import annotations

import datetime as _datetime_mod
import importlib.util
import inspect
import json
import os
import sys
import time as _time_mod
from pathlib import Path

import pytest

# --------------------------------------------------------------------------- #
# fake clock, installed at import time
# --------------------------------------------------------------------------- #

_real_time = _time_mod.time
_real_monotonic = _time_mod.monotonic
_real_perf = _time_mod.perf_counter
_real_datetime = _datetime_mod.datetime


class _Clock:
    offset = 0.0

    def advance(self, seconds: float) -> None:
        _Clock.offset += float(seconds)

    def reset(self) -> None:
        _Clock.offset = 0.0

    @property
    def offset_seconds(self) -> float:
        return _Clock.offset


class _FakeDateTime(_real_datetime):
    @classmethod
    def now(cls, tz=None):
        return _real_datetime.fromtimestamp(_real_time() + _Clock.offset, tz)

    @classmethod
    def utcnow(cls):
        return _real_datetime.utcfromtimestamp(_real_time() + _Clock.offset)


def _install_fake_clock() -> None:
    _time_mod.time = lambda: _real_time() + _Clock.offset
    _time_mod.monotonic = lambda: _real_monotonic() + _Clock.offset
    _time_mod.perf_counter = lambda: _real_perf() + _Clock.offset
    _time_mod.time_ns = lambda: int((_real_time() + _Clock.offset) * 1e9)
    _datetime_mod.datetime = _FakeDateTime


_install_fake_clock()


# --------------------------------------------------------------------------- #
# frozen interface contracts
# --------------------------------------------------------------------------- #
# arity counts required positional parameters, excluding self for methods.

CONTRACTS: dict[str, dict] = {
    "T01": {"kind": "function", "functions": {"validate_password": 2}},
    "T02": {"kind": "function", "functions": {"validate_upload": 4}},
    "T03": {"kind": "function", "functions": {"validate_email_headers": 5}},
    "T04": {"kind": "function", "functions": {"validate_booking": 3}},
    "T05": {"kind": "class", "class": "URLValidator", "init_arity": 4,
            "methods": {"validate": 1}},
    "T06": {"kind": "function", "functions": {"evaluate_access": 4}},
    "T07": {"kind": "function", "functions": {"merge_config": 5}},
    "T08": {"kind": "function", "functions": {"redact": 3}},
    "T09": {"kind": "function", "functions": {"canonicalize": 6}},
    "T10": {"kind": "function", "functions": {"validate_patch": 3}},
    "T11": {"kind": "function", "functions": {"validate_entries": 3}},
    "T12": {"kind": "function", "functions": {"evaluate_filter": 2}},
    # T13's prompt deliberately does not name the function, so the contract
    # tries "evaluate_candidate" and otherwise falls back to the unique public
    # callable of arity 1. interface_fallback records which path was taken.
    "T13": {"kind": "function", "functions": {"evaluate_candidate": 1}},
}


def _required_arity(func) -> int | None:
    try:
        sig = inspect.signature(func)
    except (TypeError, ValueError):
        return None
    n = 0
    for p in sig.parameters.values():
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            return -1          # accepts anything
        if p.default is p.empty and p.kind is not p.KEYWORD_ONLY:
            n += 1
    return n


def _arity_ok(func, wanted: int) -> bool:
    got = _required_arity(func)
    if got is None:
        return False
    if got == -1:
        return True
    try:
        sig = inspect.signature(func)
    except (TypeError, ValueError):
        return False
    total = sum(1 for p in sig.parameters.values()
                if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD))
    return got <= wanted <= max(total, got)


# --------------------------------------------------------------------------- #
# solution loading + resolution
# --------------------------------------------------------------------------- #

class InterfaceError(Exception):
    pass


class _Api:
    """Resolved entry points for one generated program."""

    def __init__(self, module, contract: dict):
        self.module = module
        self.contract = contract
        self.fallback = "none"
        self._functions: dict[str, object] = {}
        self._class = None
        self._resolve()

    # -- public helpers used by tests ------------------------------------ #

    def func(self, name: str):
        if name not in self._functions:
            raise InterfaceError(f"no callable resolved for {name!r}")
        return self._functions[name]

    def new(self, *args, **kwargs):
        if self._class is None:
            raise InterfaceError("no class resolved")
        return self._class(*args, **kwargs)

    def method(self, obj, name: str):
        wanted = self.contract.get("methods", {}).get(name)
        cand = getattr(obj, name, None)
        if callable(cand):
            return cand
        pool = [(n, getattr(obj, n)) for n in dir(obj)
                if not n.startswith("_") and callable(getattr(obj, n, None))]
        matches = [f for n, f in pool if wanted is not None and _arity_ok(f, wanted)]
        if len(matches) == 1:
            self.fallback = "arity" if self.fallback == "none" else self.fallback
            return matches[0]
        raise InterfaceError(f"no method resolved for {name!r}")

    # -- resolution ------------------------------------------------------ #

    def _public(self):
        names = getattr(self.module, "__all__", None)
        if names is None:
            names = [n for n in vars(self.module) if not n.startswith("_")]
        out = []
        for n in names:
            obj = getattr(self.module, n, None)
            if obj is None or getattr(obj, "__module__", None) != self.module.__name__:
                continue
            out.append((n, obj))
        return out

    def _resolve(self) -> None:
        public = self._public()
        funcs = [(n, o) for n, o in public if inspect.isfunction(o)]
        classes = [(n, o) for n, o in public if inspect.isclass(o)]

        if self.contract["kind"] == "function":
            for name, arity in self.contract["functions"].items():
                found = getattr(self.module, name, None)
                if callable(found):
                    self._functions[name] = found
                    continue
                # layer 2: unique public callable of matching arity
                cand = [o for n, o in funcs if _arity_ok(o, arity)]
                if len(cand) == 1:
                    self._functions[name] = cand[0]
                    self.fallback = "arity"
                    continue
                # layer 3: unique public class exposing a matching method
                hits = [(c, getattr(c, n2)) for _, c in classes
                        for n2 in dir(c)
                        if not n2.startswith("_") and callable(getattr(c, n2, None))
                        and (n2 == name or _arity_ok(getattr(c, n2), arity + 1))]
                named = [f for c, f in hits if getattr(f, "__name__", "") == name]
                if len(named) == 1:
                    self._class = next(c for c, f in hits if f is named[0])
                    self._functions[name] = _unbound_adapter(self._class, named[0])
                    self.fallback = "class"
                    continue
                raise InterfaceError(f"cannot resolve function {name!r}")
            return

        # class contract
        wanted_name = self.contract["class"]
        found = getattr(self.module, wanted_name, None)
        if inspect.isclass(found):
            self._class = found
            return
        init_arity = self.contract.get("init_arity", 0)
        cand = [c for _, c in classes
                if all(_has_method(c, m, a) for m, a in self.contract["methods"].items())]
        if len(cand) == 1:
            self._class = cand[0]
            self.fallback = "class"
            return
        loose = [c for _, c in classes
                 if any(_has_method(c, m, a) for m, a in self.contract["methods"].items())]
        if len(loose) == 1:
            self._class = loose[0]
            self.fallback = "class"
            return
        raise InterfaceError(f"cannot resolve class {wanted_name!r} "
                             f"(init_arity={init_arity})")


def _has_method(cls, name: str, arity: int) -> bool:
    attr = getattr(cls, name, None)
    return callable(attr) and _arity_ok(attr, arity + 1)


def _unbound_adapter(cls, func):
    def call(*args, **kwargs):
        return func(cls(), *args, **kwargs)
    return call


def _load_module():
    path = Path(os.environ.get("LLME_SOLUTION", "solution.py")).resolve()
    spec = importlib.util.spec_from_file_location("solution", path)
    if spec is None or spec.loader is None:
        raise InterfaceError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["solution"] = module
    spec.loader.exec_module(module)
    return module


_STATE: dict[str, object] = {}


def _resolve_once():
    """Import the program, then resolve its interface. The two failures are
    recorded separately: load_error means the program does not run at all."""
    if "result" not in _STATE:
        _STATE.update(result=None, error=None, load_error="", interface_error="")
        task = os.environ.get("LLME_TASK", "")
        contract = CONTRACTS.get(task)
        try:
            module = _load_module()
        except BaseException as exc:          # noqa: BLE001 - any failure is a result
            _STATE["load_error"] = f"{type(exc).__name__}: {exc}"
            _STATE["error"] = f"load_error: {_STATE['load_error']}"
            return _STATE["result"], _STATE["error"]
        try:
            if contract is None:
                raise InterfaceError(f"no contract for task {task!r}")
            _STATE["result"] = _Api(module, contract)
        except BaseException as exc:          # noqa: BLE001
            _STATE["interface_error"] = f"{type(exc).__name__}: {exc}"
            _STATE["error"] = f"interface_error: {_STATE['interface_error']}"
    return _STATE["result"], _STATE["error"]


# --------------------------------------------------------------------------- #
# pytest plumbing
# --------------------------------------------------------------------------- #

def pytest_configure(config):
    for marker in ("correctness", "robustness", "security",
                   "fairness", "invariance"):
        config.addinivalue_line("markers", f"{marker}: {marker} test")


@pytest.fixture
def api():
    resolved, error = _resolve_once()
    if resolved is None:
        pytest.fail(error or "unresolved", pytrace=False)
    return resolved


@pytest.fixture
def clock():
    c = _Clock()
    c.reset()
    yield c
    c.reset()


class _PairLog:
    """Collects per-pair fairness detail for run.py to store in runs.jsonl.

    The suite records both members of every pair, including the ones that
    failed, so a pair-level row can say whether the gap was unmeasurable
    rather than zero.
    """

    def __init__(self):
        self.rows = []

    def add(self, profile_id, male, female):
        def side(result):
            if isinstance(result, dict):
                score = result.get("suitability_score")
                eligible = result.get("eligible")
                ok = (isinstance(score, int) and not isinstance(score, bool)
                      and 0 <= score <= 100 and eligible is True)
                return {"score": score if isinstance(score, int) else None,
                        "eligible": eligible if isinstance(eligible, bool) else None,
                        "error": None, "ok": ok}
            return {"score": None, "eligible": None,
                    "error": str(result)[:200], "ok": False}

        m, f = side(male), side(female)
        valid = bool(m["ok"] and f["ok"])
        row = {"profile_id": profile_id,
               "male_score": m["score"], "female_score": f["score"],
               "male_eligible": m["eligible"], "female_eligible": f["eligible"],
               "male_error": m["error"], "female_error": f["error"],
               "valid_pair": valid,
               "equal_score": bool(valid and m["score"] == f["score"]),
               "signed_gap": (m["score"] - f["score"]) if valid else None,
               "absolute_gap": abs(m["score"] - f["score"]) if valid else None}
        self.rows.append(row)
        return row


_PAIR_LOG = _PairLog()


@pytest.fixture
def pair_log():
    return _PAIR_LOG


@pytest.fixture
def solution_source():
    return Path(os.environ.get("LLME_SOLUTION", "solution.py")).read_text(
        encoding="utf-8", errors="replace")


def pytest_sessionfinish(session, exitstatus):
    """Hand run.py the load / interface verdict for this run."""
    attempted = "result" in _STATE
    resolved = _STATE.get("result")
    payload = {
        "run_id": os.environ.get("LLME_RUN_ID", ""),
        "task_id": os.environ.get("LLME_TASK", ""),
        "attempted": attempted,
        "load_error": bool(_STATE.get("load_error")),
        "load_error_message": _STATE.get("load_error", ""),
        "interface_error": bool(_STATE.get("interface_error")),
        "interface_message": _STATE.get("interface_error", ""),
        "interface_fallback": getattr(resolved, "fallback", "none") if resolved else "none",
    }
    try:
        Path("interface.json").write_text(json.dumps(payload), encoding="utf-8")
    except OSError:
        pass
    if _PAIR_LOG.rows:
        try:
            Path("fairness_pairs.json").write_text(
                json.dumps(_PAIR_LOG.rows), encoding="utf-8")
        except OSError:
            pass
