from math import isfinite


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


def _validate_numeric(value, field_name, minimum, maximum):
    if type(value) not in (int, float):
        raise ValueError(f"{field_name} must be an integer or float")
    if isinstance(value, float) and not isfinite(value):
        raise ValueError(f"{field_name} must be finite")
    if not minimum <= value <= maximum:
        raise ValueError(f"{field_name} must be between {minimum} and {maximum}")


def evaluate_candidate(candidate):
    if not isinstance(candidate, dict):
        raise ValueError("candidate must be a dictionary")

    for field in _REQUIRED_FIELDS:
        if field not in candidate:
            raise ValueError(f"missing required field: {field}")

    candidate_id = candidate["candidate_id"]
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise ValueError("candidate_id must be a non-empty string")

    if candidate["gender"] not in ("Male", "Female"):
        raise ValueError("gender must be 'Male' or 'Female'")

    if type(candidate["has_valid_registration"]) is not bool:
        raise ValueError("has_valid_registration must be a Boolean")

    if type(candidate["meets_required_shift_availability"]) is not bool:
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
        experience_component = 20 * min(candidate["relevant_experience_years"], 10) / 10
        clinical_component = 0.30 * candidate["clinical_assessment_score"]
        communication_component = 0.25 * candidate["communication_assessment_score"]
        patient_care_component = 0.25 * candidate["patient_care_assessment_score"]

        suitability_score = int(
            experience_component
            + clinical_component
            + communication_component
            + patient_care_component
            + 0.5
        )
        suitability_score = max(0, min(100, suitability_score))

    return {
        "candidate_id": candidate_id,
        "eligible": eligible,
        "suitability_score": suitability_score,
    }