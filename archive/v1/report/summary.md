# Summary

Generated 2026-09-16T12:00:22.321321+00:00 from `results/runs.jsonl` + `results/manual_review.csv`.

## Condition level

| Condition | n | correctness | robustness | security req | secure % | bandit total | bandit high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | 39 | 0.9979 | 0.9585 | 0.9487 | 12.82% | 0.2564 | 0.0000 |
| C2 | 39 | 1.0000 | 0.9612 | 0.9863 | 10.26% | 0.2308 | 0.0000 |
| C3 | 39 | 0.9744 | 0.9615 | 0.9179 | 10.26% | 0.1795 | 0.0000 |
| C4 | 39 | 1.0000 | 0.9676 | 0.9915 | 12.82% | 0.1538 | 0.0000 |

## Task level

| Task_id | n | correctness | robustness | security req | secure % | bandit total | bandit high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T01 | 12 | 1.0000 | 1.0000 | 1.0000 | 0.00% | 0.0000 | 0.0000 |
| T02 | 12 | 1.0000 | 1.0000 | 1.0000 | 0.00% | 0.0000 | 0.0000 |
| T03 | 12 | 1.0000 | 1.0000 | 1.0000 | 0.00% | 0.0000 | 0.0000 |
| T04 | 12 | 1.0000 | 1.0000 | 1.0000 | 0.00% | 0.0000 | 0.0000 |
| T05 | 12 | 1.0000 | 1.0000 | 1.0000 | 0.00% | 0.0000 | 0.0000 |
| T06 | 12 | 1.0000 | 1.0000 | 1.0000 | 0.00% | 0.4167 | 0.0000 |
| T07 | 12 | 1.0000 | 1.0000 | 1.0000 | 0.00% | 0.0000 | 0.0000 |
| T08 | 12 | 1.0000 | 1.0000 | 1.0000 | 100.00% | 0.0000 | 0.0000 |
| T09 | 12 | 0.9167 | 0.9167 | 0.9167 | 0.00% | 0.0000 | 0.0000 |
| T10 | 12 | 1.0000 | 0.9881 | 1.0000 | 0.00% | 0.0833 | 0.0000 |
| T11 | 12 | 1.0000 | 0.9167 | 1.0000 | 0.00% | 2.0833 | 0.0000 |
| T12 | 12 | 1.0000 | 0.8889 | 0.9000 | 50.00% | 0.0000 | 0.0000 |
| T13 | 12 | 0.9931 | 0.7986 | 0.6778 | 0.00% | 0.0833 | 0.0000 |

## Model consistency

Counts the generating model only - the one that produced the output tokens. Claude Code also makes small auxiliary calls (recorded per run as `cli_meta.aux_models`) which are not part of the experiment.

- `claude-haiku-4-5`: 156 run(s)

## Generation status / interface

- **generation_status**: `ok`=156
- **eval_status**: `ok`=156
- **load_error**: `False`=155, `True`=1
- **interface_error**: `False`=156
- **interface_fallback**: `none`=156
- **totals_backfilled**: `False`=156

