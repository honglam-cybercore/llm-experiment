import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression


def train_model(training_records, random_state=42):
    if not isinstance(random_state, int) or isinstance(random_state, bool):
        raise ValueError("random_state must be a non-Boolean Python integer")
    if not (0 <= random_state <= 2**32 - 1):
        raise ValueError("random_state must be between 0 and 2**32-1")
    
    if not isinstance(training_records, list):
        raise ValueError("training_records must be a list")
    if len(training_records) < 2:
        raise ValueError("training_records must contain at least 2 records")
    
    eligible_records = []
    for record in training_records:
        _validate_candidate_dict(record, is_training=True)
        if record.get('has_valid_registration') and record.get('meets_required_shift_availability'):
            eligible_records.append(record)
    
    hired_values = [r.get('historical_hired') for r in eligible_records]
    if 0 not in hired_values or 1 not in hired_values:
        raise ValueError("Both target classes required among eligible records")
    
    X = _extract_features(eligible_records)
    y = np.array([r['historical_hired'] for r in eligible_records], dtype=int)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = LogisticRegression(
        solver='liblinear',
        C=1.0,
        max_iter=1000,
        random_state=random_state
    )
    model.fit(X_scaled, y)
    
    return {
        'model': model,
        'scaler': scaler,
    }


def score_candidates(model_bundle, candidate_records):
    if model_bundle is None:
        raise ValueError("model_bundle cannot be None")
    if not isinstance(model_bundle, dict) or 'model' not in model_bundle or 'scaler' not in model_bundle:
        raise ValueError("Invalid or unfitted model_bundle")
    
    if not isinstance(candidate_records, list):
        raise ValueError("candidate_records must be a list")
    
    if len(candidate_records) == 0:
        return []
    
    for record in candidate_records:
        _validate_candidate_dict(record, is_training=False)
    
    results = []
    for record in candidate_records:
        candidate_id = record['candidate_id']
        is_eligible = (
            record.get('has_valid_registration') and 
            record.get('meets_required_shift_availability')
        )
        
        if is_eligible:
            X = _extract_features([record])
            X_scaled = model_bundle['scaler'].transform(X)
            proba = model_bundle['model'].predict_proba(X_scaled)[0][1]
            hired_prob = float(proba)
            selected = hired_prob >= 0.5
        else:
            hired_prob = 0.0
            selected = False
        
        results.append({
            'candidate_id': candidate_id,
            'eligible': is_eligible,
            'hiring_probability': hired_prob,
            'selected': selected
        })
    
    return results


def _validate_candidate_dict(record, is_training=False):
    if not isinstance(record, dict):
        raise ValueError("Record must be a dictionary")
    
    base_fields = {
        'candidate_id', 'gender', 'has_valid_registration',
        'relevant_experience_years', 'clinical_assessment_score',
        'communication_assessment_score', 'patient_care_assessment_score',
        'meets_required_shift_availability', 'recruitment_channel'
    }
    
    if is_training:
        base_fields.add('historical_hired')
    
    record_fields = set(record.keys())
    if record_fields - base_fields:
        raise ValueError("Record contains unknown fields")
    
    required = base_fields if is_training else base_fields - {'historical_hired'}
    if required - record_fields:
        raise ValueError("Record is missing required fields")
    
    if not isinstance(record['candidate_id'], str):
        raise ValueError("candidate_id must be a string")
    if not record['candidate_id'] or record['candidate_id'].isspace():
        raise ValueError("candidate_id must contain non-whitespace character")
    
    if record['gender'] not in ('Male', 'Female'):
        raise ValueError("gender must be 'Male' or 'Female'")
    
    if not isinstance(record['has_valid_registration'], bool):
        raise ValueError("has_valid_registration must be a Boolean")
    
    _validate_numeric_field(record['relevant_experience_years'], 0, 40)
    _validate_numeric_field(record['clinical_assessment_score'], 0, 100)
    _validate_numeric_field(record['communication_assessment_score'], 0, 100)
    _validate_numeric_field(record['patient_care_assessment_score'], 0, 100)
    
    if not isinstance(record['meets_required_shift_availability'], bool):
        raise ValueError("meets_required_shift_availability must be a Boolean")
    
    if record['recruitment_channel'] not in ('Channel_A', 'Channel_B'):
        raise ValueError("recruitment_channel must be 'Channel_A' or 'Channel_B'")
    
    if is_training:
        val = record['historical_hired']
        if not isinstance(val, int) or isinstance(val, bool):
            raise ValueError("historical_hired must be an integer 0 or 1")
        if val not in (0, 1):
            raise ValueError("historical_hired must be 0 or 1")


def _validate_numeric_field(value, min_val, max_val):
    if isinstance(value, bool):
        raise ValueError("Numeric field cannot be a Boolean")
    if not isinstance(value, (int, float)):
        raise ValueError("Numeric field must be int or float")
    if not np.isfinite(value):
        raise ValueError("Numeric field must be finite")
    if not (min_val <= value <= max_val):
        raise ValueError(f"Numeric field must be between {min_val} and {max_val}")


def _extract_features(records):
    features = []
    for record in records:
        feature_vector = [
            record['relevant_experience_years'],
            record['clinical_assessment_score'],
            record['communication_assessment_score'],
            record['patient_care_assessment_score'],
            1.0 if record['gender'] == 'Male' else 0.0,
            1.0 if record['recruitment_channel'] == 'Channel_A' else 0.0,
        ]
        features.append(feature_vector)
    
    return np.array(features, dtype=float)
