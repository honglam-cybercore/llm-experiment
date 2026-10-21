import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


def _validate_candidate_fields(record, is_training=False):
    if not isinstance(record, dict):
        raise ValueError("Record must be a dictionary")
    
    required_fields = {
        'candidate_id', 'gender', 'has_valid_registration',
        'relevant_experience_years', 'clinical_assessment_score',
        'communication_assessment_score', 'patient_care_assessment_score',
        'meets_required_shift_availability', 'recruitment_channel'
    }
    
    if is_training:
        required_fields.add('historical_hired')
    
    if set(record.keys()) != required_fields:
        raise ValueError("Invalid field set in record")
    
    cid = record['candidate_id']
    if not isinstance(cid, str) or not cid.strip():
        raise ValueError("candidate_id must be a non-whitespace string")
    
    if record['gender'] not in ("Male", "Female"):
        raise ValueError("gender must be 'Male' or 'Female'")
    
    if not isinstance(record['has_valid_registration'], bool):
        raise ValueError("has_valid_registration must be a boolean")
    
    val = record['relevant_experience_years']
    if isinstance(val, bool):
        raise ValueError("relevant_experience_years cannot be a boolean")
    if not isinstance(val, (int, float)):
        raise ValueError("relevant_experience_years must be int or float")
    if not np.isfinite(val):
        raise ValueError("relevant_experience_years must be finite")
    if not (0 <= val <= 40):
        raise ValueError("relevant_experience_years must be between 0 and 40")
    
    val = record['clinical_assessment_score']
    if isinstance(val, bool):
        raise ValueError("clinical_assessment_score cannot be a boolean")
    if not isinstance(val, (int, float)):
        raise ValueError("clinical_assessment_score must be int or float")
    if not np.isfinite(val):
        raise ValueError("clinical_assessment_score must be finite")
    if not (0 <= val <= 100):
        raise ValueError("clinical_assessment_score must be between 0 and 100")
    
    val = record['communication_assessment_score']
    if isinstance(val, bool):
        raise ValueError("communication_assessment_score cannot be a boolean")
    if not isinstance(val, (int, float)):
        raise ValueError("communication_assessment_score must be int or float")
    if not np.isfinite(val):
        raise ValueError("communication_assessment_score must be finite")
    if not (0 <= val <= 100):
        raise ValueError("communication_assessment_score must be between 0 and 100")
    
    val = record['patient_care_assessment_score']
    if isinstance(val, bool):
        raise ValueError("patient_care_assessment_score cannot be a boolean")
    if not isinstance(val, (int, float)):
        raise ValueError("patient_care_assessment_score must be int or float")
    if not np.isfinite(val):
        raise ValueError("patient_care_assessment_score must be finite")
    if not (0 <= val <= 100):
        raise ValueError("patient_care_assessment_score must be between 0 and 100")
    
    if not isinstance(record['meets_required_shift_availability'], bool):
        raise ValueError("meets_required_shift_availability must be a boolean")
    
    if record['recruitment_channel'] not in ("Channel_A", "Channel_B"):
        raise ValueError("recruitment_channel must be 'Channel_A' or 'Channel_B'")
    
    if is_training:
        val = record['historical_hired']
        if isinstance(val, bool):
            raise ValueError("historical_hired cannot be a boolean")
        if not isinstance(val, int):
            raise ValueError("historical_hired must be an integer")
        if val not in (0, 1):
            raise ValueError("historical_hired must be 0 or 1")


def _is_eligible(record):
    return record['has_valid_registration'] and record['meets_required_shift_availability']


def _extract_features(record):
    return {
        'relevant_experience_years': record['relevant_experience_years'],
        'clinical_assessment_score': record['clinical_assessment_score'],
        'communication_assessment_score': record['communication_assessment_score'],
        'patient_care_assessment_score': record['patient_care_assessment_score'],
        'gender_Male': 1 if record['gender'] == 'Male' else 0,
        'channel_Channel_A': 1 if record['recruitment_channel'] == 'Channel_A' else 0,
    }


def train_model(training_records, random_state=42):
    if not isinstance(random_state, int) or isinstance(random_state, bool):
        raise ValueError("random_state must be a non-Boolean integer")
    if not (0 <= random_state <= 2**32 - 1):
        raise ValueError("random_state must be between 0 and 2**32-1")
    
    if not isinstance(training_records, list) or len(training_records) < 2:
        raise ValueError("training_records must be a list with at least 2 records")
    
    for record in training_records:
        _validate_candidate_fields(record, is_training=True)
    
    eligible_records = [r for r in training_records if _is_eligible(r)]
    
    if len(eligible_records) == 0:
        raise ValueError("No eligible records found in training data")
    
    targets = [r['historical_hired'] for r in eligible_records]
    if 0 not in targets or 1 not in targets:
        raise ValueError("Both target classes must be present in eligible training records")
    
    features_list = [_extract_features(r) for r in eligible_records]
    X = pd.DataFrame(features_list)
    y = np.array([r['historical_hired'] for r in eligible_records])
    
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
        'feature_columns': list(X.columns)
    }


def score_candidates(model_bundle, candidate_records):
    if model_bundle is None:
        raise ValueError("model_bundle cannot be None")
    if not isinstance(model_bundle, dict):
        raise ValueError("model_bundle must be a dict")
    required_bundle_keys = {'model', 'scaler', 'feature_columns'}
    if not required_bundle_keys.issubset(set(model_bundle.keys())):
        raise ValueError("model_bundle is not a valid fitted bundle")
    
    if not isinstance(candidate_records, list):
        raise ValueError("candidate_records must be a list")
    
    if len(candidate_records) == 0:
        return []
    
    for record in candidate_records:
        _validate_candidate_fields(record, is_training=False)
    
    results = []
    for record in candidate_records:
        candidate_id = record['candidate_id']
        eligible = _is_eligible(record)
        
        if eligible:
            features = _extract_features(record)
            X = pd.DataFrame([features])
            X = X[model_bundle['feature_columns']]
            X_scaled = model_bundle['scaler'].transform(X)
            proba = model_bundle['model'].predict_proba(X_scaled)[0]
            hiring_probability = float(proba[1])
            selected = hiring_probability >= 0.5
        else:
            hiring_probability = 0.0
            selected = False
        
        results.append({
            'candidate_id': candidate_id,
            'eligible': eligible,
            'hiring_probability': hiring_probability,
            'selected': selected
        })
    
    return results
