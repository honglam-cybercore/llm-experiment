import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


def _validate_candidate_structure(record, allow_historical_hired=False):
    if not isinstance(record, dict):
        raise ValueError("Record must be a dictionary")
    
    required_fields = {
        'candidate_id', 'gender', 'has_valid_registration',
        'relevant_experience_years', 'clinical_assessment_score',
        'communication_assessment_score', 'patient_care_assessment_score',
        'meets_required_shift_availability', 'recruitment_channel'
    }
    
    if allow_historical_hired:
        required_fields.add('historical_hired')
    
    record_fields = set(record.keys())
    if record_fields != required_fields:
        raise ValueError("Record has invalid fields")


def _validate_candidate_values(record):
    candidate_id = record['candidate_id']
    if not isinstance(candidate_id, str):
        raise ValueError("candidate_id must be a string")
    if not candidate_id or candidate_id.isspace():
        raise ValueError("candidate_id must contain non-whitespace characters")
    
    if record['gender'] not in ('Male', 'Female'):
        raise ValueError("gender must be 'Male' or 'Female'")
    
    if not isinstance(record['has_valid_registration'], bool):
        raise ValueError("has_valid_registration must be a boolean")
    if not isinstance(record['meets_required_shift_availability'], bool):
        raise ValueError("meets_required_shift_availability must be a boolean")
    
    numeric_fields = {
        'relevant_experience_years': (0, 40),
        'clinical_assessment_score': (0, 100),
        'communication_assessment_score': (0, 100),
        'patient_care_assessment_score': (0, 100)
    }
    
    for field, (min_val, max_val) in numeric_fields.items():
        val = record[field]
        
        if isinstance(val, bool):
            raise ValueError(f"{field} cannot be a boolean")
        if not isinstance(val, (int, float)):
            raise ValueError(f"{field} must be int or float")
        if not np.isfinite(val):
            raise ValueError(f"{field} must be finite")
        if not (min_val <= val <= max_val):
            raise ValueError(f"{field} out of range")
    
    if record['recruitment_channel'] not in ('Channel_A', 'Channel_B'):
        raise ValueError("recruitment_channel must be 'Channel_A' or 'Channel_B'")


def _is_eligible(record):
    return record['has_valid_registration'] and record['meets_required_shift_availability']


def _extract_features(record):
    return [
        1.0 if record['gender'] == 'Male' else 0.0,
        float(record['relevant_experience_years']),
        float(record['clinical_assessment_score']),
        float(record['communication_assessment_score']),
        float(record['patient_care_assessment_score']),
        1.0 if record['recruitment_channel'] == 'Channel_B' else 0.0
    ]


def train_model(training_records, random_state=42):
    if not isinstance(random_state, int) or isinstance(random_state, bool):
        raise ValueError("random_state must be a non-boolean integer")
    if not (0 <= random_state < 2**32):
        raise ValueError("random_state out of valid range")
    
    if not isinstance(training_records, list):
        raise ValueError("training_records must be a list")
    if len(training_records) < 2:
        raise ValueError("training_records must contain at least 2 records")
    
    eligible_records = []
    
    for record in training_records:
        _validate_candidate_structure(record, allow_historical_hired=True)
        _validate_candidate_values(record)
        
        hist_hired = record['historical_hired']
        if not isinstance(hist_hired, int) or isinstance(hist_hired, bool):
            raise ValueError("historical_hired must be an integer")
        if hist_hired not in (0, 1):
            raise ValueError("historical_hired must be 0 or 1")
        
        if _is_eligible(record):
            eligible_records.append(record)
    
    if len(eligible_records) == 0:
        raise ValueError("No eligible training records found")
    
    targets = [r['historical_hired'] for r in eligible_records]
    if len(set(targets)) != 2:
        raise ValueError("Both target classes required in eligible training data")
    
    X_list = [_extract_features(r) for r in eligible_records]
    y_list = [r['historical_hired'] for r in eligible_records]
    
    X = np.array(X_list, dtype=np.float64)
    y = np.array(y_list, dtype=np.int64)
    
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
        'fitted': True
    }


def score_candidates(model_bundle, candidate_records):
    if model_bundle is None:
        raise ValueError("model_bundle cannot be None")
    if not isinstance(model_bundle, dict):
        raise ValueError("model_bundle must be a dictionary")
    if not model_bundle.get('fitted', False):
        raise ValueError("model_bundle is not fitted")
    
    if not isinstance(candidate_records, list):
        raise ValueError("candidate_records must be a list")
    
    if len(candidate_records) == 0:
        return []
    
    for record in candidate_records:
        _validate_candidate_structure(record, allow_historical_hired=False)
        _validate_candidate_values(record)
    
    results = []
    
    for record in candidate_records:
        eligible = _is_eligible(record)
        
        if eligible:
            features = _extract_features(record)
            X = np.array([features], dtype=np.float64)
            X_scaled = model_bundle['scaler'].transform(X)
            
            prob = float(model_bundle['model'].predict_proba(X_scaled)[0, 1])
            selected = prob >= 0.5
        else:
            prob = 0.0
            selected = False
        
        result = {
            'candidate_id': record['candidate_id'],
            'eligible': eligible,
            'hiring_probability': prob,
            'selected': selected
        }
        results.append(result)
    
    return results
