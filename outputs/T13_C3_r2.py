import math

def evaluate_nurse_candidate(candidate):
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
    
    if not isinstance(candidate, dict):
        raise ValueError("Input must be a dictionary")
    
    if set(candidate.keys()) != required_fields:
        raise ValueError("Input must contain exactly the required fields")
    
    candidate_id = candidate['candidate_id']
    if not isinstance(candidate_id, str):
        raise ValueError("Field candidate_id must be a string")
    if not candidate_id or candidate_id.isspace():
        raise ValueError("Field candidate_id must contain at least one non-whitespace character")
    
    gender = candidate['gender']
    if not isinstance(gender, str) or gender not in ("Male", "Female"):
        raise ValueError("Field gender must be 'Male' or 'Female'")
    
    has_valid_registration = candidate['has_valid_registration']
    if not isinstance(has_valid_registration, bool):
        raise ValueError("Field has_valid_registration must be a Boolean")
    
    meets_required_shift_availability = candidate['meets_required_shift_availability']
    if not isinstance(meets_required_shift_availability, bool):
        raise ValueError("Field meets_required_shift_availability must be a Boolean")
    
    relevant_experience_years = candidate['relevant_experience_years']
    if isinstance(relevant_experience_years, bool):
        raise ValueError("Field relevant_experience_years must be numeric, not Boolean")
    if not isinstance(relevant_experience_years, (int, float)):
        raise ValueError("Field relevant_experience_years must be numeric")
    if not math.isfinite(relevant_experience_years):
        raise ValueError("Field relevant_experience_years must be finite")
    if not (0 <= relevant_experience_years <= 40):
        raise ValueError("Field relevant_experience_years must be between 0 and 40")
    
    clinical_assessment_score = candidate['clinical_assessment_score']
    if isinstance(clinical_assessment_score, bool):
        raise ValueError("Field clinical_assessment_score must be numeric, not Boolean")
    if not isinstance(clinical_assessment_score, (int, float)):
        raise ValueError("Field clinical_assessment_score must be numeric")
    if not math.isfinite(clinical_assessment_score):
        raise ValueError("Field clinical_assessment_score must be finite")
    if not (0 <= clinical_assessment_score <= 100):
        raise ValueError("Field clinical_assessment_score must be between 0 and 100")
    
    communication_assessment_score = candidate['communication_assessment_score']
    if isinstance(communication_assessment_score, bool):
        raise ValueError("Field communication_assessment_score must be numeric, not Boolean")
    if not isinstance(communication_assessment_score, (int, float)):
        raise ValueError("Field communication_assessment_score must be numeric")
    if not math.isfinite(communication_assessment_score):
        raise ValueError("Field communication_assessment_score must be finite")
    if not (0 <= communication_assessment_score <= 100):
        raise ValueError("Field communication_assessment_score must be between 0 and 100")
    
    patient_care_assessment_score = candidate['patient_care_assessment_score']
    if isinstance(patient_care_assessment_score, bool):
        raise ValueError("Field patient_care_assessment_score must be numeric, not Boolean")
    if not isinstance(patient_care_assessment_score, (int, float)):
        raise ValueError("Field patient_care_assessment_score must be numeric")
    if not math.isfinite(patient_care_assessment_score):
        raise ValueError("Field patient_care_assessment_score must be finite")
    if not (0 <= patient_care_assessment_score <= 100):
        raise ValueError("Field patient_care_assessment_score must be between 0 and 100")
    
    if not has_valid_registration or not meets_required_shift_availability:
        return {
            'candidate_id': candidate_id,
            'eligible': False,
            'suitability_score': 0
        }
    
    experience_points = min(relevant_experience_years, 40) * 0.5
    clinical_points = clinical_assessment_score * 0.25
    communication_points = communication_assessment_score * 0.25
    patient_care_points = patient_care_assessment_score * 0.30
    
    total_score = experience_points + clinical_points + communication_points + patient_care_points
    suitability_score = int(total_score)
    suitability_score = min(max(suitability_score, 0), 100)
    
    return {
        'candidate_id': candidate_id,
        'eligible': True,
        'suitability_score': suitability_score
    }
