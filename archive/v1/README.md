# v1 - the first task set (archived)

Frozen on 2026-09-17, when `12_Coding_Tasks_Experiment_Specification.md`
replaced all twelve tasks with a different set. Nothing here was deleted, and
nothing here is evidence for the current experiment: these runs answer task
definitions that no longer exist.

| | |
| --- | --- |
| `outputs/` | 156 generated programs, main lane (`claude-haiku-4-5`) |
| `outputs/codex/` | 156 generated programs, codex lane (`gpt-5.6-luna`, effort medium) |
| `results/` | `runs.jsonl` and per-run logs, both lanes |
| `report/` | `results.csv` and `summary.md`, main lane |
| `tasks.yaml`, `prompts.md` | the 52 prompts these runs were generated from |
| `tests/` | the suites these runs were scored against |

The v1 task set: User Registration Validator, Login Attempt Manager, Token
Generator, Password Hashing, Session Manager, OTP Validator, API Key Manager,
Rate Limiter, Data Encryption, Temporary Code Generator, Arithmetic Expression
Evaluator, Order Status Transitions, and (added later) Secure URL Validator.

Only the last survives into v2, as Task 5.

The scoring logic has not changed, so `report/results.csv` still reads
correctly. To re-score anything, point `run.py` at a copy of this folder.
