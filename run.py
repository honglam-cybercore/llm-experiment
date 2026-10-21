#!/usr/bin/env python3
"""Single CLI for the LLM code-generation experiment.

    python run.py prompt T01 C1      print one assembled prompt + its sha256
    python run.py build              (re)generate prompts.md, 48 frozen prompts
    python run.py gen [run_id ...]   generate code, one throwaway session per run
    python run.py eval [run_id ...]  pytest + bandit each generated program
    python run.py report             results.csv + summary.md
    python run.py report --emit-manual   write results/manual_review.csv skeleton

gen and eval are re-entrant: an existing output is never regenerated and an
already-evaluated run is never re-run unless --force is given.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is missing. Activate .venv and pip install -r requirements.lock")

ROOT = Path(__file__).resolve().parent
TASKS_YAML = ROOT / "tasks.yaml"
REQUIREMENTS = ROOT / "requirements.lock"
REQ_PYTHON = ROOT / ".python-version"
PROMPTS_MD = ROOT / "prompts.md"
TESTS_DIR = ROOT / "tests"
OUTPUTS_DIR = ROOT / "outputs"
RESULTS_DIR = ROOT / "results"
LOGS_DIR = RESULTS_DIR / "logs"
RUNS_JSONL = RESULTS_DIR / "runs.jsonl"
MANUAL_CSV = RESULTS_DIR / "manual_review.csv"
REPORT_DIR = ROOT / "report"

# A "lane" is one provider's parallel universe: same prompts, same tests, same
# conftest, same scoring, separate artifacts. The default lane keeps the
# original layout byte-for-byte, so the runs completed before lanes existed are
# untouched and every path in the README still resolves.
DEFAULT_LANE = "main"
LANE = DEFAULT_LANE


def _apply_lane(lane: str) -> None:
    """Point every per-run artifact at this lane. Called once from main(),
    before any command runs. TASKS_YAML, PROMPTS_MD and TESTS_DIR are
    deliberately NOT lane-aware: holding them in common is what makes two
    lanes comparable at all."""
    global LANE, OUTPUTS_DIR, LOGS_DIR, RUNS_JSONL, MANUAL_CSV, REPORT_DIR
    LANE = lane
    if lane == DEFAULT_LANE:
        return
    OUTPUTS_DIR = ROOT / "outputs" / lane
    LOGS_DIR = RESULTS_DIR / lane / "logs"
    RUNS_JSONL = RESULTS_DIR / lane / "runs.jsonl"
    MANUAL_CSV = RESULTS_DIR / lane / "manual_review.csv"
    REPORT_DIR = ROOT / "report" / lane


def lane_paths(lane: str) -> dict:
    """The same mapping as a plain dict, for reading a lane you are not in
    (compare reads two lanes in one process)."""
    if lane == DEFAULT_LANE:
        return {"outputs": ROOT / "outputs", "logs": RESULTS_DIR / "logs",
                "runs": RESULTS_DIR / "runs.jsonl",
                "manual": RESULTS_DIR / "manual_review.csv",
                "report": ROOT / "report"}
    return {"outputs": ROOT / "outputs" / lane, "logs": RESULTS_DIR / lane / "logs",
            "runs": RESULTS_DIR / lane / "runs.jsonl",
            "manual": RESULTS_DIR / lane / "manual_review.csv",
            "report": ROOT / "report" / lane}

TASK_IDS = [f"T{i:02d}" for i in range(1, 14)]
CONDITIONS = ["C1", "C2", "C3", "C4"]
REPLICATES = [1, 2, 3]

# T13B (the ML-pipeline fairness task) is kept OUT of TASK_IDS on purpose. Every
# T01-T13 command (report, compare, the manual-review skeleton, the 156-run
# loops) keeps meaning exactly what it meant before; T13B is addressed by name
# (`run.py gen T13B`, `run.py eval T13B`) and scored by its own package, task13b.
TASK_B = "T13B"
# "T13A" is the thesis name of the original T13. The id stays T13 on disk so no
# historical run id, output file or runs.jsonl record is rewritten.
TASK_ALIASES = {"T13A": "T13"}

# Which parts of the prompt each condition carries. FROZEN.
CONDITION_PARTS = {
    "C1": ("requirement",),
    "C2": ("requirement", "context"),
    "C3": ("requirement", "security_guidance"),
    "C4": ("requirement", "context", "security_guidance"),
}

# Security checks that require human judgement (source / static inspection).
# Every other S-check is automated in tests/TXX.py. Bandit S-checks are not
# pass/fail: they are recorded in the bandit_* columns. FROZEN.
MANUAL_CHECKS = {
    "T01": ["S03", "S07"],
    "T02": ["S10"],
    "T03": ["S08"],
    "T04": ["S05"],
    "T05": ["S17", "S18"],
    "T06": ["S09"],
    "T07": ["S03", "S04"],
    "T08": ["S08"],
    "T09": ["S09", "S10"],
    "T10": ["S10"],
    "T11": ["S13", "S14"],
    "T12": ["S10", "S11", "S12"],
    "T13": ["S04", "S05", "S06"],
    # T13B: S01-S03 and S07 are automated; S10 is Bandit. See task13b/tests/test_security.py.
    "T13B": ["S04", "S05", "S06", "S08", "S09"],
}

SOLUTION_MODULE = "solution"  # every generated program is imported under this name

# Test-name buckets. C/R/S are shared by every task; F (gender pairs) and
# I (additional invariance) exist for T13 and read 0/0 everywhere else.
BUCKETS = "CRSFI"

# Flags passed to the Claude Code CLI to kill tools and MCP. Flag NAMES drift
# between CLI versions - verify with `claude --help` before Phase 1 and correct
# this list, or override per invocation with --isolation-flag.
ISOLATION_FLAGS = ["--allowed-tools", "", "--strict-mcp-config"]

# Every run gets a fresh CLAUDE_CONFIG_DIR so no user- or project-specific
# context reaches a supposedly isolated prompt. A completely empty one also
# strips the credentials, and the CLI answers "Not logged in", so the real
# config dir is copied EXCEPT for the entries below, which are the ones that
# carry context. Anything not listed (credentials, account state) is copied so
# authentication still works. Every copied name is recorded per run in
# runs.jsonl as config_copied, and doctor --live probes empirically that no
# memory leaks through.
CONFIG_EXCLUDE = {
    "CLAUDE.md", "CLAUDE.local.md", "memory",
    "settings.json", "settings.local.json",
    "projects", "history.jsonl", "todos", "shell-snapshots", "file-history",
    "commands", "agents", "skills", "plugins", "hooks", "output-styles",
    "mcp.json", "mcp_servers.json", ".mcp.json",
    "statsig", "logs", "ide", "downloads", "debug",
}

# Files that must be copied for authentication but can also carry conversation
# history or MCP wiring. These keys are stripped from the copy.
CONFIG_STRIP_KEYS = {"projects", "mcpServers", "history", "tipsHistory",
                     "pastedContents", "recentCommands"}
CONFIG_SANITIZE = {".claude.json", "config.json", "claude.json"}

# Codex equivalents, VERIFIED against codex-cli 0.154.0 with `codex exec
# --help` on the experiment machine. Each flag earns its place:
#
#   --sandbox read-only    the model may not write files or reach the network
#   --skip-git-repo-check  every run gets an empty temp cwd, never a git repo
#   --ephemeral            no session file is persisted, so nothing a run does
#                          can be resumed or read by the next one
#   --ignore-user-config   $CODEX_HOME/config.toml is not loaded at all; auth
#                          still comes from CODEX_HOME. This is the strongest
#                          single guarantee that no user-level setting reaches
#                          a supposedly isolated prompt
#   --ignore-rules         no user or project execpolicy .rules file is loaded
#
# Note what is NOT here: codex has no equivalent of `--allowed-tools ""`. The
# read-only sandbox stops the model changing anything, but shell tools still
# exist and it may still take several turns. See "What is NOT controlled
# across lanes" in the README - this is a real asymmetry with the claude lane,
# not an oversight.
CODEX_ISOLATION_FLAGS = [
    "--sandbox", "read-only",
    "--skip-git-repo-check",
    "--ephemeral",
    "--ignore-user-config",
    "--ignore-rules",
]

# What a fresh CODEX_HOME must NOT inherit. auth.json is what has to survive so
# the CLI stays logged in. The real ~/.codex also holds goals_N.sqlite and
# logs_N.sqlite (plus -shm/-wal siblings), which are conversation history under
# another name, so they are excluded by suffix rather than by exact name.
CODEX_CONFIG_EXCLUDE = {
    "config.toml", "config.json", "history.jsonl", "sessions", "prompts",
    "AGENTS.md", "log", "logs", "tmp", "cache", "archived_sessions",
    # User-installed extensions. The first live probe copied these in; they are
    # the codex equivalent of ~/.claude/skills and ~/.claude/plugins and can
    # carry instructions, so they are excluded even though --ignore-user-config
    # already blocks config.toml.
    "skills", "plugins", "packages", "hooks", "mcp", "mcp.json",
}
CODEX_CONFIG_EXCLUDE_SUFFIXES = {".sqlite", ".sqlite-shm", ".sqlite-wal", ".db"}


# --------------------------------------------------------------------------- #
# prompt assembly
# --------------------------------------------------------------------------- #

def load_tasks() -> dict:
    with TASKS_YAML.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def build_prompt(spec: dict, task_id: str, condition: str) -> str:
    common = spec["common"]
    task = spec["tasks"][task_id]
    # A task may carry its prompts verbatim instead of being assembled from
    # parts. T13 does: its handover supplies "exact generation prompts" whose
    # header, spacing and security paragraph differ from the shared ones, so
    # rebuilding them from pieces would drift from the document.
    if "verbatim_prompts" in task:
        return task["verbatim_prompts"][condition]
    labels = common["labels"]
    blocks = [common["header"].rstrip("\n")]
    for part in CONDITION_PARTS[condition]:
        body = task[part] if part != "security_guidance" else common["security_guidance"]
        blocks.append(f"{labels[part]}\n{body.rstrip()}")
    blocks.append(f"{labels['interface']}\n{task['interface'].rstrip()}")
    return "\n\n".join(blocks) + "\n"


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_run_id(run_id: str) -> tuple[str, str, int]:
    task_id, condition, rep = run_id.split("_")
    return task_id, condition, int(rep[1:])


def all_run_ids() -> list[str]:
    return [f"{t}_{c}_r{r}" for t in TASK_IDS for c in CONDITIONS for r in REPLICATES]


def b_run_ids() -> list[str]:
    return [f"{TASK_B}_{c}_r{r}" for c in CONDITIONS for r in REPLICATES]


def _normalise_selector(sel: str) -> str:
    for alias, real in TASK_ALIASES.items():
        if sel == alias or sel.startswith(alias + "_"):
            return real + sel[len(alias):]
    return sel


def resolve_run_ids(selectors: list[str]) -> list[str]:
    """Accept full run ids, or prefixes such as T01, T01_C2, C3. T13A means T13.
    T13B ids resolve only when named (T13B, T13B_C2, T13B_C2_r1); a bare
    condition such as C3, or no selector at all, still means T01-T13 only."""
    if not selectors:
        return all_run_ids()
    selectors = [_normalise_selector(s) for s in selectors]
    chosen: list[str] = []
    matched: set[str] = set()
    for rid in all_run_ids() + b_run_ids():
        task_id, condition, rep = parse_run_id(rid)
        is_b = task_id == TASK_B
        for sel in selectors:
            keys = (rid, task_id, f"{task_id}_{condition}") + (() if is_b else (condition,))
            if sel in keys:
                chosen.append(rid)
                matched.add(sel)
                break
    missing = [s for s in selectors if s not in matched]
    if missing:
        sys.exit(f"unknown selector(s): {', '.join(missing)}")
    return chosen


# --------------------------------------------------------------------------- #
# runs.jsonl
# --------------------------------------------------------------------------- #

def append_record(record: dict) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with RUNS_JSONL.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def read_records(path: Path | None = None) -> dict[str, dict[str, dict]]:
    """{run_id: {phase: record}} keeping the last record written per phase."""
    out: dict[str, dict[str, dict]] = {}
    path = path or RUNS_JSONL
    if not path.exists():
        return out
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            out.setdefault(rec["run_id"], {})[rec["phase"]] = rec
    return out


# --------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------- #

def cmd_prompt(args) -> None:
    spec = load_tasks()
    text = build_prompt(spec, args.task_id, args.condition)
    print(text, end="")
    print(f"\n----- sha256: {sha256(text)}", file=sys.stderr)


def cmd_build(args) -> None:
    spec = load_tasks()
    build_ids = TASK_IDS + [TASK_B]
    lines = [
        f"# Frozen prompts ({len(build_ids) * len(CONDITIONS)})",
        "",
        "Generated by `python run.py build` from `tasks.yaml`. Audit evidence:",
        "the sha256 recorded per prompt must match `prompt_sha256` in",
        "`results/runs.jsonl` for every run of that task-condition.",
        "",
        f"Built at {datetime.now(timezone.utc).isoformat()} from tasks.yaml"
        f" sha256 `{sha256(TASKS_YAML.read_text(encoding='utf-8'))}`.",
        "",
    ]
    for task_id in build_ids:
        lines.append(f"## {task_id} {spec['tasks'][task_id]['name']}")
        lines.append("")
        for condition in CONDITIONS:
            text = build_prompt(spec, task_id, condition)
            lines += [
                f"### {task_id} {condition}",
                "",
                f"sha256: `{sha256(text)}`",
                "",
                "```text",
                text.rstrip("\n"),
                "```",
                "",
            ]
    PROMPTS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {PROMPTS_MD.relative_to(ROOT)} ({len(build_ids) * len(CONDITIONS)} prompts)")


def strip_outer_fence(text: str) -> tuple[str, bool]:
    """Remove the outermost ``` fence lines, even when preceded by prose."""
    lines = text.split("\n")
    first = next((i for i, l in enumerate(lines)
                  if l.lstrip().startswith("```")), None)
    if first is None:
        return text, False
    last = next((i for i in range(len(lines) - 1, first, -1)
                 if lines[i].strip().startswith("```")), None)
    if last is None or last == first:
        return text, False
    return "\n".join(lines[first + 1:last]).strip("\n") + "\n", True


def classify_source(text: str, meta: dict | None = None) -> str:
    """`cli_error` is not an experiment result. A refused or failed CLI call
    (not logged in, rate limited, API error) produces an error message where the
    program should be; recording that as syntax_error would enter it into the
    dataset as if the model had written broken code."""
    if meta and (meta.get("is_error") or meta.get("subtype") not in (None, "success")):
        return "cli_error"
    if not text.strip():
        return "empty"
    try:
        ast.parse(text)
    except SyntaxError:
        return "syntax_error"
    return "ok"


def _resolve_cli_bin(name: str, spec: dict | None = None) -> str:
    """Windows ships these CLIs as .cmd shims or under Programs\\, and an
    installer does not always put them on PATH - codex does not, on this
    machine. Look on PATH first, then in the provider's known install
    locations, so a working install does not need --cli-bin."""
    if os.path.sep in name or (os.path.altsep and os.path.altsep in name):
        return name
    found = shutil.which(name)
    if found:
        return found
    for candidate in (spec or {}).get("bin_fallbacks", ()):
        path = Path(os.path.expandvars(str(candidate))).expanduser()
        if path.is_file():
            return str(path)
    tried = "\n  ".join(str(Path(os.path.expandvars(str(c))).expanduser())
                        for c in (spec or {}).get("bin_fallbacks", ()))
    sys.exit(f"cannot find the CLI {name!r} on PATH"
             + (f", nor at:\n  {tried}" if tried else "")
             + f"\nInstall it, or pass --cli-bin with the full path.")


def _real_config_dir(spec: dict) -> Path | None:
    raw = os.environ.get(spec["config_env"])
    candidate = Path(raw) if raw else Path.home() / spec["config_dirname"]
    return candidate if candidate.is_dir() else None


def _seed_config_dir(dest: str, spec: dict) -> list[str]:
    """Copy credentials and account state into a fresh config dir, leaving out
    everything that would carry context into the prompt. Any *.md is skipped
    whatever it is called, which covers CLAUDE.md and AGENTS.md alike."""
    src = _real_config_dir(spec)
    if src is None:
        return []
    copied = []
    for entry in src.iterdir():
        if entry.name in spec["config_exclude"] or entry.suffix.lower() == ".md":
            continue
        if any(entry.name.lower().endswith(s)
               for s in spec.get("config_exclude_suffixes", ())):
            continue
        target = Path(dest) / entry.name
        try:
            if entry.is_dir():
                shutil.copytree(entry, target, dirs_exist_ok=True)
            else:
                shutil.copy2(entry, target)
                if entry.name in CONFIG_SANITIZE:
                    _strip_context_keys(target)
        except OSError:
            continue
        copied.append(entry.name)
    return sorted(copied)


def _strip_context_keys(path: Path) -> None:
    """Remove conversation history and MCP wiring from a copied config file,
    keeping whatever the CLI needs to stay authenticated."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return
    if not isinstance(data, dict):
        return
    if not CONFIG_STRIP_KEYS & data.keys():
        return
    for key in CONFIG_STRIP_KEYS:
        data.pop(key, None)
    try:
        path.write_text(json.dumps(data), encoding="utf-8")
    except OSError:
        pass


def _extract_text(raw: str, output_format: str) -> tuple[str, dict]:
    """With --output-format json the CLI returns a metadata envelope."""
    if output_format != "json":
        return raw, {}
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw, {"cli_json_parse_failed": True}
    if isinstance(data, list):
        data = data[-1] if data else {}
    if not isinstance(data, dict):
        return raw, {"cli_json_parse_failed": True}
    meta = {k: data[k] for k in ("session_id", "duration_ms", "total_cost_usd",
                                 "num_turns", "is_error", "subtype", "uuid")
            if k in data}
    # `claude-opus-5` carries no date suffix, so the requested id does not pin a
    # build. Record whatever the envelope says was actually served.
    #
    # modelUsage lists auxiliary models too: Claude Code makes small internal
    # calls (a Haiku call of ~12 output tokens for housekeeping) alongside the
    # one that writes the program. The generating model is the one that produced
    # the output tokens, so pick by outputTokens and keep the rest as aux.
    usage = data.get("modelUsage")
    if isinstance(usage, dict) and usage:
        def _out(name):
            v = usage.get(name)
            return v.get("outputTokens", 0) if isinstance(v, dict) else 0
        ranked = sorted(usage, key=_out, reverse=True)
        meta["resolved_models"] = sorted(usage)
        meta["primary_model"] = ranked[0]
        meta["primary_output_tokens"] = _out(ranked[0])
        if len(ranked) > 1:
            meta["aux_models"] = {n: _out(n) for n in ranked[1:]}
    for key in ("model", "modelId"):
        if isinstance(data.get(key), str) and "primary_model" not in meta:
            meta["primary_model"] = data[key]
            meta.setdefault("resolved_models", [data[key]])
    text = data.get("result")
    return (text if isinstance(text, str) else raw), meta


def _codex_message(obj) -> str | None:
    """Pull an assistant message out of one codex --json event, across the
    shapes the CLI has used. Returns None when the event is not a message."""
    if not isinstance(obj, dict):
        return None
    item = obj.get("item") if isinstance(obj.get("item"), dict) else None
    msg = obj.get("msg") if isinstance(obj.get("msg"), dict) else None
    for holder in (item, msg, obj):
        if not isinstance(holder, dict):
            continue
        kind = str(holder.get("type") or holder.get("role") or "")
        if kind not in ("agent_message", "assistant_message", "assistant",
                        "message", "item.completed"):
            continue
        for key in ("text", "message", "content", "last_agent_message"):
            val = holder.get(key)
            if isinstance(val, str) and val.strip():
                return val
            if isinstance(val, list):                 # content blocks
                parts = [b.get("text") for b in val
                         if isinstance(b, dict) and isinstance(b.get("text"), str)]
                if parts:
                    return "".join(parts)
    return None


def _extract_codex(raw: str, output_format: str) -> tuple[str, dict]:
    """`codex exec --json` streams one JSON event per line. The event shape has
    changed between releases, so this walks every line, keeps the LAST thing
    that looks like an assistant message, and records whatever session and
    usage fields it recognises.

    When no line is recognisable the result is flagged as a CLI error rather
    than returned as text. A parser that does not understand its CLI must halt
    the batch: recording its confusion as a generated program would enter
    garbage into the dataset as if a model had written it.
    """
    if output_format != "json":
        return raw, {}
    meta: dict = {}
    text = None
    for line in raw.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        found = _codex_message(obj)
        if found is not None:
            text = found
        flat = obj if isinstance(obj, dict) else {}
        nested = flat.get("msg") if isinstance(flat.get("msg"), dict) else {}
        for source in (flat, nested):
            for key in ("session_id", "conversation_id", "thread_id"):
                if isinstance(source.get(key), str):
                    meta.setdefault("session_id", source[key])
            for key in ("model", "model_slug"):
                if isinstance(source.get(key), str):
                    meta.setdefault("primary_model", source[key])
            usage = source.get("usage") or source.get("token_usage")
            if isinstance(usage, dict):
                meta["usage"] = usage
            if source.get("type") in ("error", "stream_error", "turn.failed"):
                meta["is_error"] = True
                detail = source.get("message") or source.get("error")
                meta.setdefault("error_text", str(detail)[:300])
    if text is None:
        meta["is_error"] = True
        meta["cli_shape_unrecognised"] = True
        return raw, meta
    if "primary_model" in meta:
        meta.setdefault("resolved_models", [meta["primary_model"]])
    return text, meta


# One entry per code-generating CLI. Everything the experiment holds constant -
# the prompts, the tests, conftest, the scoring - is shared. Only the argv that
# asks a model for a program differs, and only what that argv produces is
# compared.
#
# `argv` returns everything after the executable, and the ORDER matters: Claude
# Code takes the prompt behind -p and tolerates trailing flags, while
# `codex exec` takes the prompt as its last positional argument, so flags have
# to come before it.
PROVIDERS = {
    "claude": {
        "bin": "claude",
        "default_model": "claude-haiku-4-5",
        "lane": DEFAULT_LANE,
        "config_env": "CLAUDE_CONFIG_DIR",
        "config_dirname": ".claude",
        "config_exclude": CONFIG_EXCLUDE,
        "isolation": ISOLATION_FLAGS,
        "bin_fallbacks": (
            "%LOCALAPPDATA%/Programs/claude/claude.exe",
            "~/.local/bin/claude.exe",
            "~/.local/bin/claude",
            "%APPDATA%/npm/claude.cmd",
        ),
        "extract": lambda raw, fmt: _extract_text(raw, fmt),
        "argv": lambda prompt, model, fmt, flags, extra: (
            ["-p", prompt, "--model", model, "--output-format", fmt]
            + list(flags) + list(extra)),
        "turns_key": "num_turns",
        "help_hint": "claude --help",
    },
    "codex": {
        "bin": "codex",
        # Chosen to sit in the same product tier as the main lane's
        # claude-haiku-4-5: GPT-5.6-Luna is Codex's "fast and affordable
        # agentic coding model", not its flagship. Comparing a small model
        # against a flagship would measure the tier, not the prompt condition.
        #
        # Verified on this account: `gpt-5-codex` is refused with "not supported
        # when using Codex with a ChatGPT account". Pass --model explicitly
        # rather than relying on the CLI default, so the id is recorded.
        "default_model": "gpt-5.6-luna",
        # Reasoning effort is a second, independent dial, and leaving it
        # unpinned is the same hazard as leaving the model id unpinned: the
        # CLI's default can move between releases. Measured on this machine,
        # same model and prompt: effort=low produced 0 reasoning tokens,
        # effort=max produced 36. It is passed as `-c <key>=<value>` because
        # `codex exec` has no dedicated flag for it, and recorded per run.
        "effort_config_key": "model_reasoning_effort",
        "default_effort": "medium",
        "lane": "codex",
        "config_env": "CODEX_HOME",
        "config_dirname": ".codex",
        "config_exclude": CODEX_CONFIG_EXCLUDE,
        "config_exclude_suffixes": CODEX_CONFIG_EXCLUDE_SUFFIXES,
        "isolation": CODEX_ISOLATION_FLAGS,
        # The installer does not add codex to PATH on this machine, so these
        # are searched before giving up and asking for --cli-bin.
        "bin_fallbacks": (
            "%LOCALAPPDATA%/Programs/OpenAI/Codex/bin/codex.exe",
            "~/.local/bin/codex.exe",
            "~/.local/bin/codex",
            "%APPDATA%/npm/codex.cmd",
        ),
        # `codex exec -o FILE` writes the final agent message to FILE. Reading
        # the program out of that file is version-proof; parsing it back out of
        # the JSONL event stream is not.
        "last_message_flag": "--output-last-message",
        "extract": lambda raw, fmt: _extract_codex(raw, fmt),
        "argv": lambda prompt, model, fmt, flags, extra: (
            ["exec", "--model", model] + (["--json"] if fmt == "json" else [])
            + list(flags) + list(extra) + [prompt]),
        "turns_key": None,
        "help_hint": "codex exec --help",
    },
}


def _invoke_cli(prompt: str, *, provider: str, cli_bin: str, model: str,
                output_format: str, isolation: list[str],
                extra: list[str] | None = None, effort: str | None = None,
                timeout: int = 600, seed_config: bool = True) -> dict:
    """One isolated, one-shot CLI session, whichever provider it is.

    cwd is a fresh empty directory (no CLAUDE.md, no AGENTS.md, no config dir,
    no git repo, no other run's output). The provider's config-dir environment
    variable points at a second fresh directory holding credentials and nothing
    that carries context, so user-level instructions, settings and history
    cannot reach the prompt. stdin is closed. Nothing is ever resumed.
    """
    spec = PROVIDERS[provider]
    extra = list(extra or [])
    effort = effort or spec.get("default_effort")
    if effort and spec.get("effort_config_key"):
        extra += ["-c", f"{spec['effort_config_key']}={effort}"]
    # The final-message file lives OUTSIDE the run's cwd on purpose: anything
    # inside it would show up in cwd_residue and look like the model wrote it.
    last_msg = None
    if spec.get("last_message_flag"):
        handle, last_msg = tempfile.mkstemp(prefix=f"{provider}_last_", suffix=".txt")
        os.close(handle)
        extra += [spec["last_message_flag"], last_msg]
    cmd = [cli_bin] + spec["argv"](prompt, model, output_format,
                                   list(isolation), extra)
    workdir = tempfile.mkdtemp(prefix=f"{provider}_run_")
    config_dir = tempfile.mkdtemp(prefix=f"{provider}_cfg_")
    config_copied = _seed_config_dir(config_dir, spec) if seed_config else []
    env = dict(os.environ, **{spec["config_env"]: config_dir})
    started = time.time()
    try:
        proc = subprocess.run(cmd, cwd=workdir, env=env, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout)
        raw, stderr, rc = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired:
        raw, stderr, rc = "", f"TIMEOUT after {timeout}s", -1
    except OSError as exc:
        raw, stderr, rc = "", f"{type(exc).__name__}: {exc}", -1
    try:
        residue = sorted(os.listdir(workdir))
    except OSError:
        residue = []
    shutil.rmtree(workdir, ignore_errors=True)
    shutil.rmtree(config_dir, ignore_errors=True)
    text, meta = spec["extract"](raw, output_format)
    if last_msg:
        try:
            final = Path(last_msg).read_text(encoding="utf-8", errors="replace")
        except OSError:
            final = ""
        Path(last_msg).unlink(missing_ok=True)
        if final.strip():
            # A written final message beats anything scraped from the stream,
            # and its presence also means the turn actually completed.
            text = final
            meta["text_source"] = "last_message_file"
            meta.pop("cli_shape_unrecognised", None)
            if not meta.get("error_text"):
                meta.pop("is_error", None)
    if effort:
        meta.setdefault("reasoning_effort", effort)
    return {"cmd": cmd, "provider": provider, "raw": raw, "text": text,
            "meta": meta, "rc": rc, "effort": effort,
            "stderr": stderr, "residue": residue, "config_copied": config_copied,
            "wall_seconds": round(time.time() - started, 2)}


def _assert_prompts_fresh() -> None:
    """prompts.md is the frozen audit record. Generating from a tasks.yaml that
    no longer matches it would make prompt_sha256 unverifiable."""
    if not PROMPTS_MD.exists():
        sys.exit("prompts.md is missing. Run `python run.py build` first.")
    import re
    recorded = re.search(r"tasks\.yaml\s*sha256 `([0-9a-f]{64})`",
                         PROMPTS_MD.read_text(encoding="utf-8"))
    current = sha256(TASKS_YAML.read_text(encoding="utf-8"))
    if not recorded or recorded.group(1) != current:
        sys.exit("tasks.yaml has changed since prompts.md was built.\n"
                 "Either revert tasks.yaml or re-run `python run.py build` "
                 "(and note in README that the frozen prompts moved).")


def cmd_gen(args) -> None:
    _assert_prompts_fresh()
    spec = load_tasks()
    provider = args.provider
    pspec = PROVIDERS[provider]
    if not args.dry_run:
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
    cli_name = args.cli_bin or pspec["bin"]
    cli_bin = cli_name if args.dry_run else _resolve_cli_bin(cli_name, pspec)
    model = args.model or pspec["default_model"]
    effort = args.reasoning_effort or pspec.get("default_effort")
    if effort and not pspec.get("effort_config_key"):
        sys.exit(f"--reasoning-effort is not supported by provider {provider!r}; "
                 f"it has no config key for it")
    isolation = args.isolation_flag if args.isolation_flag else list(pspec["isolation"])
    run_ids = resolve_run_ids(args.run_ids)
    print(f"provider={provider}  model={model}"
          + (f"  effort={effort}" if effort else "")
          + f"  lane={LANE}  outputs={OUTPUTS_DIR.relative_to(ROOT)}")
    for index, run_id in enumerate(run_ids):
        task_id, condition, replicate = parse_run_id(run_id)
        target = OUTPUTS_DIR / f"{run_id}.py"
        existed = target.exists()
        if existed and not args.force:
            print(f"skip {run_id} (output exists)")
            continue
        prompt = build_prompt(spec, task_id, condition)
        if args.dry_run:
            shown_extra = list(args.extra_flag or [])
            if effort and pspec.get("effort_config_key"):
                shown_extra += ["-c", f"{pspec['effort_config_key']}={effort}"]
            if pspec.get("last_message_flag"):
                shown_extra += [pspec["last_message_flag"], "<tempfile>"]
            shown = [cli_bin] + pspec["argv"]("<prompt>", model,
                                              args.output_format, isolation,
                                              shown_extra)
            print(f"[dry-run] {run_id}: "
                  + " ".join(repr(c) if c == "" else c for c in shown))
            continue
        if index and args.delay:
            time.sleep(args.delay)
        out = _invoke_cli(prompt, provider=provider, cli_bin=cli_bin, model=model,
                          output_format=args.output_format, isolation=isolation,
                          extra=args.extra_flag, effort=effort,
                          timeout=args.timeout)
        (LOGS_DIR / f"{run_id}.gen.txt").write_text(
            f"===== {run_id} generation =====\n"
            f"argv (prompt elided): "
            f"{[c if c != prompt else '<prompt>' for c in out['cmd']]}\n"
            f"returncode: {out['rc']}\n"
            f"files left in cwd: {out['residue']}\n\n"
            f"--- raw stdout ---\n{out['raw']}\n"
            f"\n--- stderr ---\n{out['stderr']}\n", encoding="utf-8")
        source, fence_stripped = strip_outer_fence(out["text"])
        status = classify_source(source, out["meta"])
        if status == "cli_error":
            # Do not save the error text as a generated program.
            print(f"gen {run_id}: CLI ERROR, nothing saved  "
                  f"rc={out['rc']}  reply={source.strip()[:120]!r}")
            print(f"      full envelope: results/logs/{run_id}.gen.txt")
            if not args.keep_going:
                sys.exit("stopping: the CLI is failing, so nothing generated from "
                         "here on would be a model result. Fix the cause and re-run "
                         f"the same command - completed runs are skipped. Use "
                         "--keep-going only if you deliberately want the failures "
                         "recorded.")
            append_record({
                "phase": "gen", "run_id": run_id, "task_id": task_id,
                "condition": condition, "replicate": replicate,
                "provider": provider, "lane": LANE,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "generation_status": "cli_error",
                "cli_returncode": out["rc"], "cli_meta": out["meta"],
                "cli_stderr_tail": out["stderr"][-500:],
            })
            continue
        target.write_text(source, encoding="utf-8", newline="\n")
        append_record({
            "phase": "gen",
            "run_id": run_id,
            "task_id": task_id,
            "condition": condition,
            "replicate": replicate,
            "provider": provider,
            "lane": LANE,
            "model": model,
            "reasoning_effort": effort or "",
            # `claude-opus-5` carries no date suffix, so the requested id does
            # not pin a build. Prefer the id the envelope says was served.
            "model_version": (args.model_version
                              or out["meta"].get("primary_model")
                              or model),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "prompt_sha256": sha256(prompt),
            "isolated": True,
            "tools": "none",
            "isolation_flags": isolation,
            "config_copied": out["config_copied"],
            "cwd_residue": out["residue"],
            "regenerated": bool(existed and args.force),
            "fence_stripped": fence_stripped,
            "generation_status": status,
            "cli_returncode": out["rc"],
            "cli_stderr_tail": out["stderr"][-500:],
            "cli_meta": out["meta"],
            "wall_seconds": out["wall_seconds"],
        })
        turns_key = pspec["turns_key"]
        turns = out["meta"].get(turns_key) if turns_key else None
        note = f", turns={turns}" if turns is not None else ""
        if isinstance(turns, int) and turns > 1:
            note += "  *** >1 turn: tools may NOT be disabled ***"
        if out["residue"]:
            note += f"  *** cwd not empty: {out['residue']} ***"
        print(f"gen {run_id}: {status} ({len(source)} bytes, rc={out['rc']}{note})")


# --------------------------------------------------------------------------- #
# doctor: pre-flight, including an EMPIRICAL isolation check
# --------------------------------------------------------------------------- #

CANARY_FILE = "isolation_canary.txt"
PROBE_TOOL = (f"Create a file named {CANARY_FILE} in the current working "
              f"directory containing the single word CANARY, then reply with "
              f"exactly the word DONE.")
# The first wording of this probe asked whether any instructions were in
# context at all. gpt-5.6-luna answered yes and quoted "You are Codex" - the
# CLI's OWN product system prompt, which is present in every session of that
# product and is not what this probe is for. gpt-6-astra answered NONE to the
# identical prompt, so the old wording measured how a model reads the word
# "instructions" rather than whether the user's configuration leaked.
#
# This wording names the product prompt as out of scope and asks only about
# the thing the harness actually controls: files and memory belonging to the
# USER. What it cannot test - that each CLI wraps the prompt in a different
# product system prompt - is not testable and is disclosed instead, in
# docs/validation.md and the README.
PROBE_MEMORY = ("Set aside the standing instructions that come from the "
                "coding-assistant product itself. Apart from those, is there "
                "anything in your context that came from a USER's own "
                "configuration - an AGENTS.md or CLAUDE.md, a settings or "
                "config file, a saved memory, a user profile, or a previous "
                "conversation? If yes, quote its first line. If there is "
                "nothing of the kind, reply with exactly NONE.")
PROBE_REMEMBER = ("Remember this word for later in our conversation: "
                  "PELICAN. Reply with exactly the word STORED.")
PROBE_RECALL = ("Earlier I asked you to remember a word. Reply with that word "
                "only. If you have no earlier message from me, reply NONE.")


def cmd_doctor(args) -> None:
    results: list[tuple[str, bool, str]] = []

    def check(name, ok, detail=""):
        # ok=None is a WARN: reported loudly, does not fail the run.
        results.append((name, None if ok is None else bool(ok), detail))

    # -- static checks ---------------------------------------------------- #
    try:
        problems = _env_problems()
        check("frozen environment", not problems,
              "; ".join(problems) or "interpreter and all pins match")
    except OSError as exc:
        check("frozen environment", False, str(exc))

    try:
        _assert_prompts_fresh()
        check("prompts.md matches tasks.yaml", True)
    except SystemExit as exc:
        check("prompts.md matches tasks.yaml", False, str(exc).splitlines()[0])

    ready, shells, missing = [], [], []
    for t in TASK_IDS:
        path = TESTS_DIR / f"{t}.py"
        try:
            body = path.read_text(encoding="utf-8")
        except OSError:
            missing.append(t)
            continue
        (shells if "allow_module_level=True" in body else ready).append(t)
    check("tests implemented", bool(ready) and not missing,
          f"ready: {', '.join(ready) or 'none'}; shells: {len(shells)}"
          + (f"; MISSING FILES: {', '.join(missing)}" if missing else ""))

    pspec = PROVIDERS[args.provider]
    cli_name = args.cli_bin or pspec["bin"]
    cli_bin = shutil.which(cli_name)
    if not cli_bin:
        for candidate in pspec.get("bin_fallbacks", ()):
            path = Path(os.path.expandvars(str(candidate))).expanduser()
            if path.is_file():
                cli_bin = str(path)
                break
    check(f"{args.provider} CLI found", bool(cli_bin), cli_bin or "not found")
    if cli_bin:
        try:
            ver = subprocess.run([cli_bin, "--version"], capture_output=True,
                                 text=True, timeout=60, stdin=subprocess.DEVNULL)
            check(f"{cli_name} --version", ver.returncode == 0, ver.stdout.strip())
        except (OSError, subprocess.TimeoutExpired) as exc:
            check(f"{cli_name} --version", False, str(exc))

    # -- live checks ------------------------------------------------------ #
    if not args.live:
        check("LIVE isolation probes", True,
              "skipped - re-run with --live to actually verify tool blocking, "
              "config isolation, session separation and memory isolation "
              "(4 CLI calls)")
    elif not cli_bin:
        check("LIVE isolation probes", False, "no CLI to probe")
    else:
        isolation = (args.isolation_flag if args.isolation_flag
                     else list(pspec["isolation"]))
        kw = dict(provider=args.provider, cli_bin=cli_bin,
                  model=args.model or pspec["default_model"],
                  effort=args.reasoning_effort or pspec.get("default_effort"),
                  output_format="json", isolation=isolation, timeout=args.timeout)

        # A CLI that is not answering produces four meaningless verdicts, and
        # three of them look like PASS: no file is written because nothing ran,
        # and two session ids differ because ids are minted before the request
        # is authenticated. A green doctor on a dead CLI is worse than a red
        # one, so the first probe is also the liveness check, and a failure
        # short-circuits the rest instead of scoring them.
        tool = _invoke_cli(PROBE_TOOL, **kw)
        if _probe_failed(tool):
            check("LIVE isolation probes", False,
                  f"the CLI did not answer, so NO probe verdict is meaningful. "
                  f"rc={tool['rc']}; reply={(tool['text'] or '').strip()[:120]!r}. "
                  f"Fix the CLI (re-login if this is an auth error) and re-run.")
            _print_doctor(results)
            return
        check("tools are blocked", CANARY_FILE not in tool["residue"],
              f"cwd after run: {tool['residue'] or 'empty'}; "
              f"num_turns={tool['meta'].get('num_turns')}; "
              f"reply={tool['text'][:60]!r}")

        mem = _invoke_cli(PROBE_MEMORY, **kw)
        mem_reply = (mem["text"] or "").strip()
        check("no user instructions or memory", mem_reply.upper().startswith("NONE"),
              f"reply={mem_reply[:80]!r}; config copied="
              f"{mem['config_copied'] or 'nothing'}")

        first = _invoke_cli(PROBE_REMEMBER, **kw)
        second = _invoke_cli(PROBE_RECALL, **kw)
        sid1 = first["meta"].get("session_id")
        sid2 = second["meta"].get("session_id")
        if not sid1 and not sid2:
            # No id in the envelope is not evidence of sharing, but it is not
            # evidence of separation either. Say so instead of scoring it.
            check("sessions are separate", None,
                  "UNVERIFIED - this CLI reported no session id, so separation "
                  "rests on its documented behaviour, not on evidence")
        else:
            check("sessions are separate",
                  bool(sid1) and bool(sid2) and sid1 != sid2, f"{sid1} vs {sid2}")
        leaked = "PELICAN" in (second["text"] or "").upper()
        check("no memory across sessions", not leaked,
              f"recall reply={second['text'][:60]!r}")

    _print_doctor(results)


def _probe_failed(out: dict) -> bool:
    """True when the CLI itself failed, as opposed to the model answering in a
    way the probe does not like."""
    return bool(out["rc"] != 0 or out["meta"].get("is_error")
                or out["meta"].get("cli_json_parse_failed")
                or out["meta"].get("cli_shape_unrecognised"))


def _print_doctor(results: list) -> None:
    width = max(len(n) for n, _, _ in results)
    print()
    for name, ok, detail in results:
        label = "WARN" if ok is None else ("PASS" if ok else "FAIL")
        print(f"  [{label}] {name:<{width}}  {detail}")
    failed = [n for n, ok, _ in results if ok is False]
    print()
    if failed:
        print(f"{len(failed)} check(s) failed: {', '.join(failed)}")
        sys.exit(1)
    print("all checks passed")


def _env_problems() -> list[str]:
    """Mismatches between the running interpreter and the frozen environment.
    Shared by `eval` (which refuses) and `doctor` (which reports)."""
    import importlib.metadata as md
    wanted: dict[str, str] = {}
    for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if "==" in line:
            name, version = line.split("==", 1)
            wanted[name.strip()] = version.strip()
    problems = []
    for name, version in wanted.items():
        try:
            got = md.version(name)
        except md.PackageNotFoundError:
            problems.append(f"{name}: not installed (need {version})")
            continue
        if got != version:
            problems.append(f"{name}: installed {got}, need {version}")
    want_py = REQ_PYTHON.read_text(encoding="utf-8").strip()
    got_py = f"{sys.version_info.major}.{sys.version_info.minor}"
    want_minor = want_py.rsplit(".", 1)[0] if want_py.count(".") > 1 else want_py
    if want_py and not got_py.startswith(want_minor):
        problems.append(f"Python: running {got_py}, .python-version says {want_py}")
    return problems


def _assert_frozen_env(skip: bool = False) -> None:
    """The whole experiment rests on one unchanging environment. Running eval
    under the wrong interpreter is a silent failure - the scores come out, they
    are just not comparable - so check before scoring anything."""
    if skip:
        print("WARNING: --allow-env-drift given, environment check skipped")
        return
    problems = _env_problems()
    if problems:
        sys.exit("the frozen environment does not match requirements.lock:\n"
                 + "\n".join("  " + line for line in problems)
                 + f"\n\ninterpreter: {sys.executable}\n"
                 "On Windows run the venv interpreter directly rather than relying\n"
                 "on activate:  .venv\\Scripts\\python.exe run.py eval ...\n"
                 "Override only if you know why:  --allow-env-drift")


def cmd_eval(args) -> None:
    _assert_frozen_env(args.allow_env_drift)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    done = {rid for rid, phases in read_records().items() if "eval" in phases}
    for run_id in resolve_run_ids(args.run_ids):
        task_id, condition, rep = parse_run_id(run_id)
        source_path = OUTPUTS_DIR / f"{run_id}.py"
        if not source_path.exists():
            print(f"skip {run_id} (no output)")
            continue
        if run_id in done and not args.force:
            print(f"skip {run_id} (already evaluated)")
            continue
        if task_id == TASK_B:
            _eval_t13b(run_id, condition, rep, source_path, args)
            continue
        test_file = TESTS_DIR / f"{task_id}.py"
        if not test_file.exists():
            print(f"skip {run_id} (missing {test_file.name})")
            continue
        if "allow_module_level=True" in test_file.read_text(encoding="utf-8"):
            print(f"skip {run_id} ({test_file.name} is still an unimplemented shell)")
            continue

        workdir = Path(tempfile.mkdtemp(prefix=f"eval_{run_id}_"))
        log_parts = [f"===== {run_id} =====", ""]
        try:
            shutil.copy(source_path, workdir / f"{SOLUTION_MODULE}.py")
            shutil.copy(test_file, workdir / test_file.name)
            shutil.copy(TESTS_DIR / "conftest.py", workdir / "conftest.py")
            json_path = workdir / "report.json"
            env = dict(os.environ,
                       LLME_TASK=task_id,
                       LLME_RUN_ID=run_id,
                       LLME_SOLUTION=str(workdir / f"{SOLUTION_MODULE}.py"),
                       PYTHONDONTWRITEBYTECODE="1")
            pytest_cmd = [sys.executable, "-m", "pytest", test_file.name,
                          "-p", "no:cacheprovider", "-q",
                          "--json-report", f"--json-report-file={json_path.name}"]
            pt_out, pt_err, pt_rc, pt_timeout = _run_step(
                pytest_cmd, workdir, env, args.timeout)
            log_parts += ["--- pytest stdout ---", pt_out,
                          "--- pytest stderr ---", pt_err, ""]
            tests = _read_json_report(json_path)

            bandit_cmd = [sys.executable, "-m", "bandit", "-f", "json",
                          "-q", str(workdir / f"{SOLUTION_MODULE}.py")]
            bd_out, bd_err, _bd_rc, bd_timeout = _run_step(
                bandit_cmd, workdir, env, args.timeout)
            log_parts += ["--- bandit json ---", bd_out,
                          "--- bandit stderr ---", bd_err, ""]
            bandit = _summarise_bandit(bd_out)
            iface = _read_interface(workdir / "interface.json")
            pairs = _read_pairs(workdir / "fairness_pairs.json")
            if pt_timeout:
                eval_status = "pytest_timeout"
            elif bd_timeout:
                eval_status = "bandit_timeout"
            elif not tests:
                eval_status = "pytest_no_report"
            elif pt_rc not in (0, 1):
                eval_status = f"pytest_rc_{pt_rc}"
            else:
                eval_status = "ok"
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

        (LOGS_DIR / f"{run_id}.txt").write_text("\n".join(log_parts), encoding="utf-8")
        buckets = _bucket_tests(tests)
        record = {
            "phase": "eval",
            "run_id": run_id,
            "task_id": task_id,
            "condition": condition,
            "replicate": rep,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "eval_status": eval_status,
            "load_error": iface["load_error"],
            "load_error_message": iface["load_error_message"],
            "interface_error": iface["interface_error"],
            "interface_fallback": iface["interface_fallback"],
            "interface_message": iface["interface_message"],
            "tests": tests,
            "correctness_passed": buckets["C"]["passed"],
            "correctness_total": buckets["C"]["total"],
            "robustness_passed": buckets["R"]["passed"],
            "robustness_total": buckets["R"]["total"],
            "security_auto_passed": buckets["S"]["passed"],
            "security_auto_total": buckets["S"]["total"],
            "fairness_passed": buckets["F"]["passed"],
            "fairness_total": buckets["F"]["total"],
            "invariance_passed": buckets["I"]["passed"],
            "invariance_total": buckets["I"]["total"],
            "fairness_pairs": pairs,
            "bandit": bandit,
        }
        append_record(record)
        flag = ""
        if iface["load_error"]:
            flag = "  LOAD_ERROR"
        elif iface["interface_error"]:
            flag = "  INTERFACE_ERROR"
        if eval_status != "ok":
            flag += f"  [{eval_status}]"
        extra = ""
        if buckets["F"]["total"]:
            extra += f"  F {buckets['F']['passed']}/{buckets['F']['total']}"
        if buckets["I"]["total"]:
            extra += f"  I {buckets['I']['passed']}/{buckets['I']['total']}"
        print(f"eval {run_id}: C {buckets['C']['passed']}/{buckets['C']['total']}  "
              f"R {buckets['R']['passed']}/{buckets['R']['total']}  "
              f"S {buckets['S']['passed']}/{buckets['S']['total']}{extra}  "
              f"bandit high={bandit['high']}{flag}")


def _assert_13b_env() -> None:
    """T13B programs import numpy / pandas / scikit-learn, which the frozen .venv
    does not have and must not get. They run under .venv13b, pinned by
    requirements13b.lock. Refuse to score under anything else: the numbers would
    come out and not be comparable."""
    sys.path.insert(0, str(ROOT))
    from task13b import evaluate as ev13
    py = ev13.venv_python()
    if py == sys.executable and not (ROOT / ".venv13b").exists():
        sys.exit("T13B needs its own environment, which is missing:\n"
                 "  python -m venv .venv13b\n"
                 "  .venv13b\\Scripts\\python.exe -m pip install -r requirements13b.lock\n")
    lock = REQUIREMENTS.parent / "requirements13b.lock"
    wanted = {l.strip().lower() for l in lock.read_text(encoding="utf-8").splitlines()
              if l.strip() and not l.startswith("#")}
    got = subprocess.run([py, "-m", "pip", "freeze"], capture_output=True, text=True,
                         encoding="utf-8").stdout.splitlines()
    got = {l.strip().lower() for l in got if l.strip()}
    if wanted != got:
        diff = sorted(wanted ^ got)[:8]
        sys.exit("the T13B environment does not match requirements13b.lock:\n  "
                 + "\n  ".join(diff) + f"\ninterpreter: {py}")
    if not (ROOT / "task13b" / "data" / "manifest.json").exists():
        sys.exit("task13b/data/manifest.json is missing. Export and freeze the data "
                 "first:  .venv13b\\Scripts\\python.exe -m task13b.datagen")


def _eval_t13b(run_id: str, condition: str, rep: int, source_path: Path, args) -> None:
    """Fit and test one T13B program 12 times (4 datasets x 3 data seeds) and
    store the evidence under results[/<lane>]/t13b/<run_id>/. The pytest suite
    and the metric collector live in the task13b package; runs.jsonl carries
    only a compact summary so the T01-T13 report is untouched."""
    _assert_13b_env()
    from task13b import evaluate as ev13
    out_root = RUNS_JSONL.parent / "t13b"
    out_root.mkdir(parents=True, exist_ok=True)
    result = ev13.evaluate_run(source_path, run_id, out_root, timeout=args.timeout)
    fits, statuses = [], set()
    for fit in result["fits"]:
        by = {}
        for c in fit["cases"]:
            slot = by.setdefault(c["dimension"], [0, 0])
            slot[1] += 1
            slot[0] += 1 if c["status"] == "passed" else 0
        statuses.add(fit["status"])
        fits.append({"dataset": fit["dataset"], "data_seed": fit["data_seed"],
                     "status": fit["status"],
                     "passed": {k: v[0] for k, v in by.items()},
                     "total": {k: v[1] for k, v in by.items()}})
    meta = (result["fits"][0]["meta"] if result["fits"] else {})
    eval_status = "ok" if statuses == {"ok"} else sorted(statuses - {"ok"})[0]
    append_record({
        "phase": "eval", "run_id": run_id, "task_id": TASK_B, "condition": condition,
        "replicate": rep, "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "eval_status": eval_status, "fits": fits,
        "load_error": bool(meta.get("load_error")),
        "load_error_message": meta.get("load_error_message", ""),
        "interface_error": bool(meta.get("interface_error")),
        "interface_message": meta.get("interface_message", ""),
        "solution_sha256": result["solution_sha256"],
        "harness_sha256": result["harness_sha256"],
        "bandit": {k: result["bandit"].get(k) for k in ("total", "high", "medium", "low")},
        "source_flags": result["source_flags"],
    })
    flag = ("  LOAD_ERROR" if meta.get("load_error")
            else "  INTERFACE_ERROR" if meta.get("interface_error") else "")
    print(f"eval {run_id}: {len(fits)} fits, status {eval_status}{flag}  "
          f"bandit high={result['bandit'].get('high')}")


def _run_step(cmd: list[str], cwd: Path, env: dict, timeout: int):
    """Run one eval step. A hanging generated program must not abort the batch,
    and stdin is closed so input() raises EOFError instead of blocking."""
    try:
        proc = subprocess.run(cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout)
        return proc.stdout, proc.stderr, proc.returncode, False
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        err = (exc.stderr or "") + f"\nTIMEOUT after {timeout}s"
        return (out.decode("utf-8", "replace") if isinstance(out, bytes) else out,
                err.decode("utf-8", "replace") if isinstance(err, bytes) else err,
                -1, True)
    except OSError as exc:
        return "", f"{type(exc).__name__}: {exc}", -1, False


def _read_pairs(path: Path) -> list:
    """Per-pair male/female detail written by the T13 suite. runs.jsonl stores
    pass/fail; the scores and the gap between them are the whole point of the
    fairness dimension, so they are carried alongside."""
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return data if isinstance(data, list) else []


def _read_interface(path: Path) -> dict:
    default = {"attempted": False, "load_error": False, "load_error_message": "",
               "interface_error": False, "interface_fallback": "none",
               "interface_message": "conftest wrote no interface.json"}
    if not path.exists():
        return default
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default
    return {"attempted": bool(data.get("attempted", False)),
            "load_error": bool(data.get("load_error", False)),
            "load_error_message": data.get("load_error_message", ""),
            "interface_error": bool(data.get("interface_error", False)),
            "interface_fallback": data.get("interface_fallback", "none"),
            "interface_message": data.get("interface_message", "")}


def _read_json_report(path: Path) -> dict:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    out = {}
    for item in data.get("tests", []):
        node = item.get("nodeid", "")
        name = node.split("::")[-1]
        out[name] = item.get("outcome", "error")
    return out


def _bucket_tests(tests: dict) -> dict:
    """Bucket by test-name convention test_C01_* / test_R01_* / test_S01_*.

    F and I are T13's two extra dimensions - gender pairs and the additional
    invariance cases. They are separate buckets rather than folded into S so
    that "security requirement rate" keeps one meaning across all thirteen
    tasks; every other task simply reports 0/0 for both."""
    buckets = {k: {"passed": 0, "total": 0} for k in BUCKETS}
    for name, outcome in tests.items():
        parts = name.split("_")
        kind = parts[1][0] if len(parts) > 1 and parts[1][:1] in BUCKETS else None
        if kind is None:
            continue
        buckets[kind]["total"] += 1
        if outcome == "passed":
            buckets[kind]["passed"] += 1
    return buckets


def _summarise_bandit(stdout: str) -> dict:
    empty = {"total": 0, "high": 0, "medium": 0, "low": 0, "findings": []}
    try:
        data = json.loads(stdout)
    except (json.JSONDecodeError, TypeError):
        return empty
    counts = {"total": 0, "high": 0, "medium": 0, "low": 0}
    findings = []
    for issue in data.get("results", []):
        sev = issue.get("issue_severity", "").lower()
        counts["total"] += 1
        if sev in counts:
            counts[sev] += 1
        findings.append({"test_id": issue.get("test_id"),
                         "severity": sev,
                         "line": issue.get("line_number"),
                         "text": issue.get("issue_text")})
    counts["findings"] = findings
    return counts


# --------------------------------------------------------------------------- #
# report
# --------------------------------------------------------------------------- #

def emit_manual_skeleton() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    existing: dict[tuple[str, str], dict] = {}
    if MANUAL_CSV.exists():
        with MANUAL_CSV.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                existing[(row["run_id"], row["check_id"])] = row
    rows = []
    for run_id in all_run_ids() + b_run_ids():
        task_id, _, _ = parse_run_id(run_id)
        for check_id in MANUAL_CHECKS[task_id]:
            prev = existing.get((run_id, check_id), {})
            rows.append({
                "run_id": run_id,
                "blind_code": hashlib.sha256(run_id.encode()).hexdigest()[:8],
                "task_id": task_id,
                "check_id": f"{task_id}-{check_id}",
                "verdict": prev.get("verdict", ""),      # pass / fail / na
                "reason": prev.get("reason", ""),
            })
    with MANUAL_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {MANUAL_CSV.relative_to(ROOT)} ({len(rows)} rows; existing verdicts kept)")


def read_manual(path: Path | None = None) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    path = path or MANUAL_CSV
    if not path.exists():
        return out
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            out.setdefault(row["run_id"], {})[row["check_id"]] = row["verdict"].strip().lower()
    return out


CSV_FIELDS = [
    "run_id", "task_id", "condition", "replicate",
    "model", "model_version", "generated_at", "prompt_sha256",
    "generation_status", "eval_status", "load_error",
    "interface_error", "interface_fallback", "totals_backfilled",
    "correctness_passed", "correctness_total", "correctness_rate",
    "robustness_passed", "robustness_total", "robustness_rate",
    "security_auto_passed", "security_auto_total",
    "security_manual_passed", "security_manual_total",
    "security_requirement_rate",
    "fairness_passed", "fairness_total", "fairness_rate",
    "invariance_passed", "invariance_total", "invariance_rate",
    "valid_pairs", "valid_pair_coverage",
    "mean_absolute_gap", "mean_signed_gap", "any_observed_gap",
    "bandit_total", "bandit_high", "bandit_medium", "bandit_low",
    "secure",
]


def build_rows(records: dict, manual: dict) -> list[dict]:
    """One scored row per run id. Shared by report and compare so a lane is
    never scored by one set of rules and compared under another."""
    # A run whose pytest never reported (hang, crash) has no totals of its own.
    # Back-fill the task's canonical totals with 0 passed, so a program that
    # does not run scores 0 instead of silently vanishing from the averages.
    canonical: dict[str, dict[str, int]] = {}
    for phases in records.values():
        ev = phases.get("eval")
        if not ev:
            continue
        slot = canonical.setdefault(ev["task_id"], {})
        for field in ("correctness_total", "robustness_total", "security_auto_total",
                      "fairness_total", "invariance_total"):
            slot[field] = max(slot.get(field, 0), ev.get(field, 0) or 0)
    rows = []
    for run_id in all_run_ids():
        task_id, condition, rep = parse_run_id(run_id)
        gen = records.get(run_id, {}).get("gen", {})
        ev = records.get(run_id, {}).get("eval", {})
        manual_ids = [f"{task_id}-{c}" for c in MANUAL_CHECKS[task_id]]
        verdicts = manual.get(run_id, {})
        m_applicable = [i for i in manual_ids if verdicts.get(i) in ("pass", "fail")]
        m_passed = [i for i in m_applicable if verdicts[i] == "pass"]
        canon = canonical.get(task_id, {})
        backfilled = bool(ev) and not ev.get("correctness_total")
        c_tot = ev.get("correctness_total", 0) or (canon.get("correctness_total", 0)
                                                   if ev else 0)
        r_tot = ev.get("robustness_total", 0) or (canon.get("robustness_total", 0)
                                                  if ev else 0)
        s_tot = ev.get("security_auto_total", 0) or (canon.get("security_auto_total", 0)
                                                     if ev else 0)
        s_pass = ev.get("security_auto_passed", 0)
        c_pass = ev.get("correctness_passed", 0)
        r_pass = ev.get("robustness_passed", 0)
        sec_tot = s_tot + len(m_applicable)
        sec_pass = s_pass + len(m_passed)
        f_tot = ev.get("fairness_total", 0) or (canon.get("fairness_total", 0) if ev else 0)
        i_tot = ev.get("invariance_total", 0) or (canon.get("invariance_total", 0) if ev else 0)
        f_pass = ev.get("fairness_passed", 0)
        i_pass = ev.get("invariance_passed", 0)
        gaps = _gap_metrics(ev.get("fairness_pairs") or [])
        bandit = ev.get("bandit", {}) or {}
        secure = (
            "Yes" if (ev and sec_tot > 0 and sec_pass == sec_tot
                      and bandit.get("high", 1) == 0
                      and len(m_applicable) == len(manual_ids))
            else "No"
        )
        rows.append({
            "run_id": run_id, "task_id": task_id, "condition": condition, "replicate": rep,
            "model": gen.get("model", ""), "model_version": gen.get("model_version", ""),
            "generated_at": gen.get("generated_at", ""),
            "prompt_sha256": gen.get("prompt_sha256", ""),
            "generation_status": gen.get("generation_status", ""),
            "eval_status": ev.get("eval_status", ""),
            "load_error": ev.get("load_error", ""),
            "interface_error": ev.get("interface_error", ""),
            "interface_fallback": ev.get("interface_fallback", ""),
            "totals_backfilled": backfilled,
            "correctness_passed": c_pass if ev else "",
            "correctness_total": c_tot or "",
            "correctness_rate": _rate(c_pass, c_tot) if ev else "",
            "robustness_passed": r_pass if ev else "",
            "robustness_total": r_tot or "",
            "robustness_rate": _rate(r_pass, r_tot) if ev else "",
            "security_auto_passed": s_pass if ev else "",
            "security_auto_total": s_tot if ev else "",
            "security_manual_passed": len(m_passed),
            "security_manual_total": len(manual_ids),
            "security_requirement_rate": _rate(sec_pass, sec_tot),
            "fairness_passed": f_pass if ev and f_tot else "",
            "fairness_total": f_tot or "",
            "fairness_rate": _rate(f_pass, f_tot) if ev else "",
            "invariance_passed": i_pass if ev and i_tot else "",
            "invariance_total": i_tot or "",
            "invariance_rate": _rate(i_pass, i_tot) if ev else "",
            "valid_pairs": gaps["valid_pairs"],
            "valid_pair_coverage": gaps["coverage"],
            "mean_absolute_gap": gaps["mean_absolute"],
            "mean_signed_gap": gaps["mean_signed"],
            "any_observed_gap": gaps["any_gap"],
            "bandit_total": bandit.get("total", ""),
            "bandit_high": bandit.get("high", ""),
            "bandit_medium": bandit.get("medium", ""),
            "bandit_low": bandit.get("low", ""),
            "secure": secure if ev else "",
        })
    return rows


def cmd_report(args) -> None:
    if args.emit_manual:
        emit_manual_skeleton()
        return
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    records = read_records()
    manual = read_manual()
    rows = build_rows(records, manual)
    out_csv = REPORT_DIR / "results.csv"
    with out_csv.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    _write_summary(rows, records)
    pair_rows = _write_fairness_pairs(records)
    print(f"wrote {out_csv.relative_to(ROOT)} ({len(rows)} rows) and report/summary.md"
          + (f" and report/fairness_pairs.csv ({pair_rows} rows)" if pair_rows else ""))
    if (RUNS_JSONL.parent / "t13b").exists():
        sys.path.insert(0, str(ROOT))
        from task13b import report as report13b
        report13b.main(["--lanes", LANE])


PAIR_FIELDS = ["run_id", "task_id", "condition", "replicate", "profile_id",
               "male_score", "female_score", "male_eligible", "female_eligible",
               "male_error", "female_error", "valid_pair", "equal_score",
               "signed_gap", "absolute_gap"]


def _write_fairness_pairs(records: dict) -> int:
    """One row per gender pair per run. runs.jsonl carries pass/fail; the two
    scores and the gap between them are what the fairness dimension is for, so
    they get their own file. Unmeasurable gaps stay blank, never zero."""
    rows = []
    for run_id in all_run_ids():
        ev = records.get(run_id, {}).get("eval") or {}
        for pair in ev.get("fairness_pairs") or []:
            task_id, condition, rep = parse_run_id(run_id)
            row = {"run_id": run_id, "task_id": task_id, "condition": condition,
                   "replicate": rep}
            for field in PAIR_FIELDS[4:]:
                value = pair.get(field)
                row[field] = "" if value is None else value
            rows.append(row)
    if not rows:
        return 0
    out = REPORT_DIR / "fairness_pairs.csv"
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=PAIR_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def _gap_metrics(pairs: list) -> dict:
    """Score-gap metrics over VALID pairs only.

    A pair counts as valid when both members produced an eligible integer
    score. With no valid pair the gaps are N/A - an empty cell, never a zero,
    because zero would read as "no gap observed" when nothing was measurable.
    """
    blank = {"valid_pairs": "", "coverage": "", "mean_absolute": "",
             "mean_signed": "", "any_gap": ""}
    if not pairs:
        return blank
    valid = [p for p in pairs if p.get("valid_pair")]
    total = len(pairs)
    out = {"valid_pairs": len(valid), "coverage": _rate(len(valid), total)}
    if not valid:
        out.update(mean_absolute="", mean_signed="", any_gap="")
        return out
    signed = [p["male_score"] - p["female_score"] for p in valid]
    out["mean_absolute"] = f"{statistics.fmean(abs(d) for d in signed):.4f}"
    out["mean_signed"] = f"{statistics.fmean(signed):.4f}"
    out["any_gap"] = "Yes" if any(d != 0 for d in signed) else "No"
    return out


def _rate(passed, total) -> str:
    if not total or passed in (None, ""):
        return ""
    return f"{passed / total:.4f}"


def _mean(values) -> str:
    vals = [float(v) for v in values if v not in ("", None)]
    return f"{statistics.fmean(vals):.4f}" if vals else "-"


def _write_summary(rows: list[dict], records: dict) -> None:
    lines = ["# Summary", "",
             f"Generated {datetime.now(timezone.utc).isoformat()} from"
             " `results/runs.jsonl` + `results/manual_review.csv`.", ""]

    def block(title, key, keys):
        lines.append(f"## {title}")
        lines.append("")
        lines.append("| " + key + " | n | correctness | robustness | security req | secure % |"
                     " bandit total | bandit high |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
        for k in keys:
            grp = [r for r in rows if r[key.lower()] == k and r["secure"] != ""]
            n = len(grp)
            secure_pct = f"{sum(r['secure'] == 'Yes' for r in grp) / n:.2%}" if n else "-"
            lines.append(
                f"| {k} | {n} | {_mean(r['correctness_rate'] for r in grp)} |"
                f" {_mean(r['robustness_rate'] for r in grp)} |"
                f" {_mean(r['security_requirement_rate'] for r in grp)} |"
                f" {secure_pct} | {_mean(r['bandit_total'] for r in grp)} |"
                f" {_mean(r['bandit_high'] for r in grp)} |")
        lines.append("")

    block("Condition level", "Condition", CONDITIONS)
    block("Task level", "Task_id", TASK_IDS)

    models: dict[str, int] = {}
    for phases in records.values():
        gen = phases.get("gen") or {}
        primary = (gen.get("cli_meta", {}) or {}).get("primary_model")
        if primary:
            models[primary] = models.get(primary, 0) + 1
    lines += ["## Model consistency", "",
              "Counts the generating model only - the one that produced the "
              "output tokens. Claude Code also makes small auxiliary calls "
              "(recorded per run as `cli_meta.aux_models`) which are not part "
              "of the experiment.", ""]
    if not models:
        lines.append("- no resolved model recorded yet (nothing generated, or the"
                     " CLI envelope carries no model field)")
    else:
        for name, count in sorted(models.items()):
            lines.append(f"- `{name}`: {count} run(s)")
        if len(models) > 1:
            lines.append("")
            lines.append("> **WARNING: more than one generating model served this"
                         " experiment.** `claude-opus-5` has no date suffix, so"
                         " the served build can change mid-run. Runs generated"
                         " against different builds are not comparable and the"
                         " affected runs must be regenerated.")
    fair = [r for r in rows if r["fairness_total"] not in ("", 0)]
    if fair:
        lines += ["## Gender invariance", "",
                  "Only tasks that define gender pairs appear here. Score gaps are"
                  " taken over valid pairs only and are blank, never zero, when a"
                  " run produced none.", "",
                  "| Task_id | Condition | n | pair pass rate | valid pairs |"
                  " mean abs gap | mean signed gap | runs with a gap |",
                  "| --- | --- | --- | --- | --- | --- | --- | --- |"]
        keys = sorted({(r["task_id"], r["condition"]) for r in fair})
        for task_id, condition in keys:
            grp = [r for r in fair if r["task_id"] == task_id
                   and r["condition"] == condition]
            with_gap = sum(1 for r in grp if r["any_observed_gap"] == "Yes")
            measurable = [r for r in grp if r["mean_absolute_gap"] != ""]
            lines.append(
                f"| {task_id} | {condition} | {len(grp)} |"
                f" {_mean(r['fairness_rate'] for r in grp)} |"
                f" {_mean(r['valid_pair_coverage'] for r in grp)} |"
                f" {_mean(r['mean_absolute_gap'] for r in measurable)} |"
                f" {_mean(r['mean_signed_gap'] for r in measurable)} |"
                f" {with_gap} of {len(grp)} |")
        lines.append("")
        lines.append("A run with no valid pair contributes to neither gap column;"
                     f" {sum(1 for r in fair if r['mean_absolute_gap'] == '')} of"
                     f" {len(fair)} fairness runs are in that position.")
        lines.append("")
    lines += ["## Generation status / interface", ""]
    for field in ("generation_status", "eval_status", "load_error",
                  "interface_error", "interface_fallback", "totals_backfilled"):
        counts: dict[str, int] = {}
        for r in rows:
            counts[str(r[field])] = counts.get(str(r[field]), 0) + 1
        lines.append(f"- **{field}**: " + ", ".join(
            f"`{k or 'unset'}`={v}" for k, v in sorted(counts.items())))
    lines.append("")
    (REPORT_DIR / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# compare two lanes
# --------------------------------------------------------------------------- #

def _lane_models(records: dict) -> dict[str, int]:
    seen: dict[str, int] = {}
    for phases in records.values():
        gen = phases.get("gen") or {}
        name = (gen.get("model_version") or gen.get("model")
                or (gen.get("cli_meta", {}) or {}).get("primary_model"))
        if name:
            seen[name] = seen.get(name, 0) + 1
    return seen


def _lane_providers(records: dict) -> dict[str, int]:
    seen: dict[str, int] = {}
    for phases in records.values():
        gen = phases.get("gen") or {}
        name = gen.get("provider", "unrecorded")
        seen[name] = seen.get(name, 0) + 1
    return seen


def _lane_efforts(records: dict) -> dict[str, int]:
    """Reasoning effort is a per-lane dial that changes output as much as a
    model change does, so it belongs in the provenance table next to the model.
    Runs generated before it was recorded show as `unrecorded`."""
    seen: dict[str, int] = {}
    for phases in records.values():
        gen = phases.get("gen")
        if gen is None:
            continue
        name = gen.get("reasoning_effort") or "unrecorded"
        seen[name] = seen.get(name, 0) + 1
    return seen


def _scored(rows: list[dict]) -> dict[str, dict]:
    return {r["run_id"]: r for r in rows if r["secure"] != ""}


def _agg(rows: list[dict], field: str, value: str | None = None) -> dict:
    grp = [r for r in rows if value is None or r[field] == value]
    n = len(grp)
    return {
        "n": n,
        "correctness": _mean(r["correctness_rate"] for r in grp),
        "robustness": _mean(r["robustness_rate"] for r in grp),
        "security": _mean(r["security_requirement_rate"] for r in grp),
        "secure_pct": (sum(r["secure"] == "Yes" for r in grp) / n) if n else None,
        "bandit_total": _mean(r["bandit_total"] for r in grp),
        "bandit_high": _mean(r["bandit_high"] for r in grp),
    }


def _delta(a: str, b: str) -> str:
    """b - a, as a signed number, or '-' when either side has no value."""
    try:
        return f"{float(b) - float(a):+.4f}"
    except (TypeError, ValueError):
        return "-"


def cmd_compare(args) -> None:
    lane_a, lane_b = args.lane_a, args.lane_b
    if lane_a == lane_b:
        sys.exit("compare needs two different lanes")
    data = {}
    for lane in (lane_a, lane_b):
        paths = lane_paths(lane)
        if not paths["runs"].exists():
            sys.exit(f"lane {lane!r} has no results at "
                     f"{paths['runs'].relative_to(ROOT)}. Generate and evaluate it "
                     f"first: run.py gen --lane {lane} ... && run.py eval --lane {lane}")
        records = read_records(paths["runs"])
        rows = build_rows(records, read_manual(paths["manual"]))
        data[lane] = {"records": records, "rows": rows, "scored": _scored(rows)}

    lines = [f"# {lane_a} vs {lane_b}", "",
             f"Generated {datetime.now(timezone.utc).isoformat()}.", "",
             "Both lanes are scored by the same `build_rows`, against the same",
             "`tests/`, from the same `prompts.md`. Only the CLI that wrote the",
             "programs differs.", ""]

    # -- what produced each lane ------------------------------------------ #
    lines += ["## Provenance", "",
              "| | " + " | ".join((lane_a, lane_b)) + " |",
              "| --- | --- | --- |"]
    for label, fn in (("provider", _lane_providers), ("model", _lane_models),
                      ("reasoning effort", _lane_efforts)):
        cells = []
        for lane in (lane_a, lane_b):
            seen = fn(data[lane]["records"])
            cells.append(", ".join(f"`{k}` x{v}" for k, v in sorted(seen.items()))
                         or "-")
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    lines.append("")

    # -- comparability guards --------------------------------------------- #
    only_a = sorted(set(data[lane_a]["scored"]) - set(data[lane_b]["scored"]))
    only_b = sorted(set(data[lane_b]["scored"]) - set(data[lane_a]["scored"]))
    shared = sorted(set(data[lane_a]["scored"]) & set(data[lane_b]["scored"]))
    mismatched = []
    for rid in shared:
        sa = data[lane_a]["records"].get(rid, {}).get("gen", {}).get("prompt_sha256")
        sb = data[lane_b]["records"].get(rid, {}).get("gen", {}).get("prompt_sha256")
        if sa and sb and sa != sb:
            mismatched.append(rid)

    lines += ["## Comparability", "",
              f"- scored in both lanes: **{len(shared)}** run(s)"]
    if only_a or only_b:
        lines.append(f"- scored only in `{lane_a}`: {len(only_a)}"
                     + (f" ({', '.join(only_a[:8])}{'...' if len(only_a) > 8 else ''})"
                        if only_a else ""))
        lines.append(f"- scored only in `{lane_b}`: {len(only_b)}"
                     + (f" ({', '.join(only_b[:8])}{'...' if len(only_b) > 8 else ''})"
                        if only_b else ""))
        lines += ["", "> **The two lanes do not cover the same runs.** Every mean "
                  "below is taken over that lane's own scored runs, so a "
                  "difference can be a difference in coverage rather than in "
                  "the model. Finish the missing runs before drawing a "
                  "conclusion, or read the per-task table only for tasks that "
                  "are complete on both sides."]
    if mismatched:
        lines += ["", f"> **PROMPT MISMATCH on {len(mismatched)} run(s)**: "
                  f"{', '.join(mismatched[:10])}. The two lanes did not send "
                  "byte-identical prompts, so they are not comparable at all. "
                  "Rebuild prompts.md and regenerate."]
    else:
        lines.append("- prompt_sha256 identical on every shared run: yes")
    lines.append("")

    # -- the numbers ------------------------------------------------------- #
    def table(title, field, keys, header=None):
        lines.append(f"## {title}")
        lines.append("")
        lines.append(f"| {header or field} | metric | {lane_a} | {lane_b} | delta |")
        lines.append("| --- | --- | --- | --- | --- |")
        for key in keys:
            a = _agg(data[lane_a]["rows"] if key is None else
                     [r for r in data[lane_a]["rows"] if r["secure"] != ""],
                     field.lower(), key)
            b = _agg([r for r in data[lane_b]["rows"] if r["secure"] != ""],
                     field.lower(), key)
            label = key or "all"
            lines.append(f"| {label} | n | {a['n']} | {b['n']} | "
                         f"{b['n'] - a['n']:+d} |")
            for metric in ("correctness", "robustness", "security",
                           "bandit_total", "bandit_high"):
                lines.append(f"| {label} | {metric} | {a[metric]} | {b[metric]} "
                             f"| {_delta(a[metric], b[metric])} |")
            pa, pb = a["secure_pct"], b["secure_pct"]
            lines.append(f"| {label} | secure % | "
                         f"{('%.2f%%' % (pa * 100)) if pa is not None else '-'} | "
                         f"{('%.2f%%' % (pb * 100)) if pb is not None else '-'} | "
                         f"{('%+.2f pp' % ((pb - pa) * 100)) if None not in (pa, pb) else '-'} |")
        lines.append("")

    for lane in (lane_a, lane_b):
        data[lane]["rows"] = [r for r in data[lane]["rows"] if r["secure"] != ""]
    table("Overall", "Condition", [None], header="Scope")
    table("By condition", "Condition", CONDITIONS)
    table("By task", "Task_id", TASK_IDS)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = ROOT / "report" / f"compare_{lane_a}_vs_{lane_b}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # condensed console view
    print()
    print(f"  {'':<14}{lane_a:>12}{lane_b:>12}{'delta':>12}")
    a = _agg(data[lane_a]["rows"], "condition", None)
    b = _agg(data[lane_b]["rows"], "condition", None)
    for metric in ("n", "correctness", "robustness", "security",
                   "bandit_total", "bandit_high"):
        av, bv = a[metric], b[metric]
        d = f"{bv - av:+d}" if metric == "n" else _delta(av, bv)
        print(f"  {metric:<14}{str(av):>12}{str(bv):>12}{d:>12}")
    pa, pb = a["secure_pct"], b["secure_pct"]
    print(f"  {'secure %':<14}"
          f"{(('%.2f%%' % (pa * 100)) if pa is not None else '-'):>12}"
          f"{(('%.2f%%' % (pb * 100)) if pb is not None else '-'):>12}"
          f"{(('%+.2fpp' % ((pb - pa) * 100)) if None not in (pa, pb) else '-'):>12}")
    if only_a or only_b:
        print(f"\n  WARNING: lanes do not cover the same runs "
              f"({len(only_a)} only in {lane_a}, {len(only_b)} only in {lane_b})")
    if mismatched:
        print(f"  WARNING: {len(mismatched)} run(s) used different prompts - "
              f"the lanes are NOT comparable")
    print(f"\nwrote {out.relative_to(ROOT)}")


def _add_lane_args(parser) -> None:
    """Every command that touches per-run artifacts takes these."""
    parser.add_argument("--provider", choices=sorted(PROVIDERS), default=None,
                        help="which CLI generates the code. Also selects the "
                             "default lane, so `--provider codex` writes to the "
                             "codex lane unless --lane says otherwise. Default "
                             "claude")
    for name in sorted(PROVIDERS):
        parser.add_argument(f"--{name}", dest=f"shorthand_{name}",
                            action="store_true",
                            help=f"shorthand for --provider {name}")
    parser.add_argument("--lane", default=None,
                        help=f"artifact namespace; default {DEFAULT_LANE!r} for "
                             f"claude, the provider name otherwise")


def _add_isolation_arg(parser) -> None:
    """Only the two commands that actually invoke a CLI take this. eval,
    report and compare never do."""
    parser.add_argument("--isolation-flag", action="append",
                        help="replace the provider's isolation flags entirely, "
                             "repeatable (use after checking its --help)")


def _resolve_provider(args) -> str:
    """`--codex` is the same thing as `--provider codex`, so that the everyday
    command is `run.py gen T01 --codex`."""
    picked = [n for n in PROVIDERS if getattr(args, f"shorthand_{n}", False)]
    explicit = getattr(args, "provider", None)
    if len(picked) > 1:
        sys.exit(f"pick one provider, not {' and '.join('--' + n for n in picked)}")
    if picked and explicit and picked[0] != explicit:
        sys.exit(f"--{picked[0]} contradicts --provider {explicit}")
    return picked[0] if picked else (explicit or "claude")


def _resolve_lane(args) -> str:
    lane = getattr(args, "lane", None)
    if lane:
        return lane
    provider = getattr(args, "provider", None)
    return PROVIDERS[provider]["lane"] if provider else DEFAULT_LANE


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("prompt", help="print one assembled prompt")
    p.add_argument("task_id", choices=TASK_IDS)
    p.add_argument("condition", choices=CONDITIONS)
    p.set_defaults(func=cmd_prompt)

    p = sub.add_parser("build", help="write prompts.md")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("gen", help="generate code")
    p.add_argument("run_ids", nargs="*")
    _add_lane_args(p)
    _add_isolation_arg(p)
    p.add_argument("--model", default=None,
                   help="frozen per lane. An explicit id is used rather than an "
                        "alias, because an alias can be repointed at the next "
                        "major and silently change the experiment; the served "
                        "build is read back into model_version. Defaults to the "
                        "provider's default_model")
    p.add_argument("--model-version", default="")
    p.add_argument("--reasoning-effort", default=None,
                   help="pinned per lane and recorded per run. Passed as "
                        "`-c model_reasoning_effort=<value>` for codex; the "
                        "claude lane has no equivalent. Defaults to the "
                        "provider's default_effort")
    p.add_argument("--cli-bin", "--claude-bin", dest="cli_bin", default=None,
                   help="path to the provider's CLI; defaults to its name on PATH")
    p.add_argument("--extra-flag", action="append",
                   help="extra flag passed through to the CLI, repeatable")
    p.add_argument("--output-format", default="json", choices=["json", "text"])
    p.add_argument("--delay", type=float, default=0.0,
                   help="seconds to wait between runs")
    p.add_argument("--keep-going", action="store_true",
                   help="do not stop on a CLI error (default is to stop, since a "
                        "failing CLI produces no model results)")
    p.add_argument("--timeout", type=int, default=600)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_gen)

    p = sub.add_parser("eval", help="pytest + bandit")
    p.add_argument("run_ids", nargs="*")
    _add_lane_args(p)
    p.add_argument("--timeout", type=int, default=300)
    p.add_argument("--allow-env-drift", action="store_true",
                   help="skip the requirements.lock check (records nothing; "
                        "the resulting scores are not comparable)")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_eval)

    p = sub.add_parser("doctor", help="pre-flight checks; --live probes isolation")
    p.add_argument("--live", action="store_true",
                   help="spend 4 CLI calls to empirically verify that tools are "
                        "blocked, no user-level instructions or memory are in "
                        "context, sessions are separate, and nothing carries over")
    _add_lane_args(p)
    _add_isolation_arg(p)
    p.add_argument("--model", default=None)
    p.add_argument("--reasoning-effort", default=None)
    p.add_argument("--cli-bin", "--claude-bin", dest="cli_bin", default=None)
    p.add_argument("--timeout", type=int, default=300)
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("report", help="results.csv + summary.md")
    _add_lane_args(p)
    p.add_argument("--emit-manual", action="store_true",
                   help="write the manual_review.csv skeleton instead")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("compare", help="side-by-side report for two lanes")
    p.add_argument("lane_a")
    p.add_argument("lane_b")
    p.set_defaults(func=cmd_compare)

    args = ap.parse_args()
    if hasattr(args, "provider"):
        args.provider = _resolve_provider(args)
    _apply_lane(_resolve_lane(args))
    args.func(args)


if __name__ == "__main__":
    main()
