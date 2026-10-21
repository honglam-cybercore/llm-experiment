"""Plan step 0.6 for Task 13B: prove the suite is green on a correct program and
red on broken ones.

    .venv13b\\Scripts\\python.exe -m task13b.selfvalidate [--only NAME ...]

The reference (tests/_reference/T13B_reference.py) must pass every case. Each
single-rule mutant (tests/_reference/t13b_mutants.py) must fail the cases it is
meant to break, and may fail only cases whose id starts with an allowed prefix.
tests/_reference is git-ignored: none of this is ever shown to a model.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
import tempfile
from pathlib import Path

from . import evaluate

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "tests" / "_reference"


def _load_mutants():
    spec = importlib.util.spec_from_file_location("t13b_mutants", REF / "t13b_mutants.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.MUTANTS


def _failed(result) -> set[str]:
    return {c["case_id"] for c in result["cases"] if c["status"] != "passed"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*")
    parser.add_argument("--seed", type=int, default=13)
    args = parser.parse_args(argv)
    source = (REF / "T13B_reference.py").read_text(encoding="utf-8")
    mutants = _load_mutants()
    work = Path(tempfile.mkdtemp(prefix="t13b_selfvalidate_"))
    problems = 0

    print("reference:")
    for dataset in ("D0", "D3"):
        ref_path = work / "reference.py"
        ref_path.write_text(source, encoding="utf-8")
        result = evaluate.run_suite(ref_path, "REF", dataset, args.seed,
                                    work / f"ref_{dataset}")
        failed = _failed(result)
        total = len(result["cases"])
        ok = result["status"] == "ok" and not failed and total > 1000
        print(f"  {dataset}: {total - len(failed)}/{total} passed"
              + ("" if ok else f"  FAILED {sorted(failed)[:10]} status={result['status']}"))
        problems += 0 if ok else 1

    print("mutants:")
    for name, spec in mutants.items():
        if args.only and name not in args.only:
            continue
        text = source
        for old, new in spec["patch"]:
            if old not in text:
                print(f"  {name}: PATCH DOES NOT APPLY ({old[:50]!r})")
                problems += 1
                break
            text = text.replace(old, new)
        else:
            path = work / f"{name}.py"
            path.write_text(text, encoding="utf-8")
            dataset = spec.get("needs_dataset", "D1")
            result = evaluate.run_suite(path, name, dataset, args.seed, work / name)
            failed = _failed(result)
            missing = [e for e in spec["expect"] if e not in failed]
            stray = sorted(f for f in failed if f not in spec["expect"]
                           and not any(f.startswith(p) for p in spec["allowed"]))
            status = "ok" if not missing and not stray and failed else "PROBLEM"
            print(f"  {name:30s} {status:8s} failed {len(failed):4d}"
                  + (f"  survived (should fail): {missing}" if missing else "")
                  + (f"  unexpected: {stray[:8]}" if stray else "")
                  + ("  killed nothing" if not failed else ""))
            problems += 0 if status == "ok" else 1
    print("OK: every mutant killed, reference green" if not problems
          else f"{problems} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
