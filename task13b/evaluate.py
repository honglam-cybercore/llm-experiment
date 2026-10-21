"""Run the Task 13B suite against one generated program.

One implementation is fitted and scored 12 times (4 datasets x 3 data seeds);
the same pytest suite runs for each fit. This module is the subprocess driver:
it copies the program into an empty temp directory, runs pytest with the 13B
interpreter, and reads back what the suite wrote. run.py eval T13B calls it.

Nothing here edits, repairs or wraps the program.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from . import harness

ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = ROOT / "task13b" / "tests"
# Literals, not imported from datagen: run.py imports this module under the frozen
# .venv, which has no numpy, and datagen needs it. The two are asserted equal in
# the selfcheck (test_evaluator.py::test_E02_sizes imports both).
DATASETS = ("D0", "D1", "D2", "D3")
DATA_SEEDS = (13, 37, 73)

# function-name prefix -> reporting dimension
DIMENSIONS = {"C": "correctness", "RT": "robustness", "RP": "robustness",
              "RM": "robustness", "G": "gender", "P": "channel", "J": "combined",
              "Q": "group", "I": "invariance", "S": "security"}
# The five S checks that need a human reading the source; S10 is Bandit.
MANUAL_CHECKS = ["S04", "S05", "S06", "S08", "S09"]


def venv_python() -> str:
    """The interpreter that has numpy / pandas / scikit-learn. Falls back to the
    running interpreter so a CI box with one environment still works."""
    for candidate in (ROOT / ".venv13b" / "Scripts" / "python.exe",
                      ROOT / ".venv13b" / "bin" / "python"):
        if candidate.exists():
            return str(candidate)
    return sys.executable


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def harness_hash() -> str:
    """One hash over every file that defines the evaluation, so a run can say
    exactly which harness produced it."""
    h = hashlib.sha256()
    files = sorted(list((ROOT / "task13b").glob("*.py")) + list(TESTS_DIR.glob("*.py")))
    for f in files:
        h.update(f.name.encode())
        h.update(f.read_bytes())
    manifest = ROOT / "task13b" / "data" / "manifest.json"
    if manifest.exists():
        h.update(manifest.read_bytes())
    return h.hexdigest()


def _kind_and_case(nodeid: str) -> tuple[str, str]:
    name = nodeid.split("::")[-1]
    param = None
    if "[" in name and name.endswith("]"):
        name, param = name[:-1].split("[", 1)
    parts = name.split("_")                  # test, C01, ...   or  test, RT, training
    token = parts[1] if len(parts) > 1 else ""
    kind = "".join(ch for ch in token if ch.isalpha())
    if token[:2] in ("RT", "RP", "RM"):
        kind = token[:2]
    case = param if (param and param[:1] in "CRGPJQIS" and param[1:2].isdigit()
                     or (param or "")[:2] in ("RT", "RP", "RM")) else token
    if kind == "S" and param is not None:    # S07[field-value]: one S07 outcome
        case = token
    return kind, case


def _read_report(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    out = []
    for item in data.get("tests", []):
        kind, case = _kind_and_case(item.get("nodeid", ""))
        if kind not in DIMENSIONS:
            continue
        outcome = item.get("outcome", "error")
        call = item.get("call") or {}
        crash = call.get("crash") or {}
        message = (crash.get("message") or "").strip().replace("\n", " ")
        if outcome != "passed" and not message:
            setup = item.get("setup") or {}
            message = ((setup.get("crash") or {}).get("message") or
                       (setup.get("longrepr") or "")).strip().replace("\n", " ")
        etype = ""
        if message.startswith("Failed:") or "pytest.fail" in message:
            etype = "Failed"
        elif ":" in message:
            etype = message.split(":", 1)[0].strip()[:60]
        out.append({"case_id": case, "dimension": DIMENSIONS[kind], "kind": kind,
                    "nodeid": item.get("nodeid", ""), "status": outcome,
                    "error_type": etype if outcome != "passed" else "",
                    "error_message": message[:300] if outcome != "passed" else "",
                    "duration_seconds": round(sum((item.get(k) or {}).get("duration", 0.0)
                                                  for k in ("setup", "call", "teardown")), 4)})
    return out


def aggregate_cases(cases: list[dict]) -> list[dict]:
    """Fold parametrised S07 into one outcome (the spec counts S01-S09 as nine
    checklist items); every other case keeps one row."""
    merged: dict[str, dict] = {}
    rows = []
    for c in cases:
        if c["kind"] == "S":
            slot = merged.setdefault(c["case_id"], dict(c, duration_seconds=0.0))
            slot["duration_seconds"] += c["duration_seconds"]
            if c["status"] != "passed" and slot["status"] == "passed":
                slot.update(status=c["status"], error_type=c["error_type"],
                            error_message=c["error_message"])
            continue
        rows.append(c)
    return rows + list(merged.values())


def run_suite(solution: Path, run_id: str, dataset: str, seed: int, out_dir: Path,
              timeout: int = 900, python: str | None = None) -> dict:
    """One pytest session. Returns {"status", "cases", "meta", "pairs", "group"}."""
    out_dir.mkdir(parents=True, exist_ok=True)
    workdir = Path(tempfile.mkdtemp(prefix=f"t13b_{run_id}_{dataset}_{seed}_"))
    try:
        shutil.copy(solution, workdir / "solution.py")
        report = out_dir / "report.json"
        env = dict(os.environ,
                   LLME_SOLUTION=str(workdir / "solution.py"), LLME_RUN_ID=run_id,
                   LLME_DATASET=dataset, LLME_SEED=str(seed), LLME_OUT=str(out_dir),
                   PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(ROOT),
                   OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
        cmd = [python or venv_python(), "-m", "pytest", str(TESTS_DIR),
               "-p", "no:cacheprovider", "-q", "--json-report",
               f"--json-report-file={report}", "--tb=short"]
        status, stdout, stderr = "ok", "", ""
        try:
            proc = subprocess.run(cmd, cwd=workdir, env=env, stdin=subprocess.DEVNULL,
                                  capture_output=True, text=True, encoding="utf-8",
                                  errors="replace", timeout=timeout)
            stdout, stderr = proc.stdout, proc.stderr
            if proc.returncode not in (0, 1):
                status = f"pytest_rc_{proc.returncode}"
        except subprocess.TimeoutExpired as exc:
            status = "pytest_timeout"
            stdout = (exc.stdout or b"").decode("utf-8", "replace") \
                if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = f"TIMEOUT after {timeout}s"
        (out_dir / "pytest.txt").write_text(f"{stdout}\n--- stderr ---\n{stderr}\n",
                                            encoding="utf-8")
        cases = aggregate_cases(_read_report(report))
        if not cases and status == "ok":
            status = "pytest_no_report"
        (out_dir / "cases.json").write_text(json.dumps(cases), encoding="utf-8")
        (out_dir / "status.json").write_text(json.dumps({"status": status}), encoding="utf-8")
        meta = _read_json(out_dir / "meta.json", {})
        return {"status": status, "cases": cases, "meta": meta,
                "pairs": _read_json(out_dir / "pairs.json", []),
                "group": _read_json(out_dir / "group.json", None)}
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def run_bandit(solution: Path, timeout: int = 300) -> dict:
    cmd = [venv_python(), "-m", "bandit", "-f", "json", "-q", str(solution)]
    try:
        proc = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout)
        data = json.loads(proc.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return {"total": 0, "high": 0, "medium": 0, "low": 0, "findings": [], "raw": None,
                "status": "bandit_failed"}
    counts = {"total": 0, "high": 0, "medium": 0, "low": 0}
    findings = []
    for issue in data.get("results", []):
        sev = issue.get("issue_severity", "").lower()
        counts["total"] += 1
        if sev in counts:
            counts[sev] += 1
        findings.append({"test_id": issue.get("test_id"), "severity": sev,
                         "confidence": issue.get("issue_confidence", "").lower(),
                         "line": issue.get("line_number"), "text": issue.get("issue_text")})
    return dict(counts, findings=findings, raw=data, status="ok")


def evaluate_run(solution: Path, run_id: str, out_root: Path, *, datasets=DATASETS,
                 seeds=DATA_SEEDS, timeout: int = 900, python: str | None = None,
                 progress=print) -> dict:
    """All fits for one implementation. Returns a record for runs.jsonl plus the
    per-fit detail (written to out_root/<run_id>/ by the caller's collector)."""
    run_dir = out_root / run_id
    fits = []
    for seed in seeds:
        for dataset in datasets:
            out_dir = run_dir / f"{dataset}_s{seed}"
            result = run_suite(solution, run_id, dataset, seed, out_dir,
                               timeout=timeout, python=python)
            passed = sum(1 for c in result["cases"] if c["status"] == "passed")
            progress(f"  {run_id} {dataset} seed {seed}: {result['status']}  "
                     f"{passed}/{len(result['cases'])} passed")
            fits.append({"dataset": dataset, "data_seed": seed, **result})
    source = Path(solution).read_text(encoding="utf-8", errors="replace")
    bandit = run_bandit(solution)
    (run_dir / "bandit.json").write_text(json.dumps(bandit), encoding="utf-8")
    flags = harness.source_flags(source)
    (run_dir / "source_flags.json").write_text(json.dumps(flags), encoding="utf-8")
    return {"fits": fits, "bandit": bandit, "source_flags": flags,
            "solution_sha256": sha256_file(solution), "harness_sha256": harness_hash()}
