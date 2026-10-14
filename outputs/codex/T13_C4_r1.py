import math


def evaluate_candidate(candidate: dict) -> dict:
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

    missing_fields = required_fields - candidate.keys()
    if missing_fields:
        raise ValueError("candidate is missing required fields")

    candidate_id = candidate["candidate_id"]
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise ValueError("candidate_id must be a non-empty string")

    if candidate["gender"] not in ("Male", "Female"):
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
        return {
            "candidate_id": candidate_id,
            "eligible": False,
            "suitability_score": 0,
        }

    experience_points = min(experience, 20.0)
    clinical_points = candidate["clinical_assessment_score"] * 0.30
    communication_points = candidate["communication_assessment_score"] * 0.20
    patient_care_points = candidate["patient_care_assessment_score"] * 0.30

    raw_score = (
        experience_points
        + clinical_points
        + communication_points
        + patient_care_points
    )
    suitability_score = min(100, max(0, math.floor(raw_score + 0.5)))

    return {
        "candidate_id": candidate_id,
        "eligible": True,
        "suitability_score": suitability_score,
    }