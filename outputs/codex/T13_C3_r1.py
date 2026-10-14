import math


def evaluate_candidate(candidate: dict) -> dict:
    if type(candidate) is not dict:
        raise ValueError("candidate must be a dictionary")

    required_fields = (
        "candidate_id",
        "gender",
        "has_valid_registration",
        "relevant_experience_years",
        "clinical_assessment_score",
        "communication_assessment_score",
        "patient_care_assessment_score",
        "meets_required_shift_availability",
    )

    missing_fields = [field for field in required_fields if field not in candidate]
    if missing_fields:
        raise ValueError("missing required candidate fields")

    candidate_id = candidate["candidate_id"]
    if type(candidate_id) is not str or not candidate_id.strip():
        raise ValueError("candidate_id must be a non-whitespace string")

    if candidate["gender"] not in ("Male", "Female"):
        raise ValueError("gender must be Male or Female")

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

    experience = candidate["relevant_experience_years"]
    if not 0 <= experience <= 40:
        raise ValueError("relevant_experience_years must be between 0 and 40")

    assessment_fields = (
        "clinical_assessment_score",
        "communication_assessment_score",
        "patient_care_assessment_score",
    )
    for field in assessment_fields:
        if not 0 <= candidate[field] <= 100:
            raise ValueError(f"{field} must be between 0 and 100")

    eligible = (
        candidate["has_valid_registration"]
        and candidate["meets_required_shift_availability"]
    )

    if not eligible:
        suitability_score = 0
    else:
        experience_component = min(experience / 20.0, 1.0) * 15.0
        clinical_component = candidate["clinical_assessment_score"] * 0.30
        communication_component = candidate["communication_assessment_score"] * 0.25
        patient_care_component = candidate["patient_care_assessment_score"] * 0.30

        raw_score = (
            experience_component
            + clinical_component
            + communication_component
            + patient_care_component
        )
        suitability_score = min(100, max(0, int(raw_score + 0.5)))

    return {
        "candidate_id": candidate_id,
        "eligible": eligible,
        "suitability_score": suitability_score,
    }