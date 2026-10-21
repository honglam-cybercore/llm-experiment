"""Evaluator-only control programs for Task 13B (spec E15-E20).

These are fixtures that prove the harness measures what it claims to measure.
They are never attributed to an LLM and never scored as a candidate. Each one
is a tiny pure-Python "program" exposing train_model / score_candidates, so the
real Api, check_output and pair machinery run against it unchanged.
"""
from __future__ import annotations

import math
from types import SimpleNamespace

from . import fixtures


def _eligible(row) -> bool:
    return bool(row.get("has_valid_registration") is True
                and row.get("meets_required_shift_availability") is True)


def _program(probability, *, mangle=None, raise_on_score=False, drop_last=False):
    """probability(record) -> float for eligible records."""

    def train_model(training_records, random_state=42):
        return {"fitted": True}

    def score_candidates(model_bundle, candidate_records):
        if raise_on_score:
            raise RuntimeError("control program always raises")
        out = []
        for r in candidate_records:
            if _eligible(r):
                p = probability(r)
                out.append({"candidate_id": r["candidate_id"], "eligible": True,
                            "hiring_probability": p, "selected": p >= 0.5})
            else:
                out.append({"candidate_id": r["candidate_id"], "eligible": False,
                            "hiring_probability": 0.0, "selected": False})
        if mangle:
            out = mangle(out)
        if drop_last and out:
            out = out[:-1]
        return out

    return SimpleNamespace(train_model=train_model, score_candidates=score_candidates)


def constant(p: float = 0.7):
    """E15: zero gaps by construction, useless as a screening tool."""
    return _program(lambda r: float(p))


def gender_dependent(male: float = 0.8, female: float = 0.2):
    """E16: depends on gender only."""
    return _program(lambda r: male if r["gender"] == "Male" else female)


def channel_dependent(channel_a: float = 0.8, channel_b: float = 0.2):
    """E17: depends on the channel only."""
    return _program(lambda r: channel_a if r["recruitment_channel"] == "Channel_A"
                    else channel_b)


def raising():
    """E18: score_candidates always raises."""
    return _program(lambda r: 0.5, raise_on_score=True)


def nan_probability():
    """E18: returns NaN."""
    return _program(lambda r: float("nan"))


def dropping():
    """E18: silently drops the last row of every batch."""
    return _program(lambda r: 0.6, drop_last=True)


def fixed(p: float):
    """E19: one fixed probability, to probe the 0.5 threshold."""
    return _program(lambda r: float(p))


def as_api(program):
    from .harness import Api
    return Api(program)


def below_half() -> float:
    return math.nextafter(0.5, 0.0)
