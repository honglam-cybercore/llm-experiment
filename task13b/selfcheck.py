"""Run the evaluator self-tests (E01-E22).

    .venv13b\\Scripts\\python.exe -m task13b.selfcheck

A failure here blocks model comparison: it means the data or the harness is
wrong, not that a program is. Fix the defect, re-freeze the hashes, and re-run
every affected implementation under the identical revised tests; never edit a
candidate program to make a test pass.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    cmd = [sys.executable, "-m", "pytest", str(HERE / "evaluator_tests"), "-q",
           "-p", "no:cacheprovider"] + sys.argv[1:]
    return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(main())
