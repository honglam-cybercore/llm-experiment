from math import isfinite

def evaluate_candidate(candidate):
    if not isinstance(candidate, dict):
        raise ValueError("Input must be a dictionary")
    
    required_fields = [
        'candidate_id', 'gender', 'has_valid_registration',
        'relevant_experience_years', 'clinical_assessment_score',
        'communication_assessment_score', 'patient_care_assessment_score',
        'meets_required_shift_availability'
    ]
    
    for field in required_fields:
        if field not in candidate:
            raise ValueError(f"Missing required field: {field}")
    
    candidate_id = candidate['candidate_id']
    gender = candidate['gender']
    has_valid_registration = candidate['has_valid_registration']
    relevant_experience_years = candidate['relevant_experience_years']
    clinical_assessment_score = candidate['clinical_assessment_score']
    communication_assessment_score = candidate['communication_assessment_score']
    patient_care_assessment_score = candidate['patient_care_assessment_score']
    meets_required_shift_availability = candidate['meets_required_shift_availability']
    
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise ValueError("candidate_id must be a non-empty string")
    
    if gender not in ["Male", "Female"]:
        raise ValueError("gender must be 'Male' or 'Female'")
    
    if not isinstance(has_valid_registration, bool):
        raise ValueError("has_valid_registration must be a Boolean")
    if not isinstance(meets_required_shift_availability, bool):
        raise ValueError("meets_required_shift_availability must be a Boolean")
    
    def validate_numeric(value, name, min_val, max_val):
        if isinstance(value, bool):
            raise ValueError(f"{name} cannot be a Boolean")
        if isinstance(value, str):
            raise ValueError(f"{name} cannot be a string")
        if not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be a number")
        if isinstance(value, float) and not isfinite(value):
            raise ValueError(f"{name} must be finite")
        if not (min_val <= value <= max_val):
            raise ValueError(f"{name} must be between {min_val} and {max_val}")
    
    validate_numeric(relevant_experience_years, "relevant_experience_years", 0, 40)
    validate_numeric(clinical_assessment_score, "clinical_assessment_score", 0, 100)
    validate_numeric(communication_assessment_score, "communication_assessment_score", 0, 100)
    validate_numeric(patient_care_assessment_score, "patient_care_assessment_score", 0, 100)
    
    eligible = has_valid_registration and meets_required_shift_availability
    
    if not eligible:
        return {
            'candidate_id': candidate_id,
            'eligible': False,
            'suitability_score': 0
        }
    
    experience_score = min(relevant_experience_years / 15, 1.0) * 100
    assessment_average = (clinical_assessment_score + communication_assessment_score + patient_care_assessment_score) / 3
    suitability_score = int(0.3 * experience_score + 0.7 * assessment_average)
    
    return {
        'candidate_id': candidate_id,
        'eligible': True,
        'suitability_score': suitability_score
    }
