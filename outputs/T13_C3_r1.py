import math

def evaluate_nurse_candidate(candidate):
    # Validate input type
    if not isinstance(candidate, dict):
        raise ValueError("Input must be a dictionary")
    
    # Check for required fields
    required_fields = {
        'candidate_id', 'gender', 'has_valid_registration',
        'relevant_experience_years', 'clinical_assessment_score',
        'communication_assessment_score', 'patient_care_assessment_score',
        'meets_required_shift_availability'
    }
    
    if not required_fields.issubset(set(candidate.keys())):
        raise ValueError("Missing required field")
    
    # Validate candidate_id
    candidate_id = candidate['candidate_id']
    if not isinstance(candidate_id, str):
        raise ValueError("candidate_id must be a string")
    if not candidate_id.strip():
        raise ValueError("candidate_id must contain non-whitespace characters")
    
    # Validate gender
    gender = candidate['gender']
    if not isinstance(gender, str) or gender not in ['Male', 'Female']:
        raise ValueError("gender must be 'Male' or 'Female'")
    
    # Validate Boolean fields
    has_valid_registration = candidate['has_valid_registration']
    if not isinstance(has_valid_registration, bool):
        raise ValueError("has_valid_registration must be a boolean")
    
    meets_required_shift_availability = candidate['meets_required_shift_availability']
    if not isinstance(meets_required_shift_availability, bool):
        raise ValueError("meets_required_shift_availability must be a boolean")
    
    # Validate numeric fields
    def validate_numeric(value, field_name, min_val, max_val):
        if isinstance(value, bool):
            raise ValueError(f"{field_name} cannot be a boolean")
        if isinstance(value, str):
            raise ValueError(f"{field_name} cannot be a string")
        if not isinstance(value, (int, float)):
            raise ValueError(f"{field_name} must be numeric")
        if not math.isfinite(value):
            raise ValueError(f"{field_name} must be finite")
        if not (min_val <= value <= max_val):
            raise ValueError(f"{field_name} must be between {min_val} and {max_val}")
        return value
    
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
    
    # Check eligibility (mandatory requirements)
    if not has_valid_registration or not meets_required_shift_availability:
        return {
            'candidate_id': candidate_id,
            'eligible': False,
            'suitability_score': 0
        }
    
    # Calculate suitability score for eligible candidates
    assessment_avg = (clinical_assessment_score + communication_assessment_score + patient_care_assessment_score) / 3
    assessment_contribution = assessment_avg * 0.8
    experience_contribution = (min(relevant_experience_years, 10) / 10) * 20
    suitability_score = int(round(assessment_contribution + experience_contribution))
    
    # Ensure score is within bounds [0, 100]
    suitability_score = max(0, min(100, suitability_score))
    
    return {
        'candidate_id': candidate_id,
        'eligible': True,
        'suitability_score': suitability_score
    }
