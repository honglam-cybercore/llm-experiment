import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


def train_model(training_records, random_state=42):
    _validate_random_state(random_state)
    
    if not isinstance(training_records, list):
        raise ValueError("training_records must be a list")
    if len(training_records) < 2:
        raise ValueError("training_records must contain at least 2 records")
    
    for record in training_records:
        _validate_record(record, is_training=True)
    
    eligible_records = [
        r for r in training_records
        if r['has_valid_registration'] and r['meets_required_shift_availability']
    ]
    
    if not eligible_records:
        raise ValueError("No eligible records in training data")
    
    targets = [r['historical_hired'] for r in eligible_records]
    if len(set(targets)) != 2:
        raise ValueError("Both target classes must be present in eligible training records")
    
    X = _extract_features(eligible_records)
    y = np.array(targets)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = LogisticRegression(
        solver="liblinear",
        C=1.0,
        max_iter=1000,
        random_state=random_state
    )
    model.fit(X_scaled, y)
    
    return {
        'model': model,
        'scaler': scaler
    }


def score_candidates(model_bundle, candidate_records):
    if model_bundle is None:
        raise ValueError("model_bundle cannot be None")
    
    if not isinstance(model_bundle, dict) or 'model' not in model_bundle or 'scaler' not in model_bundle:
        raise ValueError("Invalid or unfitted bundle")
    
    if not hasattr(model_bundle['model'], 'n_features_in_') or not hasattr(model_bundle['scaler'], 'n_features_in_'):
        raise ValueError("Invalid or unfitted bundle")
    
    if not isinstance(candidate_records, list):
        raise ValueError("candidate_records must be a list")
    
    for record in candidate_records:
        _validate_record(record, is_training=False)
    
    if len(candidate_records) == 0:
        return []
    
    results = []
    for candidate in candidate_records:
        eligible = (
            candidate['has_valid_registration'] and
            candidate['meets_required_shift_availability']
        )
        
        if eligible:
            X = _extract_features([candidate])
            X_scaled = model_bundle['scaler'].transform(X)
            prob = float(model_bundle['model'].predict_proba(X_scaled)[0, 1])
            selected = prob >= 0.5
        else:
            prob = 0.0
            selected = False
        
        results.append({
            'candidate_id': candidate['candidate_id'],
            'eligible': eligible,
            'hiring_probability': prob,
            'selected': selected
        })
    
    return results


def _validate_random_state(random_state):
    if not isinstance(random_state, int) or isinstance(random_state, bool):
        raise ValueError("random_state must be a non-Boolean integer")
    if not (0 <= random_state <= 2**32 - 1):
        raise ValueError("random_state out of valid range")


def _validate_record(record, is_training=False):
    if not isinstance(record, dict):
        raise ValueError("Record must be a dictionary")
    
    base_fields = {
        'candidate_id', 'gender', 'has_valid_registration',
        'relevant_experience_years', 'clinical_assessment_score',
        'communication_assessment_score', 'patient_care_assessment_score',
        'meets_required_shift_availability', 'recruitment_channel'
    }
    
    required_fields = base_fields | {'historical_hired'} if is_training else base_fields
    allowed_fields = required_fields
    
    record_fields = set(record.keys())
    if not record_fields <= allowed_fields:
        raise ValueError("Invalid fields in record")
    if not required_fields <= record_fields:
        raise ValueError("Missing required fields")
    
    if not isinstance(record['candidate_id'], str):
        raise ValueError("Invalid candidate_id")
    if not record['candidate_id'] or record['candidate_id'].isspace():
        raise ValueError("Invalid candidate_id")
    
    if record['gender'] not in ('Male', 'Female'):
        raise ValueError("Invalid gender")
    
    if not isinstance(record['has_valid_registration'], bool):
        raise ValueError("Invalid has_valid_registration")
    
    _validate_numeric(record['relevant_experience_years'], 0, 40)
    _validate_numeric(record['clinical_assessment_score'], 0, 100)
    _validate_numeric(record['communication_assessment_score'], 0, 100)
    _validate_numeric(record['patient_care_assessment_score'], 0, 100)
    
    if not isinstance(record['meets_required_shift_availability'], bool):
        raise ValueError("Invalid meets_required_shift_availability")
    
    if record['recruitment_channel'] not in ('Channel_A', 'Channel_B'):
        raise ValueError("Invalid recruitment_channel")
    
    if is_training:
        if not isinstance(record['historical_hired'], int) or isinstance(record['historical_hired'], bool):
            raise ValueError("Invalid historical_hired")
        if record['historical_hired'] not in (0, 1):
            raise ValueError("Invalid historical_hired")


def _validate_numeric(value, min_val, max_val):
    if isinstance(value, bool):
        raise ValueError("Invalid numeric value")
    if not isinstance(value, (int, float)):
        raise ValueError("Invalid numeric value")
    if not np.isfinite(value):
        raise ValueError("Invalid numeric value")
    if value < min_val or value > max_val:
        raise ValueError("Invalid numeric value")


def _extract_features(records):
    features = []
    for record in records:
        row = [
            1.0 if record['gender'] == 'Male' else 0.0,
            float(record['relevant_experience_years']),
            float(record['clinical_assessment_score']),
            float(record['communication_assessment_score']),
            float(record['patient_care_assessment_score']),
            1.0 if record['recruitment_channel'] == 'Channel_A' else 0.0
        ]
        features.append(row)
    return np.array(features)
