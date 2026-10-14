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
    
    if not required_fields.issubset(set(candidate.keys())):
        raise ValueError("Missing required fields")
    
    candidate_id = candidate['candidate_id']
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise ValueError("candidate_id must be a non-empty string with non-whitespace characters")
    
    gender = candidate['gender']
    if not isinstance(gender, str) or gender not in ['Male', 'Female']:
        raise ValueError("gender must be 'Male' or 'Female'")
    
    if not isinstance(candidate['has_valid_registration'], bool):
        raise ValueError("has_valid_registration must be a Boolean")
    
    if not isinstance(candidate['meets_required_shift_availability'], bool):
        raise ValueError("meets_required_shift_availability must be a Boolean")
    
    def validate_numeric(value, field_name, min_val, max_val):
        if isinstance(value, bool):
            raise ValueError(f"{field_name} cannot be a Boolean value")
        
        if isinstance(value, str):
            raise ValueError(f"{field_name} must be a number, not a string")
        
        if not isinstance(value, (int, float)):
            raise ValueError(f"{field_name} must be a numeric value")
        
        if not math.isfinite(value):
            raise ValueError(f"{field_name} must be a finite number")
        
        if not (min_val <= value <= max_val):
            raise ValueError(f"{field_name} must be between {min_val} and {max_val}")
    
    validate_numeric(candidate['relevant_experience_years'], 'relevant_experience_years', 0, 40)
    validate_numeric(candidate['clinical_assessment_score'], 'clinical_assessment_score', 0, 100)
    validate_numeric(candidate['communication_assessment_score'], 'communication_assessment_score', 0, 100)
    validate_numeric(candidate['patient_care_assessment_score'], 'patient_care_assessment_score', 0, 100)
    
    has_registration = candidate['has_valid_registration']
    meets_shift_availability = candidate['meets_required_shift_availability']
    
    if not has_registration or not meets_shift_availability:
        return {
            'candidate_id': candidate_id,
            'eligible': False,
            'suitability_score': 0
        }
    
    experience_normalized = min(candidate['relevant_experience_years'] / 10.0, 1.0)
    clinical_normalized = candidate['clinical_assessment_score'] / 100.0
    communication_normalized = candidate['communication_assessment_score'] / 100.0
    patient_care_normalized = candidate['patient_care_assessment_score'] / 100.0
    
    average_normalized = (experience_normalized + clinical_normalized + 
                         communication_normalized + patient_care_normalized) / 4.0
    
    suitability_score = int(round(average_normalized * 100))
    suitability_score = max(0, min(100, suitability_score))
    
    return {
        'candidate_id': candidate_id,
        'eligible': True,
        'suitability_score': suitability_score
    }
