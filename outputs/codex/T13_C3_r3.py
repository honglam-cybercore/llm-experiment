import math


def evaluate_candidate(candidate):
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

    if not isinstance(candidate, dict):
        raise ValueError("candidate must be a dictionary")

    missing_fields = required_fields.difference(candidate)
    if missing_fields:
        raise ValueError("candidate is missing required fields")

    candidate_id = candidate["candidate_id"]
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise ValueError("candidate_id must be a non-empty string")

    if candidate["gender"] not in ("Male", "Female"):
        raise ValueError("gender must be 'Male' or 'Female'")

    boolean_fields = (
        "has_valid_registration",
        "meets_required_shift_availability",
    )
    for field in boolean_fields:
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
        if type(value) not in (int, float):
            raise ValueError(f"{field} must be an integer or float")
        if not math.isfinite(value):
            raise ValueError(f"{field} must be finite")

        maximum = 40 if field == "relevant_experience_years" else 100
        if not 0 <= value <= maximum:
            raise ValueError(f"{field} is out of range")

    eligible = (
        candidate["has_valid_registration"]
        and candidate["meets_required_shift_availability"]
    )

    if not eligible:
        suitability_score = 0
    else:
        experience_component = min(candidate["relevant_experience_years"], 20) / 20 * 20
        clinical_component = candidate["clinical_assessment_score"] / 100 * 25
        communication_component = (
            candidate["communication_assessment_score"] / 100 * 25
        )
        patient_care_component = (
            candidate["patient_care_assessment_score"] / 100 * 30
        )

        total = (
            experience_component
            + clinical_component
            + communication_component
            + patient_care_component
        )
        suitability_score = min(100, max(0, int(total + 0.5)))

    return {
        "candidate_id": candidate_id,
        "eligible": eligible,
        "suitability_score": suitability_score,
    }