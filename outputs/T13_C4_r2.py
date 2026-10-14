import math

def evaluate_nurse_candidate(candidate):
    if not isinstance(candidate, dict):
        raise ValueError("Input must be a dictionary")
    
    required_fields = {
        'candidate_id', 'gender', 'has_valid_registration',
        'relevant_experience_years', 'clinical_assessment_score',
        'communication_assessment_score', 'patient_care_assessment_score',
        'meets_required_shift_availability'
    }
    
    if not required_fields.issubset(candidate.keys()):
        raise ValueError("Missing required fields")
    
    candidate_id = candidate['candidate_id']
    if not isinstance(candidate_id, str):
        raise ValueError("Invalid candidate_id: must be a string")
    if not candidate_id.strip():
        raise ValueError("Invalid candidate_id: must contain at least one non-whitespace character")
    
    gender = candidate['gender']
    if gender not in ("Male", "Female"):
        raise ValueError("Invalid gender: must be 'Male' or 'Female'")
    
    has_valid_registration = candidate['has_valid_registration']
    if not isinstance(has_valid_registration, bool):
        raise ValueError("Invalid has_valid_registration: must be Boolean")
    
    meets_required_shift_availability = candidate['meets_required_shift_availability']
    if not isinstance(meets_required_shift_availability, bool):
        raise ValueError("Invalid meets_required_shift_availability: must be Boolean")
    
    def validate_numeric(value, field_name, min_val, max_val):
        if isinstance(value, bool):
            raise ValueError(f"Invalid {field_name}: Boolean values not allowed")
        if isinstance(value, str):
            raise ValueError(f"Invalid {field_name}: numeric strings not allowed")
        try:
            num = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid {field_name}: must be numeric")
        if math.isnan(num) or math.isinf(num):
            raise ValueError(f"Invalid {field_name}: NaN or infinity not allowed")
        if not (min_val <= num <= max_val):
            raise ValueError(f"Invalid {field_name}: must be between {min_val} and {max_val}")
        return num
    
    relevant_experience_years = validate_numeric(
        candidate['relevant_experience_years'], 'relevant_experience_years', 0, 40
    )
    clinical_assessment_score = validate_numeric(
        candidate['clinical_assessment_score'], 'clinical_assessment_score', 0, 100
    )
    communication_assessment_score = validate_numeric(
        candidate['communication_assessment_score'], 'communication_assessment_score', 0, 100
    )
    patient_care_assessment_score = validate_numeric(
        candidate['patient_care_assessment_score'], 'patient_care_assessment_score', 0, 100
    )
    
    if not has_valid_registration or not meets_required_shift_availability:
        return {
            'candidate_id': candidate_id,
            'eligible': False,
            'suitability_score': 0
        }
    
    experience_contribution = min(relevant_experience_years, 10) / 10 * 100
    assessment_average = (clinical_assessment_score + communication_assessment_score + patient_care_assessment_score) / 3
    final_score = experience_contribution * 0.25 + assessment_average * 0.75
    suitability_score = int(round(final_score))
    suitability_score = max(0, min(100, suitability_score))
    
    return {
        'candidate_id': candidate_id,
        'eligible': True,
        'suitability_score': suitability_score
    }
