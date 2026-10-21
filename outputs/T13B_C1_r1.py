import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from typing import List, Dict, Any

def validate_candidate_record(record: Dict[str, Any], training: bool = False) -> None:
    expected_fields = {
        'candidate_id', 'gender', 'has_valid_registration', 'relevant_experience_years',
        'clinical_assessment_score', 'communication_assessment_score',
        'patient_care_assessment_score', 'meets_required_shift_availability',
        'recruitment_channel'
    }
    
    if training:
        expected_fields.add('historical_hired')
    
    actual_fields = set(record.keys())
    if actual_fields != expected_fields:
        raise ValueError("Invalid fields in record")
    
    if not isinstance(record['candidate_id'], str) or not record['candidate_id'] or record['candidate_id'].isspace():
        raise ValueError("Invalid candidate_id")
    
    if record['gender'] not in ("Male", "Female"):
        raise ValueError("Invalid gender")
    
    if not isinstance(record['has_valid_registration'], bool):
        raise ValueError("Invalid has_valid_registration")
    
    exp = record['relevant_experience_years']
    if isinstance(exp, bool) or not isinstance(exp, (int, float)) or not (0 <= exp <= 40) or not np.isfinite(exp):
        raise ValueError("Invalid relevant_experience_years")
    
    cas = record['clinical_assessment_score']
    if isinstance(cas, bool) or not isinstance(cas, (int, float)) or not (0 <= cas <= 100) or not np.isfinite(cas):
        raise ValueError("Invalid clinical_assessment_score")
    
    coms = record['communication_assessment_score']
    if isinstance(coms, bool) or not isinstance(coms, (int, float)) or not (0 <= coms <= 100) or not np.isfinite(coms):
        raise ValueError("Invalid communication_assessment_score")
    
    pcas = record['patient_care_assessment_score']
    if isinstance(pcas, bool) or not isinstance(pcas, (int, float)) or not (0 <= pcas <= 100) or not np.isfinite(pcas):
        raise ValueError("Invalid patient_care_assessment_score")
    
    if not isinstance(record['meets_required_shift_availability'], bool):
        raise ValueError("Invalid meets_required_shift_availability")
    
    if record['recruitment_channel'] not in ("Channel_A", "Channel_B"):
        raise ValueError("Invalid recruitment_channel")
    
    if training:
        hired = record['historical_hired']
        if not isinstance(hired, int) or isinstance(hired, bool) or hired not in (0, 1):
            raise ValueError("Invalid historical_hired")

def extract_features(record: Dict[str, Any]) -> np.ndarray:
    features = [
        1.0 if record['gender'] == 'Male' else 0.0,
        float(record['relevant_experience_years']),
        float(record['clinical_assessment_score']),
        float(record['communication_assessment_score']),
        float(record['patient_care_assessment_score']),
        1.0 if record['recruitment_channel'] == 'Channel_A' else 0.0,
    ]
    return np.array(features)

def train_model(training_records: List[Dict[str, Any]], random_state: int = 42) -> Dict[str, Any]:
    if not isinstance(random_state, int) or isinstance(random_state, bool):
        raise ValueError("random_state must be a non-Boolean integer")
    if not (0 <= random_state <= 2**32 - 1):
        raise ValueError("random_state must be between 0 and 2**32-1")
    
    if not isinstance(training_records, list):
        raise ValueError("training_records must be a list")
    
    if len(training_records) < 2:
        raise ValueError("training_records must have at least 2 records")
    
    for record in training_records:
        if not isinstance(record, dict):
            raise ValueError("Each record must be a dictionary")
        validate_candidate_record(record, training=True)
    
    eligible_records = []
    target_values = []
    
    for record in training_records:
        if record['has_valid_registration'] and record['meets_required_shift_availability']:
            eligible_records.append(record)
            target_values.append(record['historical_hired'])
    
    if len(eligible_records) == 0:
        raise ValueError("No eligible records for training")
    
    unique_targets = set(target_values)
    if len(unique_targets) < 2:
        raise ValueError("Training data must contain both target classes")
    
    X = np.array([extract_features(record) for record in eligible_records])
    y = np.array(target_values)
    
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
        'scaler': scaler
    }

def score_candidates(model_bundle: Dict[str, Any], candidate_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if model_bundle is None:
        raise ValueError("model_bundle cannot be None")
    
    if not isinstance(model_bundle, dict):
        raise ValueError("model_bundle must be a dictionary")
    
    if 'model' not in model_bundle or 'scaler' not in model_bundle:
        raise ValueError("model_bundle is not a valid fitted bundle")
    
    if not hasattr(model_bundle['model'], 'coef_') or not hasattr(model_bundle['scaler'], 'scale_'):
        raise ValueError("model_bundle is not a valid fitted bundle")
    
    if not isinstance(candidate_records, list):
        raise ValueError("candidate_records must be a list")
    
    if len(candidate_records) == 0:
        return []
    
    for record in candidate_records:
        if not isinstance(record, dict):
            raise ValueError("Each record must be a dictionary")
        validate_candidate_record(record, training=False)
    
    results = []
    for record in candidate_records:
        is_eligible = record['has_valid_registration'] and record['meets_required_shift_availability']
        
        if is_eligible:
            features = extract_features(record)
            features_scaled = model_bundle['scaler'].transform([features])
            probabilities = model_bundle['model'].predict_proba(features_scaled)[0]
            hiring_probability = float(probabilities[1])
            selected = hiring_probability >= 0.5
        else:
            hiring_probability = 0.0
            selected = False
        
        result = {
            'candidate_id': record['candidate_id'],
            'eligible': is_eligible,
            'hiring_probability': hiring_probability,
            'selected': selected
        }
        results.append(result)
    
    return results
