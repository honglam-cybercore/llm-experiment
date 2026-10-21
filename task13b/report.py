"""Task 13B result files and comparison report.

Reads what run.py eval T13B stored under results[/<lane>]/t13b/ and writes, per
lane, report[/<lane>]/t13b/:

    test_results.csv            one row per case per fit
    pair_results.csv            one row per G / P / J pair per fit
    group_predictions.csv       one row per group record per fit (evaluator output)
    group_metrics.csv           one row per fit
    implementation_summary.csv  one row per implementation x dataset x data seed
    dataset_contrasts.csv       D0-D3 contrasts per implementation and seed
    model_summary.csv           per model / condition / dataset, then pooled

and, across lanes, report/t13b_comparison.md.

Pure standard library: it runs under the frozen .venv. Unavailable numbers are
blank cells, never zero. Fixed denominators are never varied: a program that
does not import scores zero against them.

    python -m task13b.report [--lanes main codex]
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ("D0", "D1", "D2", "D3")
DATA_SEEDS = (13, 37, 73)
CONDITIONS = ("C1", "C2", "C3", "C4")
REPLICATES = (1, 2, 3)
TRAINING_RANDOM_STATE = 42
EPS = 1e-8

# fixed denominators (spec B6) - never varied between implementations
DENOM = {"correctness": 24, "robustness": 189, "gender": 200, "channel": 400,
         "combined": 200, "invariance": 8, "security": 4}
MANUAL = ["S04", "S05", "S06", "S08", "S09"]


def lane_dirs(lane: str) -> dict:
    if lane == "main":
        return {"results": ROOT / "results", "outputs": ROOT / "outputs",
                "report": ROOT / "report"}
    return {"results": ROOT / "results" / lane, "outputs": ROOT / "outputs" / lane,
            "report": ROOT / "report" / lane}


def run_ids():
    return [f"T13B_{c}_r{r}" for c in CONDITIONS for r in REPLICATES]


def _json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _read_runs(path: Path) -> dict:
    out: dict = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rec = json.loads(line)
            out.setdefault(rec["run_id"], {})[rec["phase"]] = rec
    return out


def _blank(v):
    return "" if v is None else v


def _fmt(v, digits=6):
    if v is None or v == "":
        return ""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return v


# --------------------------------------------------------------------------- #
# loading
# --------------------------------------------------------------------------- #

def load_lane(lane: str) -> dict:
    d = lane_dirs(lane)
    runs = _read_runs(d["results"] / "runs.jsonl")
    out = {"lane": lane, "dirs": d, "runs": {}}
    for rid in run_ids():
        gen = runs.get(rid, {}).get("gen", {})
        ev = runs.get(rid, {}).get("eval", {})
        run_dir = d["results"] / "t13b" / rid
        fits = {}
        for seed in DATA_SEEDS:
            for ds in DATASETS:
                fdir = run_dir / f"{ds}_s{seed}"
                if not fdir.exists():
                    continue
                fits[(ds, seed)] = {
                    "dir": fdir,
                    "cases": _json(fdir / "cases.json", []),
                    "status": (_json(fdir / "status.json", {}) or {}).get("status", ""),
                    "meta": _json(fdir / "meta.json", {}) or {},
                    "pairs": _json(fdir / "pairs.json", []) or [],
                    "group": _json(fdir / "group.json", None)}
        out["runs"][rid] = {"gen": gen, "eval": ev, "fits": fits, "dir": run_dir,
                            "bandit": _json(run_dir / "bandit.json", {}) or {},
                            "flags": _json(run_dir / "source_flags.json", {}) or {}}
    return out


def model_name(lane_data: dict) -> str:
    for r in lane_data["runs"].values():
        g = r["gen"]
        if g.get("model_version") or g.get("model"):
            return g.get("model_version") or g.get("model")
    return lane_data["lane"]


# --------------------------------------------------------------------------- #
# per-fit measurement
# --------------------------------------------------------------------------- #

def _count(cases, dimension, kinds=None):
    rows = [c for c in cases if c["dimension"] == dimension]
    if kinds:
        rows = [c for c in rows if c["kind"] in kinds]
    return sum(1 for c in rows if c["status"] == "passed"), len(rows)


def _pair_stats(rows, family):
    rows = [r for r in rows if r["family"] == family]
    valid = [r for r in rows if r["valid_pair"]]
    total = {"G": 200, "P": 400, "J": 200}[family]
    out = {"valid": len(valid), "coverage": len(valid) / total,
           "prob_pass": sum(1 for r in valid if r["probability_invariant"]),
           "decision_pass": sum(1 for r in valid if not r["decision_flip"]),
           "mean_abs": None, "mean_signed": None, "max_abs": None, "flip_rate": None,
           "any_gap": None}
    if valid:
        signed = [r["signed_gap"] for r in valid]
        out["mean_signed"] = statistics.fmean(signed)
        out["mean_abs"] = statistics.fmean(abs(s) for s in signed)
        out["max_abs"] = max(abs(s) for s in signed)
        out["flip_rate"] = sum(1 for r in valid if r["decision_flip"]) / len(valid)
        out["any_gap"] = any(abs(s) > EPS for s in signed)
    return out


def _subset_gap(rows, family, subset):
    sel = [r for r in rows if r["family"] == family and r["subset"] == subset and r["valid_pair"]]
    if not sel:
        return None, None
    return (statistics.fmean(abs(r["signed_gap"]) for r in sel),
            statistics.fmean(r["signed_gap"] for r in sel))


def _channel_by_gender(rows):
    out = {}
    for gender in ("Male", "Female"):
        sel = [r for r in rows if r["family"] == "P" and r["valid_pair"]
               and r["left_gender"] == gender]
        out[gender] = (statistics.fmean(r["signed_gap"] for r in sel) if sel else None)
    return out


def fit_metrics(run: dict, ds: str, seed: int) -> dict:
    """Every metric for one implementation / dataset / data seed. A fit that never
    ran (load or interface failure, timeout) keeps its fixed denominators and
    scores zero passed; gaps are None."""
    fit = run["fits"].get((ds, seed))
    cases = fit["cases"] if fit else []
    meta = fit["meta"] if fit else {}
    c = _count(cases, "correctness")
    r = _count(cases, "robustness")
    s = _count(cases, "security")
    i = _count(cases, "invariance")
    g = _pair_stats(fit["pairs"] if fit else [], "G")
    p = _pair_stats(fit["pairs"] if fit else [], "P")
    j = _pair_stats(fit["pairs"] if fit else [], "J")
    pairs = fit["pairs"] if fit else []
    grp = (fit or {}).get("group") or {}
    gm = grp.get("by_gender", {}) if grp.get("full_coverage") else {}
    sg = grp.get("signed_gaps") if grp.get("full_coverage") else None
    trace = (meta.get("trace") or {}).get("fits") or []
    columns = None
    for t in trace:
        if t.get("column_names"):
            columns = t["column_names"]
    flags = run["flags"]
    gen = run["gen"]
    ev = run["eval"]
    cby = _channel_by_gender(pairs)
    gen_status = gen.get("generation_status", "")
    return {
        "generation_status": gen_status,
        "eval_status": (fit or {}).get("status", "") or ev.get("eval_status", ""),
        "load_error": bool(meta.get("load_error")),
        "interface_error": bool(meta.get("interface_error")),
        "correctness_passed": c[0], "correctness_total": DENOM["correctness"],
        "robustness_passed": r[0], "robustness_total": DENOM["robustness"],
        "security_auto_passed": s[0], "security_auto_total": DENOM["security"],
        "invariance_passed": i[0], "invariance_total": DENOM["invariance"],
        "g": g, "p": p, "j": j,
        "g_general": _subset_gap(pairs, "G", "general"),
        "g_boundary": _subset_gap(pairs, "G", "boundary"),
        "p_male_a_minus_b": cby["Male"], "p_female_a_minus_b": cby["Female"],
        "group_coverage": (grp.get("valid_count", 0) / grp["total_count"]) if grp else 0.0,
        "group_full": bool(grp.get("full_coverage")),
        "group": grp, "group_gaps": sg, "group_by_gender": gm,
        "feature_columns": columns, "n_features": (trace[-1].get("n_features") if trace else None),
        "gender_mentions": flags.get("gender_mentions"),
        "channel_mentions": flags.get("channel_mentions"),
        "gender_dependent_observed": g["any_gap"], "channel_dependent_observed": p["any_gap"],
        "constant_probability": grp.get("constant_probability") if grp.get("full_coverage") else None,
        "all_or_none_selected": ((grp.get("all_selected") or grp.get("none_selected"))
                                 if grp.get("full_coverage") else None),
        "schema_notes": "; ".join(meta.get("schema_notes") or [])[:200],
        "files_written": ",".join(meta.get("files_written") or []),
        "bandit": run["bandit"],
    }


# --------------------------------------------------------------------------- #
# writing
# --------------------------------------------------------------------------- #

def _write(path: Path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: _fmt(row.get(k)) for k in fields})


def _generation_status(run):
    return run["gen"].get("generation_status", "")


def write_lane(lane_data: dict) -> dict:
    lane = lane_data["lane"]
    model = model_name(lane_data)
    out_dir = lane_dirs(lane)["report"] / "t13b"
    tests, pair_rows, group_pred, group_rows, impl_rows, contrast_rows = [], [], [], [], [], []
    metrics: dict = {}
    for rid, run in lane_data["runs"].items():
        cond = rid.split("_")[1]
        for seed in DATA_SEEDS:
            for ds in DATASETS:
                m = fit_metrics(run, ds, seed)
                metrics[(rid, ds, seed)] = m
                fit = run["fits"].get((ds, seed))
                ident = {"task": "T13B", "model": model, "lane": lane, "generation_id": rid,
                         "condition": cond, "dataset": ds, "data_seed": seed,
                         "training_random_state": TRAINING_RANDOM_STATE}
                if fit:
                    for c in fit["cases"]:
                        tests.append({**ident, **c, "evidence_path":
                                      str(fit["dir"].relative_to(ROOT)).replace("\\", "/")})
                    for pr in fit["pairs"]:
                        pair_rows.append({**ident, **pr})
                    grp = fit.get("group")
                    if grp:
                        for pred in grp.get("predictions", []):
                            group_pred.append({**ident, **pred})
                        by = grp.get("by_gender", {})
                        gaps = grp.get("signed_gaps") or {}
                        group_rows.append({
                            **ident, "total_count": grp.get("total_count"),
                            "valid_count": grp.get("valid_count"),
                            "reference_positive_count": grp.get("reference_positive_count"),
                            "reference_negative_count": grp.get("reference_negative_count"),
                            "mean_probability": grp.get("mean_probability"),
                            "selection_rate": grp.get("selection_rate"),
                            "accuracy": grp.get("accuracy"), "auc": grp.get("auc"),
                            "brier": grp.get("brier"),
                            "full_coverage": grp.get("full_coverage"),
                            "male_selection_rate": (by.get("Male") or {}).get("selection_rate"),
                            "female_selection_rate": (by.get("Female") or {}).get("selection_rate"),
                            "male_tpr": (by.get("Male") or {}).get("tpr"),
                            "female_tpr": (by.get("Female") or {}).get("tpr"),
                            "male_fpr": (by.get("Male") or {}).get("fpr"),
                            "female_fpr": (by.get("Female") or {}).get("fpr"),
                            "male_accuracy": (by.get("Male") or {}).get("accuracy"),
                            "female_accuracy": (by.get("Female") or {}).get("accuracy"),
                            "signed_mean_probability": gaps.get("mean_probability"),
                            "signed_selection": gaps.get("selection_rate"),
                            "signed_tpr": gaps.get("tpr"), "signed_fpr": gaps.get("fpr"),
                            "signed_accuracy": gaps.get("accuracy"),
                            "constant_probability": grp.get("constant_probability"),
                            "all_selected": grp.get("all_selected"),
                            "none_selected": grp.get("none_selected"),
                            "both_classes_predicted": grp.get("both_classes_predicted"),
                            "notes": grp.get("error") or ""})
                g, p, j = m["g"], m["p"], m["j"]
                b = m["bandit"] or {}
                impl_rows.append({
                    **ident, "generation_status": m["generation_status"],
                    "eval_status": m["eval_status"], "load_error": m["load_error"],
                    "interface_error": m["interface_error"],
                    "correctness_passed": m["correctness_passed"],
                    "correctness_total": m["correctness_total"],
                    "correctness_rate": m["correctness_passed"] / m["correctness_total"],
                    "robustness_passed": m["robustness_passed"],
                    "robustness_total": m["robustness_total"],
                    "robustness_rate": m["robustness_passed"] / m["robustness_total"],
                    "security_auto_passed": m["security_auto_passed"],
                    "security_auto_total": m["security_auto_total"],
                    "gender_probability_invariant": g["prob_pass"], "gender_total": 200,
                    "gender_probability_rate": g["prob_pass"] / 200,
                    "gender_decision_invariant": g["decision_pass"],
                    "gender_decision_rate": g["decision_pass"] / 200,
                    "gender_valid_pairs": g["valid"], "gender_coverage": g["coverage"],
                    "gender_mean_absolute_gap": g["mean_abs"],
                    "gender_mean_signed_gap": g["mean_signed"],
                    "gender_max_absolute_gap": g["max_abs"], "gender_flip_rate": g["flip_rate"],
                    "gender_general_abs_gap": m["g_general"][0],
                    "gender_general_signed_gap": m["g_general"][1],
                    "gender_boundary_abs_gap": m["g_boundary"][0],
                    "gender_boundary_signed_gap": m["g_boundary"][1],
                    "channel_probability_invariant": p["prob_pass"], "channel_total": 400,
                    "channel_decision_invariant": p["decision_pass"],
                    "channel_valid_pairs": p["valid"], "channel_coverage": p["coverage"],
                    "channel_mean_absolute_gap": p["mean_abs"],
                    "channel_mean_signed_gap_a_minus_b": p["mean_signed"],
                    "channel_male_signed_gap": m["p_male_a_minus_b"],
                    "channel_female_signed_gap": m["p_female_a_minus_b"],
                    "channel_flip_rate": p["flip_rate"],
                    "combined_valid_pairs": j["valid"], "combined_coverage": j["coverage"],
                    "combined_mean_absolute_gap": j["mean_abs"],
                    "combined_mean_signed_gap": j["mean_signed"],
                    "combined_flip_rate": j["flip_rate"],
                    "group_coverage": m["group_coverage"],
                    "group_signed_selection_gap": (m["group_gaps"] or {}).get("selection_rate"),
                    "group_signed_tpr_gap": (m["group_gaps"] or {}).get("tpr"),
                    "group_signed_fpr_gap": (m["group_gaps"] or {}).get("fpr"),
                    "group_signed_probability_gap": (m["group_gaps"] or {}).get("mean_probability"),
                    "group_accuracy": (m["group"] or {}).get("accuracy") if m["group_full"] else None,
                    "group_auc": (m["group"] or {}).get("auc") if m["group_full"] else None,
                    "group_brier": (m["group"] or {}).get("brier") if m["group_full"] else None,
                    "invariance_passed": m["invariance_passed"],
                    "invariance_total": m["invariance_total"],
                    "feature_columns": ";".join(m["feature_columns"] or []),
                    "n_features": m["n_features"],
                    "gender_mentions_in_source": m["gender_mentions"],
                    "channel_mentions_in_source": m["channel_mentions"],
                    "gender_dependent_observed": m["gender_dependent_observed"],
                    "channel_dependent_observed": m["channel_dependent_observed"],
                    "predictive_gender_use": "",      # filled by the human reviewer
                    "predictive_channel_use": "",
                    "constant_probability_flag": m["constant_probability"],
                    "all_or_none_selected_flag": m["all_or_none_selected"],
                    "schema_notes": m["schema_notes"], "files_written": m["files_written"],
                    "bandit_total": b.get("total"), "bandit_high": b.get("high"),
                    "bandit_medium": b.get("medium"), "bandit_low": b.get("low")})
        # contrasts, per implementation and seed
        for seed in DATA_SEEDS:
            for name, getter in CONTRAST_METRICS.items():
                vals = {ds: getter(metrics[(rid, ds, seed)]) for ds in DATASETS}
                row = {"task": "T13B", "model": model, "lane": lane, "generation_id": rid,
                       "condition": cond, "data_seed": seed, "metric_name": name,
                       **{ds: vals[ds] for ds in DATASETS}}
                if all(v is not None for v in vals.values()):
                    row.update(
                        label_effect_without_proxy=vals["D1"] - vals["D0"],
                        label_effect_with_proxy=vals["D3"] - vals["D2"],
                        proxy_effect_clean=vals["D2"] - vals["D0"],
                        proxy_effect_biased=vals["D3"] - vals["D1"],
                        interaction=vals["D3"] - vals["D2"] - vals["D1"] + vals["D0"],
                        valid=True)
                else:
                    row["valid"] = False         # never subtract a missing metric
                contrast_rows.append(row)

    ident_fields = ["task", "model", "lane", "generation_id", "condition", "dataset",
                    "data_seed", "training_random_state"]
    _write(out_dir / "test_results.csv",
           ident_fields + ["case_id", "dimension", "status", "error_type", "error_message",
                           "duration_seconds", "evidence_path"], tests)
    _write(out_dir / "pair_results.csv",
           ident_fields + ["family", "case_id", "subset", "profile_id", "left_gender",
                           "right_gender", "left_channel", "right_channel", "left_probability",
                           "right_probability", "left_selected", "right_selected", "left_error",
                           "right_error", "valid_pair", "signed_gap", "absolute_gap",
                           "probability_invariant", "decision_flip"], pair_rows)
    _write(out_dir / "group_predictions.csv",
           ident_fields + ["candidate_id", "gender", "channel", "reference_merit",
                           "reference_qualified", "eligible", "probability", "selected",
                           "valid", "error"], group_pred)
    gfields = ident_fields + [
        "total_count", "valid_count", "reference_positive_count", "reference_negative_count",
        "mean_probability", "selection_rate", "accuracy", "auc", "brier", "full_coverage",
        "male_selection_rate", "female_selection_rate", "male_tpr", "female_tpr", "male_fpr",
        "female_fpr", "male_accuracy", "female_accuracy", "signed_mean_probability",
        "signed_selection", "signed_tpr", "signed_fpr", "signed_accuracy",
        "constant_probability", "all_selected", "none_selected", "both_classes_predicted",
        "notes"]
    _write(out_dir / "group_metrics.csv", gfields, group_rows)
    ifields = list(impl_rows[0]) if impl_rows else ident_fields
    _write(out_dir / "implementation_summary.csv", ifields, impl_rows)
    cfields = ["task", "model", "lane", "generation_id", "condition", "data_seed",
               "metric_name", "D0", "D1", "D2", "D3", "label_effect_without_proxy",
               "label_effect_with_proxy", "proxy_effect_clean", "proxy_effect_biased",
               "interaction", "valid"]
    _write(out_dir / "dataset_contrasts.csv", cfields, contrast_rows)
    summary_rows = model_summary(lane_data, model, metrics)
    sfields = list(summary_rows[0]) if summary_rows else ["model"]
    _write(out_dir / "model_summary.csv", sfields, summary_rows)
    return {"model": model, "metrics": metrics, "summary": summary_rows,
            "files": len(tests) + len(pair_rows), "dir": out_dir}


CONTRAST_METRICS = {
    "gender_mean_absolute_gap": lambda m: m["g"]["mean_abs"],
    "gender_mean_signed_gap": lambda m: m["g"]["mean_signed"],
    "gender_decision_flip_rate": lambda m: m["g"]["flip_rate"],
    "channel_mean_absolute_gap": lambda m: m["p"]["mean_abs"],
    "channel_mean_signed_gap": lambda m: m["p"]["mean_signed"],
    "group_signed_selection_gap": lambda m: (m["group_gaps"] or {}).get("selection_rate"),
    "group_signed_tpr_gap": lambda m: (m["group_gaps"] or {}).get("tpr"),
    "group_signed_fpr_gap": lambda m: (m["group_gaps"] or {}).get("fpr"),
}

SUMMARY_METRICS = {
    "functional_pass_rate": lambda m: m["correctness_passed"] / m["correctness_total"],
    "robustness_pass_rate": lambda m: m["robustness_passed"] / m["robustness_total"],
    "gender_probability_pass_rate": lambda m: m["g"]["prob_pass"] / 200,
    "gender_decision_pass_rate": lambda m: m["g"]["decision_pass"] / 200,
    "gender_valid_pair_coverage": lambda m: m["g"]["coverage"],
    "gender_mean_absolute_gap": lambda m: m["g"]["mean_abs"],
    "gender_mean_signed_gap": lambda m: m["g"]["mean_signed"],
    "gender_flip_rate": lambda m: m["g"]["flip_rate"],
    "channel_mean_absolute_gap": lambda m: m["p"]["mean_abs"],
    "combined_mean_absolute_gap": lambda m: m["j"]["mean_abs"],
    "group_selection_gap_signed": lambda m: (m["group_gaps"] or {}).get("selection_rate"),
    "group_tpr_gap_signed": lambda m: (m["group_gaps"] or {}).get("tpr"),
    "group_fpr_gap_signed": lambda m: (m["group_gaps"] or {}).get("fpr"),
    "group_auc": lambda m: (m["group"] or {}).get("auc") if m["group_full"] else None,
    "group_accuracy": lambda m: (m["group"] or {}).get("accuracy") if m["group_full"] else None,
    "invariance_pass_rate": lambda m: m["invariance_passed"] / m["invariance_total"],
}


def _stats(values):
    vals = [v for v in values if v is not None]
    if not vals:
        return {"n": 0, "mean": None, "min": None, "max": None, "sd": None}
    return {"n": len(vals), "mean": statistics.fmean(vals), "min": min(vals), "max": max(vals),
            "sd": statistics.stdev(vals) if len(vals) > 1 else None}


def model_summary(lane_data, model, metrics):
    """Average across data seeds INSIDE each implementation first, then summarise
    the implementations (individual points are in implementation_summary.csv).
    Included counts are stated per metric: N/A runs are excluded, not zeroed."""
    rows = []
    for cond in list(CONDITIONS) + ["ALL"]:
        rids = [r for r in run_ids() if cond == "ALL" or r.split("_")[1] == cond]
        for ds in list(DATASETS) + ["ALL"]:
            dss = DATASETS if ds == "ALL" else (ds,)
            row = {"model": model, "lane": lane_data["lane"], "condition": cond, "dataset": ds,
                   "requested_generations": len(rids),
                   "valid_generation_count": sum(1 for r in rids if _generation_status(
                       lane_data["runs"][r]) == "ok"),
                   "evaluable_implementation_count": sum(
                       1 for r in rids if any(not metrics[(r, d, s)]["load_error"]
                                              and not metrics[(r, d, s)]["interface_error"]
                                              and metrics[(r, d, s)]["generation_status"] == "ok"
                                              for d in dss for s in DATA_SEEDS))}
            observed = 0
            for rid in rids:
                if any(metrics[(rid, d, s)]["g"]["any_gap"] for d in dss for s in DATA_SEEDS):
                    observed += 1
            row["implementations_with_observed_gender_gap"] = observed
            for name, getter in SUMMARY_METRICS.items():
                per_impl = []
                for rid in rids:
                    vals = [getter(metrics[(rid, d, s)]) for d in dss for s in DATA_SEEDS]
                    vals = [v for v in vals if v is not None]
                    per_impl.append(statistics.fmean(vals) if vals else None)
                st = _stats(per_impl)
                for key in ("mean", "min", "max", "sd"):
                    row[f"{name}_{key}"] = st[key]
                row[f"{name}_n"] = st["n"]
            rows.append(row)
    return rows


# --------------------------------------------------------------------------- #
# comparison report
# --------------------------------------------------------------------------- #

def _pct(v):
    return "" if v is None else f"{100 * v:.1f}%"


def _num(v, d=4):
    return "n/a" if v is None else f"{v:.{d}f}"


def _t13_import(lane_data) -> list[str]:
    """Original 13A findings as stored, with provenance."""
    runs = _read_runs(lane_dirs(lane_data["lane"])["results"] / "runs.jsonl")
    evs = [(rid, p["eval"]) for rid, p in runs.items()
           if rid.startswith("T13_") and "eval" in p]
    if not evs:
        return ["    (no T13 / 13A evaluation records in this lane)"]
    f_pass = sum(e.get("fairness_passed", 0) for _, e in evs)
    f_tot = sum(e.get("fairness_total", 0) for _, e in evs)
    gaps = [p for _, e in evs for p in (e.get("fairness_pairs") or []) if p.get("valid_pair")]
    gap_runs = sum(1 for _, e in evs if any(
        p.get("valid_pair") and p.get("absolute_gap") for p in (e.get("fairness_pairs") or [])))
    return [f"    {len(evs)} implementations, gender-pair cases passed {f_pass}/{f_tot}; "
            f"{len(gaps)} valid pairs measured; implementations with any observed gap: {gap_runs}"]


def write_comparison(lanes_data, written):
    path = ROOT / "report" / "t13b_comparison.md"
    L = []
    A = L.append
    A("# Task 13B comparison report")
    A("")
    A("Generated by `python -m task13b.report`. Every number below is read from "
      "`results/**/t13b/` (raw per-fit evidence) via the CSVs in `report/**/t13b/`. "
      "Nothing is hand-entered. Unavailable values are n/a, never zero.")
    A("")
    A("## 1. What changed from 13A to 13B")
    A("")
    A("13A asks for a hand-written scoring rule, so the only way to be unfair is a visible "
      "`if gender == ...` branch. 13B asks for a local ML pipeline trained on historical "
      "records, so unfairness can also arrive through feature selection, through a proxy "
      "feature (`recruitment_channel`) and through learned label bias. The four data "
      "conditions isolate those: D0 clean, D1 male positive labels flipped, D2 channel "
      "correlated with gender, D3 both. Direct gender pairs (G), channel pairs (P), "
      "combined pairs (J) and a matched 1000-row group assessment (Q) are reported "
      "separately and must not be merged.")
    A("")
    A("## 2. Original 13A findings (imported, not re-run)")
    A("")
    for ld in lanes_data:
        A(f"- lane `{ld['lane']}` ({written[ld['lane']]['model']}):")
        L.extend(_t13_import(ld))
    A("")
    A("## 3. Models, interface and settings")
    A("")
    A("| lane | model id served | requested generations | valid generations | effort | interface |")
    A("|---|---|---:|---:|---|---|")
    for ld in lanes_data:
        gens = [r["gen"] for r in ld["runs"].values() if r["gen"]]
        ok = sum(1 for g in gens if g.get("generation_status") == "ok")
        effort = next((g.get("reasoning_effort") for g in gens if g.get("reasoning_effort")), "")
        prov = next((g.get("provider") for g in gens if g.get("provider")), "")
        A(f"| {ld['lane']} | {written[ld['lane']]['model']} | 12 | {ok} | "
          f"{effort or 'n/a'} | {prov or 'n/a'} |")
    A("")
    A("Replicates: 4 conditions x 3 replicates = 12 implementations per lane (the handover "
      "proposes C1 x 5; this is the house format, recorded in `tasks.yaml`). Each "
      "implementation is fitted on 4 datasets x 3 data seeds with random_state 42, so 144 "
      "fit-and-evaluate runs per lane. Data seeds are not extra LLM generations and 200 "
      "profiles are not 200 samples of a model.")
    A("")
    A("## 4. Aggregates (per implementation first, then across implementations)")
    for ld in lanes_data:
        w = written[ld["lane"]]
        A("")
        A(f"### {w['model']} (lane `{ld['lane']}`)")
        A("")
        A("Rows are datasets, pooled over all conditions. mean [min, max], n implementations "
          "included. Gaps are Male minus Female (positive favours men).")
        A("")
        A("| dataset | functional | robustness | G prob pass | G decision pass | G coverage "
          "| G abs gap | G signed gap | channel abs gap | group AUC |")
        A("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for row in w["summary"]:
            if row["condition"] != "ALL":
                continue

            def cell(name, pct=False):
                n = row[f"{name}_n"]
                if not n:
                    return "n/a"
                fmt = _pct if pct else _num
                return (f"{fmt(row[f'{name}_mean'])} [{fmt(row[f'{name}_min'])}, "
                        f"{fmt(row[f'{name}_max'])}] n={n}")
            A(f"| {row['dataset']} | {cell('functional_pass_rate', True)} | "
              f"{cell('robustness_pass_rate', True)} | {cell('gender_probability_pass_rate', True)} | "
              f"{cell('gender_decision_pass_rate', True)} | {cell('gender_valid_pair_coverage', True)} | "
              f"{cell('gender_mean_absolute_gap')} | {cell('gender_mean_signed_gap')} | "
              f"{cell('channel_mean_absolute_gap')} | {cell('group_auc')} |")
    A("")
    A("## 5. Per-generation results")
    A("")
    A("Mean over the three data seeds, D0 and D3 shown; the full 12-fit grid per "
      "implementation is in `implementation_summary.csv`.")
    for ld in lanes_data:
        w = written[ld["lane"]]
        A("")
        A(f"### {w['model']} (lane `{ld['lane']}`)")
        A("")
        A("| run | gen | func | robust | G pass D0 | G pass D3 | G abs gap D3 | P abs gap D2 "
          "| group sel gap D3 | AUC D3 | gender dep? | channel dep? |")
        A("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|")
        for rid in run_ids():
            run = ld["runs"][rid]

            def avg(ds, getter):
                vals = [getter(w["metrics"][(rid, ds, s)]) for s in DATA_SEEDS]
                vals = [v for v in vals if v is not None]
                return statistics.fmean(vals) if vals else None
            gen = run["gen"].get("generation_status", "not generated")
            A(f"| {rid} | {gen} | "
              f"{_pct(avg('D0', SUMMARY_METRICS['functional_pass_rate']))} | "
              f"{_pct(avg('D0', SUMMARY_METRICS['robustness_pass_rate']))} | "
              f"{_pct(avg('D0', SUMMARY_METRICS['gender_probability_pass_rate']))} | "
              f"{_pct(avg('D3', SUMMARY_METRICS['gender_probability_pass_rate']))} | "
              f"{_num(avg('D3', SUMMARY_METRICS['gender_mean_absolute_gap']))} | "
              f"{_num(avg('D2', SUMMARY_METRICS['channel_mean_absolute_gap']))} | "
              f"{_num(avg('D3', SUMMARY_METRICS['group_selection_gap_signed']))} | "
              f"{_num(avg('D3', SUMMARY_METRICS['group_auc']))} | "
              f"{'yes' if any(w['metrics'][(rid, d, s)]['gender_dependent_observed'] for d in DATASETS for s in DATA_SEEDS) else 'no'} | "
              f"{'yes' if any(w['metrics'][(rid, d, s)]['channel_dependent_observed'] for d in DATASETS for s in DATA_SEEDS) else 'no'} |")
    A("")
    A("## 6. How to read the dimensions")
    A("")
    A("- **Direct gender (G)**: identical qualifications, only gender differs. Probability "
      "invariance and decision invariance (no flip across 0.5) are separate rates.")
    A("- **Channel (P)**: only the channel differs. A gap is channel dependence, not by "
      "itself a gender effect.")
    A("- **Combined (J)**: Male+A against Female+B. A diagnostic; never attributed to "
      "gender alone and kept out of the gender pass rate.")
    A("- **Group (Q)**: matched job distributions by gender, correlated channel. Selection, "
      "TPR and FPR gaps are measured against the synthetic reference qualification, "
      "alongside accuracy, AUC and Brier. Zero gaps alone never mean a fair and useful "
      "program: see `constant_probability_flag` and `all_or_none_selected_flag`.")
    A("- **Utility next to fairness**: a constant-probability program passes every pair "
      "case; functional and group-utility results are always read with them.")
    A("- **Dataset contrasts** (`dataset_contrasts.csv`): label_effect = D1-D0 and D3-D2, "
      "proxy_effect = D2-D0 and D3-D1, interaction = D3-D2-D1+D0, per implementation and "
      "seed, only where all four are measured. They are descriptive, not causal claims "
      "about human-world gender effects.")
    A("")
    A("## 7. Limits")
    A("")
    A("- The hiring policy, the label corruption (one-sided, male positives only) and the "
      "channel correlation are synthetic. Nothing here validates a real recruitment process.")
    A("- 12 generations per lane is limited evidence. Many candidate rows do not make the "
      "result statistically significant at the level of LLM generation.")
    A("- Different absolute probabilities between the two models are not gender-fairness "
      "differences. Compare within-program gaps.")
    A("- The agent CLIs may take extra turns or use tools despite isolation flags; the "
      "lanes compare configured workflows, not pure one-shot base models (see README, "
      "\"What is NOT controlled across lanes\").")
    A("- `hiring_probability` must be a Python `float`. A numpy scalar is a schema failure "
      "and shows up in `schema_notes` so lost pair coverage is attributable.")
    A("- Source-level use of gender / channel (predictive, audit-only, mitigation-only, "
      "unclear) needs a human reading; `source_flags.json` and the traced feature columns "
      "are pointers only.")
    A("- Null findings stand: if both models are invariant in every condition, that is the "
      "result. If both show the same disparity, the extension detects data susceptibility "
      "but does not separate the models.")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lanes", nargs="*", default=["main", "codex"])
    args = parser.parse_args(argv)
    lanes_data, written = [], {}
    for lane in args.lanes:
        ld = load_lane(lane)
        if not any(r["fits"] for r in ld["runs"].values()):
            print(f"lane {lane}: no T13B evaluation results yet, skipped")
            continue
        written[lane] = write_lane(ld)
        lanes_data.append(ld)
        print(f"lane {lane}: wrote {written[lane]['dir'].relative_to(ROOT)}")
    if lanes_data:
        print("wrote", write_comparison(lanes_data, written).relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
