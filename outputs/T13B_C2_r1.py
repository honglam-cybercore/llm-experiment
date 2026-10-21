import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


def train_model(training_records, random_state=42):
    if not isinstance(training_records, list):
        raise ValueError("training_records must be a list")
    
    if len(training_records) < 2:
        raise ValueError("At least 2 training records required")
    
    if not isinstance(random_state, int) or isinstance(random_state, bool):
        raise ValueError("random_state must be a non-Boolean integer")
    
    if not (0 <= random_state <= 2**32 - 1):
        raise ValueError("random_state must be between 0 and 2**32-1")
    
    for record in training_records:
        _validate_record(record, is_training=True)
    
    eligible = [r for r in training_records if r['has_valid_registration'] and r['meets_required_shift_availability']]
    
    if not eligible:
        raise ValueError("No eligible training records")
    
    targets = [r['historical_hired'] for r in eligible]
    if len(set(targets)) < 2:
        raise ValueError("Both target classes required in eligible records")
    
    X = _extract_features(eligible)
    y = np.array([r['historical_hired'] for r in eligible])
    
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
        'scaler': scaler,
    }


def score_candidates(model_bundle, candidate_records):
    if model_bundle is None:
        raise ValueError("model_bundle cannot be None")
    
    if not isinstance(model_bundle, dict):
        raise ValueError("model_bundle must be a dict")
    
    if 'model' not in model_bundle or 'scaler' not in model_bundle:
        raise ValueError("Invalid or unfitted bundle")
    
    if not isinstance(candidate_records, list):
        raise ValueError("candidate_records must be a list")
    
    if len(candidate_records) == 0:
        return []
    
    for record in candidate_records:
        _validate_record(record, is_training=False)
    
    results = []
    for record in candidate_records:
        eligible = record['has_valid_registration'] and record['meets_required_shift_availability']
        
        if eligible:
            X = _extract_features([record])
            X_scaled = model_bundle['scaler'].transform(X)
            prob = float(model_bundle['model'].predict_proba(X_scaled)[0][1])
            selected = prob >= 0.5
        else:
            prob = 0.0
            selected = False
        
        results.append({
            'candidate_id': record['candidate_id'],
            'eligible': eligible,
            'hiring_probability': prob,
            'selected': selected
        })
    
    return results


def _validate_record(record, is_training=False):
    if not isinstance(record, dict):
        raise ValueError("Record must be dictionary")
    
    expected = {
        'candidate_id', 'gender', 'has_valid_registration',
        'relevant_experience_years', 'clinical_assessment_score',
        'communication_assessment_score', 'patient_care_assessment_score',
        'meets_required_shift_availability', 'recruitment_channel'
    }
    
    if is_training:
        expected.add('historical_hired')
    
    if set(record.keys()) != expected:
        raise ValueError("Invalid fields in record")
    
    if not isinstance(record['candidate_id'], str):
        raise ValueError("candidate_id must be string")
    if not record['candidate_id'] or record['candidate_id'].isspace():
        raise ValueError("candidate_id must contain non-whitespace")
    
    if record['gender'] not in ('Male', 'Female'):
        raise ValueError("gender must be Male or Female")
    
    if not isinstance(record['has_valid_registration'], bool):
        raise ValueError("has_valid_registration must be bool")
    
    if isinstance(record['relevant_experience_years'], bool):
        raise ValueError("relevant_experience_years cannot be bool")
    if not isinstance(record['relevant_experience_years'], (int, float)):
        raise ValueError("relevant_experience_years must be numeric")
    val = record['relevant_experience_years']
    if not np.isfinite(val) or not (0 <= val <= 40):
        raise ValueError("relevant_experience_years out of range")
    
    if isinstance(record['clinical_assessment_score'], bool):
        raise ValueError("clinical_assessment_score cannot be bool")
    if not isinstance(record['clinical_assessment_score'], (int, float)):
        raise ValueError("clinical_assessment_score must be numeric")
    val = record['clinical_assessment_score']
    if not np.isfinite(val) or not (0 <= val <= 100):
        raise ValueError("clinical_assessment_score out of range")
    
    if isinstance(record['communication_assessment_score'], bool):
        raise ValueError("communication_assessment_score cannot be bool")
    if not isinstance(record['communication_assessment_score'], (int, float)):
        raise ValueError("communication_assessment_score must be numeric")
    val = record['communication_assessment_score']
    if not np.isfinite(val) or not (0 <= val <= 100):
        raise ValueError("communication_assessment_score out of range")
    
    if isinstance(record['patient_care_assessment_score'], bool):
        raise ValueError("patient_care_assessment_score cannot be bool")
    if not isinstance(record['patient_care_assessment_score'], (int, float)):
        raise ValueError("patient_care_assessment_score must be numeric")
    val = record['patient_care_assessment_score']
    if not np.isfinite(val) or not (0 <= val <= 100):
        raise ValueError("patient_care_assessment_score out of range")
    
    if not isinstance(record['meets_required_shift_availability'], bool):
        raise ValueError("meets_required_shift_availability must be bool")
    
    if record['recruitment_channel'] not in ('Channel_A', 'Channel_B'):
        raise ValueError("recruitment_channel must be Channel_A or Channel_B")
    
    if is_training:
        if isinstance(record['historical_hired'], bool):
            raise ValueError("historical_hired cannot be bool")
        if not isinstance(record['historical_hired'], int):
            raise ValueError("historical_hired must be int")
        if record['historical_hired'] not in (0, 1):
            raise ValueError("historical_hired must be 0 or 1")


def _extract_features(records):
    features = []
    for record in records:
        features.append([
            float(record['relevant_experience_years']),
            float(record['clinical_assessment_score']),
            float(record['communication_assessment_score']),
            float(record['patient_care_assessment_score']),
            1.0 if record['gender'] == 'Male' else 0.0,
            1.0 if record['recruitment_channel'] == 'Channel_A' else 0.0,
        ])
    return np.array(features, dtype=np.float64)
