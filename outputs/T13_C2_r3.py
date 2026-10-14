def evaluate_nurse_candidate(candidate):
    # Validate all required fields are present
    required_fields = {
        'candidate_id', 'gender', 'has_valid_registration',
        'relevant_experience_years', 'clinical_assessment_score',
        'communication_assessment_score', 'patient_care_assessment_score',
        'meets_required_shift_availability'
    }
    if not required_fields.issubset(candidate.keys()):
        raise ValueError("Missing required fields")
    
    # Validate and extract values
    candidate_id = _validate_string_field(candidate['candidate_id'], 'candidate_id')
    gender = _validate_choice_field(candidate['gender'], 'gender', ["Male", "Female"])
    has_valid_registration = _validate_boolean_field(candidate['has_valid_registration'], 'has_valid_registration')
    meets_required_shift_availability = _validate_boolean_field(candidate['meets_required_shift_availability'], 'meets_required_shift_availability')
    relevant_experience_years = _validate_numeric_field(candidate['relevant_experience_years'], 'relevant_experience_years', 0, 40)
    clinical_assessment_score = _validate_numeric_field(candidate['clinical_assessment_score'], 'clinical_assessment_score', 0, 100)
    communication_assessment_score = _validate_numeric_field(candidate['communication_assessment_score'], 'communication_assessment_score', 0, 100)
    patient_care_assessment_score = _validate_numeric_field(candidate['patient_care_assessment_score'], 'patient_care_assessment_score', 0, 100)
    
    # Check eligibility
    eligible = has_valid_registration and meets_required_shift_availability
    
    if not eligible:
        return {
            'candidate_id': candidate_id,
            'eligible': False,
            'suitability_score': 0
        }
    
    # Calculate suitability score for eligible candidates
    avg_assessments = (clinical_assessment_score + communication_assessment_score + patient_care_assessment_score) / 3
    normalized_experience = (min(relevant_experience_years, 20) / 20) * 100
    suitability_score = round(0.70 * avg_assessments + 0.30 * normalized_experience)
    
    return {
        'candidate_id': candidate_id,
        'eligible': True,
        'suitability_score': suitability_score
    }


def _validate_string_field(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _validate_choice_field(value, name, choices):
    if value not in choices:
        raise ValueError(f"{name} must be one of {choices}")
    return value


def _validate_boolean_field(value, name):
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a Boolean")
    return value


def _validate_numeric_field(value, name, min_val, max_val):
    if isinstance(value, bool):
        raise ValueError(f"{name} cannot be a Boolean")
    if not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    if value != value:
        raise ValueError(f"{name} cannot be NaN")
    if value in (float('inf'), float('-inf')):
        raise ValueError(f"{name} cannot be infinity")
    if not (min_val <= value <= max_val):
        raise ValueError(f"{name} must be between {min_val} and {max_val}")
    return value
