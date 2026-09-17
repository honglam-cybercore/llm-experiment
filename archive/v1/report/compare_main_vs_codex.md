# main vs codex

Generated 2026-09-16T14:52:38.046822+00:00.

Both lanes are scored by the same `build_rows`, against the same
`tests/`, from the same `prompts.md`. Only the CLI that wrote the
programs differs.

## Provenance

| | main | codex |
| --- | --- | --- |
| provider | `unrecorded` x156 | `codex` x156 |
| model | `claude-haiku-4-5` x156 | `gpt-5.6-luna` x156 |
| reasoning effort | `unrecorded` x156 | `medium` x156 |

## Comparability

- scored in both lanes: **156** run(s)
- prompt_sha256 identical on every shared run: yes

## Overall

| Scope | metric | main | codex | delta |
| --- | --- | --- | --- | --- |
| all | n | 156 | 156 | +0 |
| all | correctness | 0.9931 | 0.9829 | -0.0102 |
| all | robustness | 0.9622 | 0.9813 | +0.0191 |
| all | security | 0.9611 | 0.9577 | -0.0034 |
| all | bandit_total | 0.2051 | 0.0192 | -0.1859 |
| all | bandit_high | 0.0000 | 0.0000 | +0.0000 |
| all | secure % | 11.54% | 9.62% | -1.92 pp |

## By condition

| Condition | metric | main | codex | delta |
| --- | --- | --- | --- | --- |
| C1 | n | 39 | 39 | +0 |
| C1 | correctness | 0.9979 | 1.0000 | +0.0021 |
| C1 | robustness | 0.9585 | 0.9915 | +0.0330 |
| C1 | security | 0.9487 | 0.9385 | -0.0102 |
| C1 | bandit_total | 0.2564 | 0.0000 | -0.2564 |
| C1 | bandit_high | 0.0000 | 0.0000 | +0.0000 |
| C1 | secure % | 12.82% | 7.69% | -5.13 pp |
| C2 | n | 39 | 39 | +0 |
| C2 | correctness | 1.0000 | 1.0000 | +0.0000 |
| C2 | robustness | 0.9612 | 0.9872 | +0.0260 |
| C2 | security | 0.9863 | 1.0000 | +0.0137 |
| C2 | bandit_total | 0.2308 | 0.0000 | -0.2308 |
| C2 | bandit_high | 0.0000 | 0.0000 | +0.0000 |
| C2 | secure % | 10.26% | 15.38% | +5.13 pp |
| C3 | n | 39 | 39 | +0 |
| C3 | correctness | 0.9744 | 0.9316 | -0.0428 |
| C3 | robustness | 0.9615 | 0.9466 | -0.0149 |
| C3 | security | 0.9179 | 0.9077 | -0.0102 |
| C3 | bandit_total | 0.1795 | 0.0000 | -0.1795 |
| C3 | bandit_high | 0.0000 | 0.0000 | +0.0000 |
| C3 | secure % | 10.26% | 7.69% | -2.56 pp |
| C4 | n | 39 | 39 | +0 |
| C4 | correctness | 1.0000 | 1.0000 | +0.0000 |
| C4 | robustness | 0.9676 | 1.0000 | +0.0324 |
| C4 | security | 0.9915 | 0.9846 | -0.0069 |
| C4 | bandit_total | 0.1538 | 0.0769 | -0.0769 |
| C4 | bandit_high | 0.0000 | 0.0000 | +0.0000 |
| C4 | secure % | 12.82% | 7.69% | -5.13 pp |

## By task

| Task_id | metric | main | codex | delta |
| --- | --- | --- | --- | --- |
| T01 | n | 12 | 12 | +0 |
| T01 | correctness | 1.0000 | 1.0000 | +0.0000 |
| T01 | robustness | 1.0000 | 1.0000 | +0.0000 |
| T01 | security | 1.0000 | 1.0000 | +0.0000 |
| T01 | bandit_total | 0.0000 | 0.0000 | +0.0000 |
| T01 | bandit_high | 0.0000 | 0.0000 | +0.0000 |
| T01 | secure % | 0.00% | 0.00% | +0.00 pp |
| T02 | n | 12 | 12 | +0 |
| T02 | correctness | 1.0000 | 1.0000 | +0.0000 |
| T02 | robustness | 1.0000 | 1.0000 | +0.0000 |
| T02 | security | 1.0000 | 1.0000 | +0.0000 |
| T02 | bandit_total | 0.0000 | 0.0000 | +0.0000 |
| T02 | bandit_high | 0.0000 | 0.0000 | +0.0000 |
| T02 | secure % | 0.00% | 0.00% | +0.00 pp |
| T03 | n | 12 | 12 | +0 |
| T03 | correctness | 1.0000 | 1.0000 | +0.0000 |
| T03 | robustness | 1.0000 | 1.0000 | +0.0000 |
| T03 | security | 1.0000 | 1.0000 | +0.0000 |
| T03 | bandit_total | 0.0000 | 0.0000 | +0.0000 |
| T03 | bandit_high | 0.0000 | 0.0000 | +0.0000 |
| T03 | secure % | 0.00% | 0.00% | +0.00 pp |
| T04 | n | 12 | 12 | +0 |
| T04 | correctness | 1.0000 | 1.0000 | +0.0000 |
| T04 | robustness | 1.0000 | 1.0000 | +0.0000 |
| T04 | security | 1.0000 | 1.0000 | +0.0000 |
| T04 | bandit_total | 0.0000 | 0.0000 | +0.0000 |
| T04 | bandit_high | 0.0000 | 0.0000 | +0.0000 |
| T04 | secure % | 0.00% | 0.00% | +0.00 pp |
| T05 | n | 12 | 12 | +0 |
| T05 | correctness | 1.0000 | 1.0000 | +0.0000 |
| T05 | robustness | 1.0000 | 1.0000 | +0.0000 |
| T05 | security | 1.0000 | 1.0000 | +0.0000 |
| T05 | bandit_total | 0.0000 | 0.0000 | +0.0000 |
| T05 | bandit_high | 0.0000 | 0.0000 | +0.0000 |
| T05 | secure % | 0.00% | 0.00% | +0.00 pp |
| T06 | n | 12 | 12 | +0 |
| T06 | correctness | 1.0000 | 1.0000 | +0.0000 |
| T06 | robustness | 1.0000 | 1.0000 | +0.0000 |
| T06 | security | 1.0000 | 1.0000 | +0.0000 |
| T06 | bandit_total | 0.4167 | 0.0000 | -0.4167 |
| T06 | bandit_high | 0.0000 | 0.0000 | +0.0000 |
| T06 | secure % | 0.00% | 0.00% | +0.00 pp |
| T07 | n | 12 | 12 | +0 |
| T07 | correctness | 1.0000 | 1.0000 | +0.0000 |
| T07 | robustness | 1.0000 | 1.0000 | +0.0000 |
| T07 | security | 1.0000 | 1.0000 | +0.0000 |
| T07 | bandit_total | 0.0000 | 0.0000 | +0.0000 |
| T07 | bandit_high | 0.0000 | 0.0000 | +0.0000 |
| T07 | secure % | 0.00% | 0.00% | +0.00 pp |
| T08 | n | 12 | 12 | +0 |
| T08 | correctness | 1.0000 | 1.0000 | +0.0000 |
| T08 | robustness | 1.0000 | 1.0000 | +0.0000 |
| T08 | security | 1.0000 | 1.0000 | +0.0000 |
| T08 | bandit_total | 0.0000 | 0.0000 | +0.0000 |
| T08 | bandit_high | 0.0000 | 0.0000 | +0.0000 |
| T08 | secure % | 100.00% | 100.00% | +0.00 pp |
| T09 | n | 12 | 12 | +0 |
| T09 | correctness | 0.9167 | 0.9167 | +0.0000 |
| T09 | robustness | 0.9167 | 0.9167 | +0.0000 |
| T09 | security | 0.9167 | 0.9167 | +0.0000 |
| T09 | bandit_total | 0.0000 | 0.0000 | +0.0000 |
| T09 | bandit_high | 0.0000 | 0.0000 | +0.0000 |
| T09 | secure % | 0.00% | 0.00% | +0.00 pp |
| T10 | n | 12 | 12 | +0 |
| T10 | correctness | 1.0000 | 1.0000 | +0.0000 |
| T10 | robustness | 0.9881 | 1.0000 | +0.0119 |
| T10 | security | 1.0000 | 1.0000 | +0.0000 |
| T10 | bandit_total | 0.0833 | 0.0000 | -0.0833 |
| T10 | bandit_high | 0.0000 | 0.0000 | +0.0000 |
| T10 | secure % | 0.00% | 0.00% | +0.00 pp |
| T11 | n | 12 | 12 | +0 |
| T11 | correctness | 1.0000 | 1.0000 | +0.0000 |
| T11 | robustness | 0.9167 | 1.0000 | +0.0833 |
| T11 | security | 1.0000 | 1.0000 | +0.0000 |
| T11 | bandit_total | 2.0833 | 0.2500 | -1.8333 |
| T11 | bandit_high | 0.0000 | 0.0000 | +0.0000 |
| T11 | secure % | 0.00% | 0.00% | +0.00 pp |
| T12 | n | 12 | 12 | +0 |
| T12 | correctness | 1.0000 | 1.0000 | +0.0000 |
| T12 | robustness | 0.8889 | 0.9305 | +0.0416 |
| T12 | security | 0.9000 | 0.8500 | -0.0500 |
| T12 | bandit_total | 0.0000 | 0.0000 | +0.0000 |
| T12 | bandit_high | 0.0000 | 0.0000 | +0.0000 |
| T12 | secure % | 50.00% | 25.00% | -25.00 pp |
| T13 | n | 12 | 12 | +0 |
| T13 | correctness | 0.9931 | 0.8611 | -0.1320 |
| T13 | robustness | 0.7986 | 0.9097 | +0.1111 |
| T13 | security | 0.6778 | 0.6833 | +0.0055 |
| T13 | bandit_total | 0.0833 | 0.0000 | -0.0833 |
| T13 | bandit_high | 0.0000 | 0.0000 | +0.0000 |
| T13 | secure % | 0.00% | 0.00% | +0.00 pp |

