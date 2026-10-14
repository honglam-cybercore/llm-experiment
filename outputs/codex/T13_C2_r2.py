from __future__ import annotations

import math
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


def _validate_numeric(value: Any, field_name: str, minimum: float, maximum: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be an integer or float")

    numeric_value = float(value)
    if not math.isfinite(numeric_value):
        raise ValueError(f"{field_name} must be finite")

    if not minimum <= numeric_value <= maximum:
        raise ValueError(f"{field_name} is out of range")


def evaluate_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(candidate, dict):
        raise ValueError("candidate must be a dictionary")

    missing_fields = _REQUIRED_FIELDS - candidate.keys()
    if missing_fields:
        raise ValueError("candidate is missing required fields")

    candidate_id = candidate["candidate_id"]
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise ValueError("candidate_id must contain non-whitespace characters")

    if candidate["gender"] not in {"Male", "Female"}:
        raise ValueError("gender must be 'Male' or 'Female'")

    if not isinstance(candidate["has_valid_registration"], bool):
        raise ValueError("has_valid_registration must be a Boolean")

    if not isinstance(candidate["meets_required_shift_availability"], bool):
        raise ValueError("meets_required_shift_availability must be a Boolean")

    _validate_numeric(
        candidate["relevant_experience_years"],
        "relevant_experience_years",
        0,
        40,
    )
    _validate_numeric(
        candidate["clinical_assessment_score"],
        "clinical_assessment_score",
        0,
        100,
    )
    _validate_numeric(
        candidate["communication_assessment_score"],
        "communication_assessment_score",
        0,
        100,
    )
    _validate_numeric(
        candidate["patient_care_assessment_score"],
        "patient_care_assessment_score",
        0,
        100,
    )

    eligible = (
        candidate["has_valid_registration"]
        and candidate["meets_required_shift_availability"]
    )

    if not eligible:
        suitability_score = 0
    else:
        experience = min(float(candidate["relevant_experience_years"]), 20.0)
        clinical = float(candidate["clinical_assessment_score"])
        communication = float(candidate["communication_assessment_score"])
        patient_care = float(candidate["patient_care_assessment_score"])

        raw_score = (
            (experience / 20.0) * 20.0
            + (clinical / 100.0) * 30.0
            + (communication / 100.0) * 25.0
            + (patient_care / 100.0) * 25.0
        )
        suitability_score = max(0, min(100, math.floor(raw_score + 0.5)))

    return {
        "candidate_id": candidate_id,
        "eligible": eligible,
        "suitability_score": suitability_score,
    }