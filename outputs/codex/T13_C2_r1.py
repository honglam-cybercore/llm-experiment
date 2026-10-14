from decimal import Decimal, ROUND_HALF_UP
import math


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

    numeric_fields = {
        "relevant_experience_years": (0, 40),
        "clinical_assessment_score": (0, 100),
        "communication_assessment_score": (0, 100),
        "patient_care_assessment_score": (0, 100),
    }

    for field, (lower, upper) in numeric_fields.items():
        value = candidate[field]
        if type(value) not in (int, float):
            raise ValueError(f"{field} must be an integer or float")
        if not math.isfinite(value) or not lower <= value <= upper:
            raise ValueError(f"{field} is outside the valid range")

    eligible = (
        candidate["has_valid_registration"]
        and candidate["meets_required_shift_availability"]
    )

    if not eligible:
        score = 0
    else:
        experience = Decimal(str(candidate["relevant_experience_years"]))
        clinical = Decimal(str(candidate["clinical_assessment_score"]))
        communication = Decimal(str(candidate["communication_assessment_score"]))
        patient_care = Decimal(str(candidate["patient_care_assessment_score"]))

        score_value = (
            experience / Decimal("40") * Decimal("20")
            + (clinical + communication + patient_care)
            / Decimal("300")
            * Decimal("80")
        )
        score = int(score_value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    return {
        "candidate_id": candidate_id,
        "eligible": eligible,
        "suitability_score": score,
    }