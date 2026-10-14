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


def evaluate_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(candidate, dict):
        raise ValueError("candidate must be a dictionary")

    missing_fields = _REQUIRED_FIELDS - candidate.keys()
    if missing_fields:
        raise ValueError("candidate is missing required fields")

    candidate_id = candidate["candidate_id"]
    gender = candidate["gender"]
    has_valid_registration = candidate["has_valid_registration"]
    relevant_experience_years = candidate["relevant_experience_years"]
    clinical_score = candidate["clinical_assessment_score"]
    communication_score = candidate["communication_assessment_score"]
    patient_care_score = candidate["patient_care_assessment_score"]
    meets_shift_availability = candidate["meets_required_shift_availability"]

    if (
        type(candidate_id) is not str
        or not candidate_id.strip()
    ):
        raise ValueError("candidate_id must be a non-whitespace string")

    if type(gender) is not str or gender not in {"Male", "Female"}:
        raise ValueError("gender must be 'Male' or 'Female'")

    if type(has_valid_registration) is not bool:
        raise ValueError("has_valid_registration must be a Boolean")

    if type(meets_shift_availability) is not bool:
        raise ValueError("meets_required_shift_availability must be a Boolean")

    numeric_values = (
        relevant_experience_years,
        clinical_score,
        communication_score,
        patient_care_score,
    )

    if any(type(value) not in (int, float) for value in numeric_values):
        raise ValueError("numeric fields must contain integers or floats")

    if any(not math.isfinite(float(value)) for value in numeric_values):
        raise ValueError("numeric fields must be finite")

    if not 0 <= relevant_experience_years <= 40:
        raise ValueError("relevant_experience_years must be between 0 and 40")

    if any(not 0 <= value <= 100 for value in (
        clinical_score,
        communication_score,
        patient_care_score,
    )):
        raise ValueError("assessment scores must be between 0 and 100")

    eligible = has_valid_registration and meets_shift_availability

    if not eligible:
        suitability_score = 0
    else:
        experience_component = (relevant_experience_years / 40) * 20
        clinical_component = (clinical_score / 100) * 25
        communication_component = (communication_score / 100) * 25
        patient_care_component = (patient_care_score / 100) * 30

        suitability_score = int(round(
            experience_component
            + clinical_component
            + communication_component
            + patient_care_component
        ))
        suitability_score = max(0, min(100, suitability_score))

    return {
        "candidate_id": candidate_id,
        "eligible": eligible,
        "suitability_score": suitability_score,
    }