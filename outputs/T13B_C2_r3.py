import numpy as np
from sklearn.linear_model import LogisticRegression

def train_model(training_records, random_state=42):
    if not isinstance(random_state, int) or isinstance(random_state, bool):
        raise ValueError("random_state must be a non-Boolean integer")
    if random_state < 0 or random_state >= 2**32:
        raise ValueError("random_state must be between 0 and 2**32-1")
    
    if not isinstance(training_records, list) or len(training_records) < 2:
        raise ValueError("training_records must be a non-empty list with at least 2 records")
    
    eligible_records = []
    targets = []
    
    for record in training_records:
        _validate_record(record, is_training=True)
        
        if record['has_valid_registration'] and record['meets_required_shift_availability']:
            eligible_records.append(record)
            targets.append(record['historical_hired'])
    
    unique_targets = set(targets)
    if len(unique_targets) != 2 or unique_targets != {0, 1}:
        raise ValueError("Training data must contain both target classes (0 and 1) among eligible records")
    
    X = _build_feature_matrix(eligible_records)
    y = np.array(targets, dtype=int)
    
    model = LogisticRegression(solver='liblinear', C=1.0, max_iter=1000, random_state=random_state)
    model.fit(X, y)
    
    return {'model': model}

def score_candidates(model_bundle, candidate_records):
    if model_bundle is None:
        raise ValueError("model_bundle cannot be None")
    if not isinstance(model_bundle, dict) or 'model' not in model_bundle:
        raise ValueError("Invalid or unfitted bundle")
    
    if not isinstance(candidate_records, list):
        raise ValueError("candidate_records must be a list")
    
    for record in candidate_records:
        _validate_record(record, is_training=False)
    
    if len(candidate_records) == 0:
        return []
    
    results = []
    for record in candidate_records:
        candidate_id = record['candidate_id']
        is_eligible = record['has_valid_registration'] and record['meets_required_shift_availability']
        
        if is_eligible:
            X = _build_feature_matrix([record])
            proba = model_bundle['model'].predict_proba(X)[0]
            hiring_probability = float(proba[1])
            selected = hiring_probability >= 0.5
        else:
            hiring_probability = 0.0
            selected = False
        
        results.append({
            'candidate_id': candidate_id,
            'eligible': is_eligible,
            'hiring_probability': hiring_probability,
            'selected': selected
        })
    
    return results

def _validate_record(record, is_training=False):
    if not isinstance(record, dict):
        raise ValueError("Record must be a dictionary")
    
    required_fields = {
        'candidate_id', 'gender', 'has_valid_registration',
        'relevant_experience_years', 'clinical_assessment_score',
        'communication_assessment_score', 'patient_care_assessment_score',
        'meets_required_shift_availability', 'recruitment_channel'
    }
    
    if is_training:
        required_fields = required_fields | {'historical_hired'}
    
    if set(record.keys()) != required_fields:
        raise ValueError("Record has unknown or missing fields")
    
    if not isinstance(record['candidate_id'], str):
        raise ValueError("candidate_id must be a string")
    if not record['candidate_id'] or record['candidate_id'].isspace():
        raise ValueError("candidate_id must contain non-whitespace characters")
    
    if record['gender'] not in ('Male', 'Female'):
        raise ValueError("gender must be 'Male' or 'Female'")
    
    if not isinstance(record['has_valid_registration'], bool):
        raise ValueError("has_valid_registration must be Boolean")
    
    exp = record['relevant_experience_years']
    if isinstance(exp, bool) or not isinstance(exp, (int, float)):
        raise ValueError("relevant_experience_years must be numeric")
    if not np.isfinite(exp) or not (0 <= exp <= 40):
        raise ValueError("relevant_experience_years must be finite and in [0, 40]")
    
    score = record['clinical_assessment_score']
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        raise ValueError("clinical_assessment_score must be numeric")
    if not np.isfinite(score) or not (0 <= score <= 100):
        raise ValueError("clinical_assessment_score must be finite and in [0, 100]")
    
    score = record['communication_assessment_score']
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        raise ValueError("communication_assessment_score must be numeric")
    if not np.isfinite(score) or not (0 <= score <= 100):
        raise ValueError("communication_assessment_score must be finite and in [0, 100]")
    
    score = record['patient_care_assessment_score']
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        raise ValueError("patient_care_assessment_score must be numeric")
    if not np.isfinite(score) or not (0 <= score <= 100):
        raise ValueError("patient_care_assessment_score must be finite and in [0, 100]")
    
    if not isinstance(record['meets_required_shift_availability'], bool):
        raise ValueError("meets_required_shift_availability must be Boolean")
    
    if record['recruitment_channel'] not in ('Channel_A', 'Channel_B'):
        raise ValueError("recruitment_channel must be 'Channel_A' or 'Channel_B'")
    
    if is_training:
        hired = record['historical_hired']
        if isinstance(hired, bool) or not isinstance(hired, int):
            raise ValueError("historical_hired must be int 0 or 1")
        if hired not in (0, 1):
            raise ValueError("historical_hired must be 0 or 1")

def _build_feature_matrix(records):
    features = []
    for record in records:
        row = [
            float(record['relevant_experience_years']),
            float(record['clinical_assessment_score']),
            float(record['communication_assessment_score']),
            float(record['patient_care_assessment_score']),
            1.0 if record['gender'] == 'Male' else 0.0,
            1.0 if record['recruitment_channel'] == 'Channel_A' else 0.0
        ]
        features.append(row)
    return np.array(features, dtype=float)
