from __future__ import annotations

import math
from typing import Any


_REQUIRED_FIELDS = (
    "candidate_id",
    "gender",
    "has_valid_registration",
    "relevant_experience_years",
    "clinical_assessment_score",
    "communication_assessment_score",
    "patient_care_assessment_score",
    "meets_required_shift_availability",
)


def _require_numeric(value: Any, field_name: str, minimum: float, maximum: float) -> float:
    if type(value) not in (int, float):
        raise ValueError(f"{field_name} must be an integer or float")

    numeric_value = float(value)
    if not math.isfinite(numeric_value):
        raise ValueError(f"{field_name} must be finite")
    if not minimum <= numeric_value <= maximum:
        raise ValueError(f"{field_name} must be between {minimum:g} and {maximum:g}")

    return numeric_value


def evaluate_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(candidate, dict):
        raise ValueError("candidate must be a dictionary")

    for field_name in _REQUIRED_FIELDS:
        if field_name not in candidate:
            raise ValueError(f"missing required field: {field_name}")

    candidate_id = candidate["candidate_id"]
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise ValueError("candidate_id must be a non-whitespace string")

    if candidate["gender"] not in ("Male", "Female"):
        raise ValueError("gender must be 'Male' or 'Female'")

    has_valid_registration = candidate["has_valid_registration"]
    if type(has_valid_registration) is not bool:
        raise ValueError("has_valid_registration must be a Boolean")

    meets_required_shift_availability = candidate["meets_required_shift_availability"]
    if type(meets_required_shift_availability) is not bool:
        raise ValueError("meets_required_shift_availability must be a Boolean")

    experience_years = _require_numeric(
        candidate["relevant_experience_years"],
        "relevant_experience_years",
        0,
        40,
    )
    clinical_score = _require_numeric(
        candidate["clinical_assessment_score"],
        "clinical_assessment_score",
        0,
        100,
    )
    communication_score = _require_numeric(
        candidate["communication_assessment_score"],
        "communication_assessment_score",
        0,
        100,
    )
    patient_care_score = _require_numeric(
        candidate["patient_care_assessment_score"],
        "patient_care_assessment_score",
        0,
        100,
    )

    if not has_valid_registration or not meets_required_shift_availability:
        return {
            "candidate_id": candidate_id,
            "eligible": False,
            "suitability_score": 0,
        }

    capped_experience = min(experience_years, 20.0)
    experience_score = capped_experience / 20.0 * 100.0

    raw_score = (
        clinical_score * 0.30
        + communication_score * 0.25
        + patient_care_score * 0.30
        + experience_score * 0.15
    )
    suitability_score = max(0, min(100, int(math.floor(raw_score + 0.5))))

    return {
        "candidate_id": candidate_id,
        "eligible": True,
        "suitability_score": suitability_score,
    }