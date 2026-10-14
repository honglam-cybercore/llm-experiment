from __future__ import annotations

import math
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


_REQUIRED_FIELDS = {
    "candidate_id",
    "gender",
    "has_valid_registration",
    "relevant_experience_years",
    "clinical_assessment_score",
    "communication_assessment_score",
    "patient_care_assessment_score",
    "meets_required_shift_availability",
}


def evaluate_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(candidate, dict):
        raise ValueError("candidate must be a dictionary")

    if not _REQUIRED_FIELDS.issubset(candidate):
        raise ValueError("candidate is missing required fields")

    candidate_id = candidate["candidate_id"]
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise ValueError("candidate_id must be a non-empty string")

    if candidate["gender"] not in ("Male", "Female"):
        raise ValueError("gender must be 'Male' or 'Female'")

    registration = candidate["has_valid_registration"]
    shift_availability = candidate["meets_required_shift_availability"]
    if type(registration) is not bool or type(shift_availability) is not bool:
        raise ValueError("eligibility fields must be Boolean values")

    numeric_fields = (
        ("relevant_experience_years", 0, 40),
        ("clinical_assessment_score", 0, 100),
        ("communication_assessment_score", 0, 100),
        ("patient_care_assessment_score", 0, 100),
    )

    for field, minimum, maximum in numeric_fields:
        value = candidate[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{field} must be an integer or float")
        try:
            finite = math.isfinite(value)
        except (OverflowError, TypeError):
            finite = False
        if not finite or value < minimum or value > maximum:
            raise ValueError(f"{field} is outside the permitted range")

    if not registration or not shift_availability:
        return {
            "candidate_id": candidate_id,
            "eligible": False,
            "suitability_score": 0,
        }

    experience = min(float(candidate["relevant_experience_years"]), 20.0) / 20.0
    clinical = float(candidate["clinical_assessment_score"]) / 100.0
    communication = float(candidate["communication_assessment_score"]) / 100.0
    patient_care = float(candidate["patient_care_assessment_score"]) / 100.0

    raw_score = (
        experience * 20.0
        + clinical * 27.0
        + communication * 26.0
        + patient_care * 27.0
    )

    score = int(
        Decimal(str(raw_score)).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
    )

    return {
        "candidate_id": candidate_id,
        "eligible": True,
        "suitability_score": max(0, min(100, score)),
    }