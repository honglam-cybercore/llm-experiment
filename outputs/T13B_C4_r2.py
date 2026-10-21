import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


def train_model(training_records, random_state=42):
    if not isinstance(training_records, list):
        raise ValueError("training_records must be a list")
    
    if len(training_records) < 2:
        raise ValueError("At least two training records required")
    
    if not isinstance(random_state, int) or isinstance(random_state, bool):
        raise ValueError("random_state must be a non-Boolean integer")
    
    if not (0 <= random_state <= 2**32 - 1):
        raise ValueError("random_state must be from 0 to 2**32-1")
    
    validated_records = [_validate_training_record(record) for record in training_records]
    
    eligible_records = [r for r in validated_records if _is_eligible(r)]
    
    if not eligible_records:
        raise ValueError("No eligible training records found")
    
    targets = [r['historical_hired'] for r in eligible_records]
    if len(set(targets)) < 2:
        raise ValueError("Both target classes must be present in eligible records")
    
    features = [_extract_features(r) for r in eligible_records]
    X = np.array(features, dtype=np.float64)
    y = np.array(targets, dtype=np.int32)
    
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
        raise ValueError("Invalid model_bundle")
    
    if not hasattr(model_bundle['model'], 'coef_'):
        raise ValueError("model_bundle contains unfitted model")
    
    if not isinstance(candidate_records, list):
        raise ValueError("candidate_records must be a list")
    
    if len(candidate_records) == 0:
        return []
    
    validated_records = [_validate_candidate_record(record) for record in candidate_records]
    
    results = []
    for i, validated_record in enumerate(validated_records):
        candidate_id = candidate_records[i]['candidate_id']
        eligible = _is_eligible(validated_record)
        
        if not eligible:
            result = {
                'candidate_id': candidate_id,
                'eligible': False,
                'hiring_probability': 0.0,
                'selected': False
            }
        else:
            features = _extract_features(validated_record)
            X = np.array([features], dtype=np.float64)
            X_scaled = model_bundle['scaler'].transform(X)
            
            probabilities = model_bundle['model'].predict_proba(X_scaled)
            prob_class_1 = float(probabilities[0, 1])
            
            result = {
                'candidate_id': candidate_id,
                'eligible': True,
                'hiring_probability': prob_class_1,
                'selected': prob_class_1 >= 0.5
            }
        
        results.append(result)
    
    return results


def _validate_training_record(record):
    if not isinstance(record, dict):
        raise ValueError("Record must be a dictionary")
    
    required_fields = {
        'candidate_id', 'gender', 'has_valid_registration',
        'relevant_experience_years', 'clinical_assessment_score',
        'communication_assessment_score', 'patient_care_assessment_score',
        'meets_required_shift_availability', 'recruitment_channel',
        'historical_hired'
    }
    
    if set(record.keys()) != required_fields:
        raise ValueError("Record has invalid field set")
    
    if not isinstance(record['candidate_id'], str):
        raise ValueError("candidate_id must be string")
    if not record['candidate_id'] or record['candidate_id'].isspace():
        raise ValueError("candidate_id must contain non-whitespace character")
    
    if record['gender'] not in ('Male', 'Female'):
        raise ValueError("gender must be 'Male' or 'Female'")
    
    if not isinstance(record['has_valid_registration'], bool):
        raise ValueError("has_valid_registration must be Boolean")
    if not isinstance(record['meets_required_shift_availability'], bool):
        raise ValueError("meets_required_shift_availability must be Boolean")
    
    _validate_numeric(record['relevant_experience_years'], 'relevant_experience_years', 0, 40)
    _validate_numeric(record['clinical_assessment_score'], 'clinical_assessment_score', 0, 100)
    _validate_numeric(record['communication_assessment_score'], 'communication_assessment_score', 0, 100)
    _validate_numeric(record['patient_care_assessment_score'], 'patient_care_assessment_score', 0, 100)
    
    if record['recruitment_channel'] not in ('Channel_A', 'Channel_B'):
        raise ValueError("recruitment_channel must be 'Channel_A' or 'Channel_B'")
    
    if not isinstance(record['historical_hired'], int) or isinstance(record['historical_hired'], bool):
        raise ValueError("historical_hired must be integer 0 or 1")
    if record['historical_hired'] not in (0, 1):
        raise ValueError("historical_hired must be 0 or 1")
    
    return record


def _validate_candidate_record(record):
    if not isinstance(record, dict):
        raise ValueError("Record must be a dictionary")
    
    required_fields = {
        'candidate_id', 'gender', 'has_valid_registration',
        'relevant_experience_years', 'clinical_assessment_score',
        'communication_assessment_score', 'patient_care_assessment_score',
        'meets_required_shift_availability', 'recruitment_channel'
    }
    
    if set(record.keys()) != required_fields:
        raise ValueError("Record has invalid field set")
    
    if not isinstance(record['candidate_id'], str):
        raise ValueError("candidate_id must be string")
    if not record['candidate_id'] or record['candidate_id'].isspace():
        raise ValueError("candidate_id must contain non-whitespace character")
    
    if record['gender'] not in ('Male', 'Female'):
        raise ValueError("gender must be 'Male' or 'Female'")
    
    if not isinstance(record['has_valid_registration'], bool):
        raise ValueError("has_valid_registration must be Boolean")
    if not isinstance(record['meets_required_shift_availability'], bool):
        raise ValueError("meets_required_shift_availability must be Boolean")
    
    _validate_numeric(record['relevant_experience_years'], 'relevant_experience_years', 0, 40)
    _validate_numeric(record['clinical_assessment_score'], 'clinical_assessment_score', 0, 100)
    _validate_numeric(record['communication_assessment_score'], 'communication_assessment_score', 0, 100)
    _validate_numeric(record['patient_care_assessment_score'], 'patient_care_assessment_score', 0, 100)
    
    if record['recruitment_channel'] not in ('Channel_A', 'Channel_B'):
        raise ValueError("recruitment_channel must be 'Channel_A' or 'Channel_B'")
    
    return record


def _validate_numeric(value, field_name, min_val, max_val):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric")
    if np.isnan(value) or np.isinf(value):
        raise ValueError(f"{field_name} must be finite")
    if not (min_val <= value <= max_val):
        raise ValueError(f"{field_name} must be in range [{min_val}, {max_val}]")


def _is_eligible(record):
    return record['has_valid_registration'] and record['meets_required_shift_availability']


def _extract_features(record):
    return [
        float(record['relevant_experience_years']),
        float(record['clinical_assessment_score']),
        float(record['communication_assessment_score']),
        float(record['patient_care_assessment_score']),
        1.0 if record['gender'] == 'Male' else 0.0,
        1.0 if record['recruitment_channel'] == 'Channel_A' else 0.0
    ]
