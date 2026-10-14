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


def evaluate_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(candidate, dict):
        raise ValueError("candidate must be a dictionary")

    for field in _REQUIRED_FIELDS:
        if field not in candidate:
            raise ValueError(f"missing required field: {field}")

    candidate_id = candidate["candidate_id"]
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise ValueError("candidate_id must be a non-whitespace string")

    if candidate["gender"] not in {"Male", "Female"}:
        raise ValueError("gender must be 'Male' or 'Female'")

    for field in (
        "has_valid_registration",
        "meets_required_shift_availability",
    ):
        if type(candidate[field]) is not bool:
            raise ValueError(f"{field} must be a Boolean")

    numeric_fields = (
        "relevant_experience_years",
        "clinical_assessment_score",
        "communication_assessment_score",
        "patient_care_assessment_score",
    )

    for field in numeric_fields:
        value = candidate[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{field} must be an integer or float")
        if not math.isfinite(value):
            raise ValueError(f"{field} must be finite")

    experience = candidate["relevant_experience_years"]
    if not 0 <= experience <= 40:
        raise ValueError("relevant_experience_years must be between 0 and 40")

    for field in numeric_fields[1:]:
        if not 0 <= candidate[field] <= 100:
            raise ValueError(f"{field} must be between 0 and 100")

    eligible = (
        candidate["has_valid_registration"]
        and candidate["meets_required_shift_availability"]
    )

    if not eligible:
        score = 0
    else:
        experience_component = min(experience, 20.0)
        assessment_component = (
            candidate["clinical_assessment_score"] * 0.30
            + candidate["communication_assessment_score"] * 0.25
            + candidate["patient_care_assessment_score"] * 0.25
        )
        score = int(math.floor(experience_component + assessment_component + 0.5))
        score = max(0, min(100, score))

    return {
        "candidate_id": candidate_id,
        "eligible": eligible,
        "suitability_score": score,
    }