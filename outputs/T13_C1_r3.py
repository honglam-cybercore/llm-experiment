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
    
    if not all(field in candidate for field in required_fields):
        raise ValueError("Missing required fields")
    
    candidate_id = candidate['candidate_id']
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise ValueError("candidate_id must be a non-empty string with at least one non-whitespace character")
    
    gender = candidate['gender']
    if gender not in ['Male', 'Female']:
        raise ValueError("gender must be 'Male' or 'Female'")
    
    has_valid_registration = candidate['has_valid_registration']
    if not isinstance(has_valid_registration, bool):
        raise ValueError("has_valid_registration must be a Boolean")
    
    relevant_experience_years = candidate['relevant_experience_years']
    if isinstance(relevant_experience_years, bool):
        raise ValueError("relevant_experience_years cannot be a Boolean")
    if not isinstance(relevant_experience_years, (int, float)):
        raise ValueError("relevant_experience_years must be numeric")
    if not math.isfinite(relevant_experience_years):
        raise ValueError("relevant_experience_years must be finite")
    if relevant_experience_years < 0 or relevant_experience_years > 40:
        raise ValueError("relevant_experience_years must be between 0 and 40")
    
    clinical_assessment_score = candidate['clinical_assessment_score']
    if isinstance(clinical_assessment_score, bool):
        raise ValueError("clinical_assessment_score cannot be a Boolean")
    if not isinstance(clinical_assessment_score, (int, float)):
        raise ValueError("clinical_assessment_score must be numeric")
    if not math.isfinite(clinical_assessment_score):
        raise ValueError("clinical_assessment_score must be finite")
    if clinical_assessment_score < 0 or clinical_assessment_score > 100:
        raise ValueError("clinical_assessment_score must be between 0 and 100")
    
    communication_assessment_score = candidate['communication_assessment_score']
    if isinstance(communication_assessment_score, bool):
        raise ValueError("communication_assessment_score cannot be a Boolean")
    if not isinstance(communication_assessment_score, (int, float)):
        raise ValueError("communication_assessment_score must be numeric")
    if not math.isfinite(communication_assessment_score):
        raise ValueError("communication_assessment_score must be finite")
    if communication_assessment_score < 0 or communication_assessment_score > 100:
        raise ValueError("communication_assessment_score must be between 0 and 100")
    
    patient_care_assessment_score = candidate['patient_care_assessment_score']
    if isinstance(patient_care_assessment_score, bool):
        raise ValueError("patient_care_assessment_score cannot be a Boolean")
    if not isinstance(patient_care_assessment_score, (int, float)):
        raise ValueError("patient_care_assessment_score must be numeric")
    if not math.isfinite(patient_care_assessment_score):
        raise ValueError("patient_care_assessment_score must be finite")
    if patient_care_assessment_score < 0 or patient_care_assessment_score > 100:
        raise ValueError("patient_care_assessment_score must be between 0 and 100")
    
    meets_required_shift_availability = candidate['meets_required_shift_availability']
    if not isinstance(meets_required_shift_availability, bool):
        raise ValueError("meets_required_shift_availability must be a Boolean")
    
    eligible = has_valid_registration and meets_required_shift_availability
    
    if not eligible:
        return {
            'candidate_id': candidate_id,
            'eligible': False,
            'suitability_score': 0
        }
    
    experience_contribution = min(relevant_experience_years, 20) / 20 * 25
    clinical_contribution = clinical_assessment_score / 100 * 25
    communication_contribution = communication_assessment_score / 100 * 25
    patient_care_contribution = patient_care_assessment_score / 100 * 25
    
    suitability_score = int(experience_contribution + clinical_contribution + communication_contribution + patient_care_contribution)
    
    return {
        'candidate_id': candidate_id,
        'eligible': True,
        'suitability_score': suitability_score
    }
