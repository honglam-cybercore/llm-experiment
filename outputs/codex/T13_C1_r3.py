from math import isfinite


def evaluate_candidate(candidate: dict) -> dict:
    if not isinstance(candidate, dict):
        raise ValueError("candidate must be a dictionary")

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

    if not required_fields.issubset(candidate):
        raise ValueError("candidate is missing required fields")

    candidate_id = candidate["candidate_id"]
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise ValueError("candidate_id must be a non-whitespace string")

    if candidate["gender"] not in {"Male", "Female"}:
        raise ValueError("gender must be Male or Female")

    for field in (
        "has_valid_registration",
        "meets_required_shift_availability",
    ):
        if type(candidate[field]) is not bool:
            raise ValueError(f"{field} must be a Boolean")

    numeric_fields = (
        ("relevant_experience_years", 0, 40),
        ("clinical_assessment_score", 0, 100),
        ("communication_assessment_score", 0, 100),
        ("patient_care_assessment_score", 0, 100),
    )

    for field, minimum, maximum in numeric_fields:
        value = candidate[field]
        if type(value) not in (int, float) or not isfinite(value):
            raise ValueError(f"{field} must be a finite number")
        if not minimum <= value <= maximum:
            raise ValueError(f"{field} is out of range")

    eligible = (
        candidate["has_valid_registration"]
        and candidate["meets_required_shift_availability"]
    )

    if not eligible:
        score = 0
    else:
        experience_component = min(candidate["relevant_experience_years"], 20) / 20 * 20
        clinical_component = candidate["clinical_assessment_score"] * 0.35
        communication_component = candidate["communication_assessment_score"] * 0.25
        patient_care_component = candidate["patient_care_assessment_score"] * 0.40

        raw_score = (
            experience_component
            + clinical_component
            + communication_component
            + patient_care_component
        )
        score = min(100, max(0, int(raw_score + 0.5)))

    return {
        "candidate_id": candidate_id,
        "eligible": eligible,
        "suitability_score": score,
    }