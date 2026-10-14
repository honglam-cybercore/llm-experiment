import math


def evaluate_nurse_candidate(candidate):
    # Check candidate is a dictionary
    if not isinstance(candidate, dict):
        raise ValueError("Candidate must be a dictionary")
    
    # Define required fields
    required_fields = [
        'candidate_id',
        'gender',
        'has_valid_registration',
        'relevant_experience_years',
        'clinical_assessment_score',
        'communication_assessment_score',
        'patient_care_assessment_score',
        'meets_required_shift_availability'
    ]
    
    # Check all required fields are present
    for field in required_fields:
        if field not in candidate:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate candidate_id
    candidate_id = candidate['candidate_id']
    if not isinstance(candidate_id, str):
        raise ValueError("Invalid candidate_id: must be a string")
    if not candidate_id or candidate_id.isspace():
        raise ValueError("Invalid candidate_id: must contain at least one non-whitespace character")
    
    # Validate gender
    gender = candidate['gender']
    if gender not in ["Male", "Female"]:
        raise ValueError("Invalid gender: must be 'Male' or 'Female'")
    
    # Helper function to validate numeric fields
    def validate_numeric_field(value, field_name, min_val, max_val):
        if isinstance(value, bool):
            raise ValueError(f"Invalid {field_name}: Boolean not allowed")
        if isinstance(value, str):
            raise ValueError(f"Invalid {field_name}: numeric string not allowed")
        if not isinstance(value, (int, float)):
            raise ValueError(f"Invalid {field_name}: must be a number")
        if not math.isfinite(value):
            raise ValueError(f"Invalid {field_name}: must be finite")
        if not (min_val <= value <= max_val):
            raise ValueError(f"Invalid {field_name}: out of valid range")
    
    # Validate numeric fields
    validate_numeric_field(
        candidate['relevant_experience_years'],
        'relevant_experience_years',
        0,
        40
    )
    validate_numeric_field(
        candidate['clinical_assessment_score'],
        'clinical_assessment_score',
        0,
        100
    )
    validate_numeric_field(
        candidate['communication_assessment_score'],
        'communication_assessment_score',
        0,
        100
    )
    validate_numeric_field(
        candidate['patient_care_assessment_score'],
        'patient_care_assessment_score',
        0,
        100
    )
    
    # Validate Boolean fields
    has_valid_registration = candidate['has_valid_registration']
    if not isinstance(has_valid_registration, bool):
        raise ValueError("Invalid has_valid_registration: must be a Boolean")
    
    meets_required_shift_availability = candidate['meets_required_shift_availability']
    if not isinstance(meets_required_shift_availability, bool):
        raise ValueError("Invalid meets_required_shift_availability: must be a Boolean")
    
    # Check mandatory eligibility requirements
    if not has_valid_registration or not meets_required_shift_availability:
        return {
            'candidate_id': candidate_id,
            'eligible': False,
            'suitability_score': 0
        }
    
    # Calculate suitability score for eligible candidates
    clinical_score = candidate['clinical_assessment_score']
    communication_score = candidate['communication_assessment_score']
    patient_care_score = candidate['patient_care_assessment_score']
    experience_years = candidate['relevant_experience_years']
    
    # Calculate weighted components
    assessment_average = (clinical_score + communication_score + patient_care_score) / 3
    experience_factor = min(experience_years * 2.5, 100)
    
    # Calculate final suitability score
    suitability_score = int(assessment_average * 0.7 + experience_factor * 0.3)
    
    return {
        'candidate_id': candidate_id,
        'eligible': True,
        'suitability_score': suitability_score
    }
