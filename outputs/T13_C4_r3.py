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
    
    missing_fields = required_fields - set(candidate.keys())
    if missing_fields:
        raise ValueError("Missing required fields")
    
    candidate_id = candidate['candidate_id']
    if not isinstance(candidate_id, str):
        raise ValueError("candidate_id must be a string")
    if not candidate_id or candidate_id.isspace():
        raise ValueError("candidate_id must contain at least one non-whitespace character")
    
    gender = candidate['gender']
    if gender not in ("Male", "Female"):
        raise ValueError("gender must be 'Male' or 'Female'")
    
    if not isinstance(candidate['has_valid_registration'], bool):
        raise ValueError("has_valid_registration must be a boolean value")
    if not isinstance(candidate['meets_required_shift_availability'], bool):
        raise ValueError("meets_required_shift_availability must be a boolean value")
    
    has_valid_registration = candidate['has_valid_registration']
    meets_required_shift_availability = candidate['meets_required_shift_availability']
    
    def validate_numeric(value, field_name, min_val, max_val):
        # bool is a subclass of int in Python, so check it first
        if isinstance(value, bool):
            raise ValueError(f"{field_name}: boolean values are not valid")
        if isinstance(value, str):
            raise ValueError(f"{field_name}: numeric strings are not accepted")
        if not isinstance(value, (int, float)):
            raise ValueError(f"{field_name}: must be numeric")
        if not math.isfinite(value):
            raise ValueError(f"{field_name}: must be finite")
        if value < min_val or value > max_val:
            raise ValueError(f"{field_name}: value out of valid range")
        return value
    
    relevant_experience_years = validate_numeric(
        candidate['relevant_experience_years'], 
        'relevant_experience_years', 0, 40
    )
    clinical_assessment_score = validate_numeric(
        candidate['clinical_assessment_score'],
        'clinical_assessment_score', 0, 100
    )
    communication_assessment_score = validate_numeric(
        candidate['communication_assessment_score'],
        'communication_assessment_score', 0, 100
    )
    patient_care_assessment_score = validate_numeric(
        candidate['patient_care_assessment_score'],
        'patient_care_assessment_score', 0, 100
    )
    
    eligible = has_valid_registration and meets_required_shift_availability
    
    if not eligible:
        return {
            'candidate_id': candidate_id,
            'eligible': False,
            'suitability_score': 0
        }
    
    assessment_average = (
        clinical_assessment_score + 
        communication_assessment_score + 
        patient_care_assessment_score
    ) / 3
    
    experience_score = min(relevant_experience_years, 10) / 10 * 100
    
    suitability_score = round(assessment_average * 0.7 + experience_score * 0.3)
    
    return {
        'candidate_id': candidate_id,
        'eligible': True,
        'suitability_score': suitability_score
    }
