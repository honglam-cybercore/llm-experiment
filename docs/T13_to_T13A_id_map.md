# T13 -> T13A id map

The handover `Task_13A_13B_Fairness_AI_Implementation_Specification.md` renames
the original Task 13 to **Task 13A**. Only the label and the test-id prefix
change. Nothing about the task, its prompts, its profiles or its results does.

## What was renamed, and what deliberately was not

| Thing | Before | After | Why |
| --- | --- | --- | --- |
| Test case ids (docstring of `tests/T13.py`) | `T13-C01` ... `T13-S08` | `T13A-C01` ... `T13A-S08` | the label the thesis uses |
| Task display name (`tasks.yaml`) | Registered Nurse Candidate Suitability Scoring | Task 13A - Registered Nurse Candidate Suitability Scoring | the label the thesis uses |
| **Task id on disk** | `T13` | `T13` (unchanged) | run ids, output files, logs and `runs.jsonl` records are evidence; rewriting them would change the historical results the handover says to preserve |
| Run ids | `T13_C1_r1` ... `T13_C4_r3` | unchanged | same |
| Test function names (`test_C01_...`) | unchanged | unchanged | `run.py` buckets results by them |
| Prompts C1-C4 | verbatim | verbatim | sha256 of all four re-checked against the new handover: identical |
| `tests/T13.py` logic | - | no code line changed | only docstring lines were touched |

`T13A` is accepted as a selector everywhere: `run.py eval T13A`, `run.py gen
T13A_C2 --dry-run` and so on resolve to the `T13` runs.

## Case id mapping

The case ids map one to one by prefix. The per-case outcomes were not touched.

| Old | New | Dimension |
| --- | --- | --- |
| `T13-C01` ... `T13-C14` | `T13A-C01` ... `T13A-C14` | correctness (16 executed cases; C11 expands to three) |
| `T13-R01` ... `T13-R16` | `T13A-R01` ... `T13A-R16` | robustness (64 cases) |
| `T13-F01` ... `T13-F20` | `T13A-F01` ... `T13A-F20` | gender pairs (20) |
| `T13-I01` ... `T13-I03` | `T13A-I01` ... `T13A-I03` | additional invariance (3) |
| `T13-S01` ... `T13-S08` | `T13A-S01` ... `T13A-S08` | security (S01-S03, S07 automated; S04-S06 manual; S08 Bandit) |

## Differences between the handover and what was run (recorded, not hidden)

| Handover says | What this repository did | Where recorded |
| --- | --- | --- |
| five independent C1 generations per model | 4 conditions x 3 replicates = 12 runs per lane, kept as-is | `tasks.yaml` T13 `frozen_decisions.replicates` |
| ten-second per-case limit | none per case; the harness cap is `run.py eval --timeout` (300 s default), recorded as `pytest_timeout` | `tests/T13.py` header |
| I01 changes TEST_001 to TEST_002 | that pair is checked first, then nine more ids of different length, case, alphabet and punctuation, because a same-shape pair cannot reveal a score that depends on id length | `tests/T13.py` I01 docstring |
| S07 takes `"True"`, `1`, `None` | those, plus `"true"`, `"yes"`, `1.0` | `tests/T13.py` S07 |

Run `run.py report` to see the imported 13A results exactly as stored; the
evaluation was not repeated.
