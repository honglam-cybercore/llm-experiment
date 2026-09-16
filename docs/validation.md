# Isolation validation record

The generation phase is only valid if each run really was a throwaway,
memory-less session that could not see the tests, the other runs, or any
user-level instruction. This file records the evidence, per provider, and what
probing changed. Re-run the probes and add a dated block whenever a CLI is
upgraded.

Machine: Windows 11, Python 3.13.3, `C:\Users\Hong\Documents\1. Dev\llm-experiment`.

---

## Lane `main` - Claude Code

**CLI**: `claude` 2.1.263 · **model**: `claude-haiku-4-5` · **flags**:
`-p <prompt> --model M --output-format json --allowed-tools "" --strict-mcp-config`

### Evidence from the 156 completed runs

Not a probe - this is the recorded `cli_meta` of every run that produced a
scored program, read back from `results/runs.jsonl`:

| Property | Evidence | Result |
| --- | --- | --- |
| tools really disabled | `num_turns` over all 156 gen records | `{1: 156}` - every run answered in one turn, so no run took a tool step |
| nothing written to cwd | `cwd_residue` non-empty count | 0 of 156 |
| sessions really separate | distinct `session_id` | 156 distinct ids across 156 runs |
| prompts really frozen | distinct `prompt_sha256` | exactly 52 - one per task-condition, shared by that condition's three replicates, matching `prompts.md` |

This is the evidence the 156 scored runs actually rest on, and it is stronger
than a probe: it is measured on the runs themselves rather than on four
stand-ins.

### Live probes - attempted 2026-09-16, INCONCLUSIVE

Every probe came back as
`Failed to authenticate: OAuth session expired and could not be refreshed`.
No verdict from that attempt means anything, and the run has to be repeated
after a `/login`.

**Why the OAuth session keeps expiring mid-batch**: each run gets a fresh
`CLAUDE_CONFIG_DIR` seeded with a copy of the credentials. When the CLI
refreshes the token it writes the new one into that throwaway directory, which
`run.py` then deletes, so a rotated refresh token never reaches the real
`~/.claude`. The next run presents a spent token. Re-login and the batch
resumes; `gen` skips completed runs.

---

## Lane `codex` - Codex CLI

**CLI**: `codex-cli` 0.154.0 · **model**: `gpt-5.6-luna` ·
**reasoning effort**: `medium` · **probed**: 2026-09-16, all four PASS

Not on `PATH` on this machine. Pass it explicitly:

```
--cli-bin "C:\Users\Hong\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe"
```

**Flags**, all confirmed present in `codex exec --help` for this build:

```
codex exec --model gpt-5.6-luna --json \
  --sandbox read-only --skip-git-repo-check --ephemeral \
  --ignore-user-config --ignore-rules \
  -c model_reasoning_effort=medium \
  --output-last-message <tempfile> <prompt>
```

| Flag | Why |
| --- | --- |
| `--sandbox read-only` | the model may not write files or reach the network |
| `--skip-git-repo-check` | every run gets an empty temp cwd, never a git repo |
| `--ephemeral` | no session file is persisted, so no run can be resumed or read by the next |
| `--ignore-user-config` | `$CODEX_HOME/config.toml` is not loaded at all; auth still comes from `CODEX_HOME` |
| `--ignore-rules` | no user or project execpolicy `.rules` file is loaded |
| `-c model_reasoning_effort=` | no dedicated flag exists; see "Reasoning effort" below |
| `--output-last-message` | the final agent message is written to a file outside the run's cwd; reading the program from it is version-proof, scraping it out of the JSONL stream is not |

### Live probes - `run.py doctor --live --provider codex`, 2026-09-16

| Probe | Verdict | Evidence |
| --- | --- | --- |
| tools are blocked | **PASS** | cwd empty after the canary prompt; reply "I couldn't create the file because the workspace is read-only" |
| no user instructions or memory | **PASS** | reply `NONE`; copied config was `.sandbox`, `.sandbox_migration`, `.tmp`, `auth.json`, `installation_id`, `models_cache.json`, `thread-writer-locks`, `version.json` - auth and machinery only |
| sessions are separate | **PASS** | `01a0aa31-1c5a-...` vs `01a0aa31-57b5-...` |
| no memory across sessions | **PASS** | the word planted in call 1 was not recalled in call 2 |

### Model

`gpt-5-codex` is **refused** on this account:

```
400 invalid_request_error: The 'gpt-5-codex' model is not supported when using
Codex with a ChatGPT account.
```

The five selectable models in this build (`~/.codex/models_cache.json`) are
`gpt-6-astra`, `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna` and `gpt-5.5`.

**`gpt-5.6-luna` is the lane's frozen model**, chosen for tier parity: Codex
describes it as its "fast and affordable agentic coding model", which is the
same position `claude-haiku-4-5` holds in the main lane. `gpt-6-astra` is the
flagship; running it against Haiku would have measured the product tier rather
than the prompt condition.

Always pass `--model` explicitly - the CLI's own default can move between
releases, and the id has to appear in `runs.jsonl` for the lane to be
auditable.

### Reasoning effort

A second dial, independent of the model, and it moves output as much as a model
change does. Measured on this machine, same model and same prompt:

| effort | `reasoning_output_tokens` |
| --- | --- |
| `low` | 0 |
| `max` | 36 |

`codex exec` has no dedicated flag, so it goes through `-c
model_reasoning_effort=<value>`. It is **pinned to `medium`** for this lane and
recorded per run as `reasoning_effort` in `runs.jsonl`, for the same reason the
model id is pinned: `gpt-6-astra` defaults to `low`, defaults differ per model,
and a default can move between releases.

`turn.completed` carries a `usage` block including `reasoning_output_tokens`,
which `run.py` stores under `cli_meta.usage`, so the effort actually spent is
auditable after the fact.

---

## What probing changed

Four things, all found by running the probes rather than by reading docs.

### 1. `skills`, `plugins` and `packages` were being copied into the codex config

The first codex probe copied them out of `~/.codex` into the throwaway config
dir. They are user-installed extensions - the codex equivalent of
`~/.claude/skills` - and can carry instructions. Added to
`CODEX_CONFIG_EXCLUDE`; the probe was re-run to confirm the copied list is auth
and machinery only.

### 2. `~/.codex` history hides in numbered sqlite files

`goals_N.sqlite` and `logs_N.sqlite` (with `-shm`/`-wal` siblings) are
conversation history under another name, and an exact-name exclusion set cannot
match a numbered file. `CODEX_CONFIG_EXCLUDE_SUFFIXES` excludes them by suffix.

### 3. The memory probe was measuring the wrong thing

Original wording: *"Do you have any user-level or project-level instructions, a
CLAUDE.md or AGENTS.md, or saved memory in your context right now?"*

`gpt-5.6-luna` answered **yes**, quoting `"You are Codex"` - the CLI's own
product system prompt. `gpt-6-astra` answered **NONE** to the identical prompt
under identical flags. The old wording therefore measured how a model reads the
word "instructions", not whether the user's configuration leaked.

The wording now names the product prompt as out of scope and asks only about
user-owned configuration. Both wordings and both results are recorded here
rather than quietly replaced, because "rewrite the probe until it passes" is
the exact failure this file exists to prevent. The property that changed hands
is disclosure, not scoring: the copied-config list is unchanged, and it is the
harder evidence.

**What this cannot test, and what is therefore disclosed instead**: each CLI
wraps the prompt in its own product system prompt. Claude Code's and Codex's
differ, neither can be removed, and both are present in every run of their
lane. See "What is NOT controlled across lanes" in the README.

### 4. `doctor --live` could report PASS on a CLI that never answered

The claude probe attempt above returned an auth error for all four calls, and
the doctor scored three of them **PASS**: no canary file is written when
nothing runs, and two session ids differ because ids are minted before the
request is authenticated.

A green doctor on a dead CLI is worse than a red one. The first probe is now
also the liveness check: if the CLI itself fails - non-zero return code, an
error in the envelope, or output the parser cannot read - the doctor reports
one FAIL saying no verdict is meaningful, and skips the remaining probes
instead of scoring them.

### And one thing worth remembering when reading a probe

In one run `gpt-5.6-luna` replied **`DONE`** to the canary prompt - claiming it
had written the file - while the cwd stayed empty. The verdict is taken from
`cwd_residue`, not from what the model says, so the check was still correct.
Never soften that: the reply is not evidence.
