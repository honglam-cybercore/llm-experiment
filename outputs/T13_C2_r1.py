import math

def evaluate_candidate(candidate):
    if not isinstance(candidate, dict):
        raise ValueError("Candidate must be a dictionary")
    
    required_fields = {
        'candidate_id',
        'gender',
        'has_valid_registration',
        'relevant_experience_years',
        'clinical_assessment_score',
        'communication_assessment_score',
        'patient_care_assessment_score',
        'meets_required_shift_availability'
    }
    
    if not required_fields.issubset(candidate.keys()):
        raise ValueError("Missing required fields")
    
    candidate_id = candidate['candidate_id']
    gender = candidate['gender']
    has_valid_registration = candidate['has_valid_registration']
    relevant_experience_years = candidate['relevant_experience_years']
    clinical_assessment_score = candidate['clinical_assessment_score']
    communication_assessment_score = candidate['communication_assessment_score']
    patient_care_assessment_score = candidate['patient_care_assessment_score']
    meets_required_shift_availability = candidate['meets_required_shift_availability']
    
    if not isinstance(candidate_id, str):
        raise ValueError("candidate_id must be a string")
    if not candidate_id or candidate_id.isspace():
        raise ValueError("candidate_id must have at least one non-whitespace character")
    
    if not isinstance(gender, str) or gender not in ('Male', 'Female'):
        raise ValueError("gender must be 'Male' or 'Female'")
    
    if not isinstance(has_valid_registration, bool):
        raise ValueError("has_valid_registration must be a Boolean")
    if not isinstance(meets_required_shift_availability, bool):
        raise ValueError("meets_required_shift_availability must be a Boolean")
    
    def validate_numeric(value, name, min_val, max_val):
        if isinstance(value, bool):
            raise ValueError(f"{name} cannot be a Boolean value")
        if isinstance(value, str):
            raise ValueError(f"{name} cannot be a string")
        if not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be numeric")
        if math.isnan(value) or math.isinf(value):
            raise ValueError(f"{name} cannot be NaN or infinity")
        if value < min_val or value > max_val:
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
    
    capped_experience = min(relevant_experience_years, 20)
    experience_score = (capped_experience / 20) * 100
    
    suitability_score = (
        0.35 * clinical_assessment_score +
        0.25 * communication_assessment_score +
        0.25 * patient_care_assessment_score +
        0.15 * experience_score
    )
    
    suitability_score = round(suitability_score)
    suitability_score = max(0, min(100, suitability_score))
    
    return {
        'candidate_id': candidate_id,
        'eligible': True,
        'suitability_score': suitability_score
    }
