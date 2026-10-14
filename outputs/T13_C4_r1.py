import math

def evaluate_nurse_candidate(candidate):
    # Validate input is a dictionary
    if not isinstance(candidate, dict):
        raise ValueError("Input must be a dictionary")
    
    # Check all required fields are present
    required_fields = {
        'candidate_id', 'gender', 'has_valid_registration',
        'relevant_experience_years', 'clinical_assessment_score',
        'communication_assessment_score', 'patient_care_assessment_score',
        'meets_required_shift_availability'
    }
    
    if not required_fields.issubset(candidate.keys()):
        raise ValueError("Missing required fields in candidate record")
    
    # Validate candidate_id: string with at least one non-whitespace character
    candidate_id = candidate['candidate_id']
    if not isinstance(candidate_id, str):
        raise ValueError("Invalid candidate_id: must be string")
    if not candidate_id.strip():
        raise ValueError("Invalid candidate_id: must contain non-whitespace")
    
    # Validate gender: must be "Male" or "Female"
    if candidate['gender'] not in ("Male", "Female"):
        raise ValueError("Invalid gender value")
    
    # Validate has_valid_registration: must be actual boolean
    if not isinstance(candidate['has_valid_registration'], bool):
        raise ValueError("Invalid has_valid_registration: must be boolean")
    
    # Validate meets_required_shift_availability: must be actual boolean
    if not isinstance(candidate['meets_required_shift_availability'], bool):
        raise ValueError("Invalid meets_required_shift_availability: must be boolean")
    
    # Helper function to validate numeric fields
    def validate_numeric_field(value, field_name, min_val, max_val):
        # Reject boolean values
        if isinstance(value, bool):
            raise ValueError(f"Invalid {field_name}: boolean not allowed")
        # Reject string values
        if isinstance(value, str):
            raise ValueError(f"Invalid {field_name}: string not allowed")
        # Must be numeric (int or float)
        if not isinstance(value, (int, float)):
            raise ValueError(f"Invalid {field_name}: must be numeric")
        # Reject NaN and infinity
        if math.isnan(value) or math.isinf(value):
            raise ValueError(f"Invalid {field_name}: NaN/infinity not allowed")
        # Must be within range
        if value < min_val or value > max_val:
            raise ValueError(f"Invalid {field_name}: out of valid range")
        return value
    
    # Validate numeric fields
    experience_years = validate_numeric_field(
        candidate['relevant_experience_years'],
        'relevant_experience_years', 0, 40
    )
    
    clinical_score = validate_numeric_field(
        candidate['clinical_assessment_score'],
        'clinical_assessment_score', 0, 100
    )
    
    communication_score = validate_numeric_field(
        candidate['communication_assessment_score'],
        'communication_assessment_score', 0, 100
    )
    
    patient_care_score = validate_numeric_field(
        candidate['patient_care_assessment_score'],
        'patient_care_assessment_score', 0, 100
    )
    
    # Check mandatory eligibility conditions
    has_valid_registration = candidate['has_valid_registration']
    meets_shift_availability = candidate['meets_required_shift_availability']
    
    eligible = has_valid_registration and meets_shift_availability
    
    # If not eligible, return score of 0
    if not eligible:
        return {
            'candidate_id': candidate_id,
            'eligible': False,
            'suitability_score': 0
        }
    
    # Calculate suitability score for eligible candidates
    # Experience contribution: capped at 10 years, normalized to 0-100 range
    experience_cap = 10.0
    experience_normalized = min(experience_years, experience_cap) / experience_cap
    experience_contribution = experience_normalized * 100.0
    
    # Assessment contribution: average of three assessment scores
    assessment_average = (clinical_score + communication_score + patient_care_score) / 3.0
    
    # Overall suitability: weighted combination
    # 30% weight on experience, 70% weight on average assessment scores
    suitability = 0.3 * experience_contribution + 0.7 * assessment_average
    
    # Convert to integer score and ensure it's in valid range
    suitability_score = int(round(suitability))
    suitability_score = max(0, min(100, suitability_score))
    
    return {
        'candidate_id': candidate_id,
        'eligible': True,
        'suitability_score': suitability_score
    }
