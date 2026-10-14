import math
from numbers import Real
from typing import Any


def evaluate_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    required_fields = {
        "candidate_id",
        "gender",
        "has_valid_registration",
        "relevant_experience_years",
        "clinical_assessment_score",
        "communication_assessment_score",
        "patient_care_assessment_score",
        "meets_required_shift_availability",
    }

    if not isinstance(candidate, dict) or not required_fields.issubset(candidate):
        raise ValueError("Invalid candidate record")

    candidate_id = candidate["candidate_id"]
    gender = candidate["gender"]
    has_valid_registration = candidate["has_valid_registration"]
    experience = candidate["relevant_experience_years"]
    clinical_score = candidate["clinical_assessment_score"]
    communication_score = candidate["communication_assessment_score"]
    patient_care_score = candidate["patient_care_assessment_score"]
    meets_shift_availability = candidate["meets_required_shift_availability"]

    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise ValueError("Invalid candidate_id")

    if gender not in ("Male", "Female"):
        raise ValueError("Invalid gender")

    if type(has_valid_registration) is not bool:
        raise ValueError("Invalid registration eligibility value")

    if type(meets_shift_availability) is not bool:
        raise ValueError("Invalid shift availability value")

    numeric_values = (
        experience,
        clinical_score,
        communication_score,
        patient_care_score,
    )

    for value in numeric_values:
        if (
            isinstance(value, bool)
            or not isinstance(value, Real)
            or not math.isfinite(float(value))
        ):
            raise ValueError("Invalid numeric value")

    if not 0 <= experience <= 40:
        raise ValueError("Invalid experience value")

    if not all(0 <= score <= 100 for score in numeric_values[1:]):
        raise ValueError("Invalid assessment score")

    eligible = has_valid_registration and meets_shift_availability

    if not eligible:
        suitability_score = 0
    else:
        experience_component = min(float(experience), 20.0) / 20.0 * 20.0
        clinical_component = float(clinical_score) / 100.0 * 30.0
        communication_component = float(communication_score) / 100.0 * 20.0
        patient_care_component = float(patient_care_score) / 100.0 * 30.0

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