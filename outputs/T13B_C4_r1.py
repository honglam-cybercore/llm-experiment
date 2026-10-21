import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

CANDIDATE_FIELDS = {
    'candidate_id', 'gender', 'has_valid_registration', 
    'relevant_experience_years', 'clinical_assessment_score',
    'communication_assessment_score', 'patient_care_assessment_score',
    'meets_required_shift_availability', 'recruitment_channel'
}

TRAINING_FIELDS = CANDIDATE_FIELDS | {'historical_hired'}

def validate_candidate(candidate, is_training=False):
    expected_fields = TRAINING_FIELDS if is_training else CANDIDATE_FIELDS
    
    if set(candidate.keys()) != expected_fields:
        raise ValueError("Invalid candidate fields")
    
    candidate_id = candidate['candidate_id']
    if not isinstance(candidate_id, str):
        raise ValueError("candidate_id must be a string")
    if not any(not c.isspace() for c in candidate_id):
        raise ValueError("candidate_id must contain a non-whitespace character")
    
    if candidate['gender'] not in ('Male', 'Female'):
        raise ValueError("gender must be 'Male' or 'Female'")
    
    if not isinstance(candidate['has_valid_registration'], bool):
        raise ValueError("has_valid_registration must be a boolean")
    if not isinstance(candidate['meets_required_shift_availability'], bool):
        raise ValueError("meets_required_shift_availability must be a boolean")
    
    exp_years = candidate['relevant_experience_years']
    if isinstance(exp_years, bool) or not isinstance(exp_years, (int, float, np.integer, np.floating)):
        raise ValueError("relevant_experience_years must be numeric")
    if not np.isfinite(exp_years):
        raise ValueError("relevant_experience_years must be finite")
    if not (0 <= exp_years <= 40):
        raise ValueError("relevant_experience_years out of range")
    
    for score_field in ['clinical_assessment_score', 'communication_assessment_score', 'patient_care_assessment_score']:
        score = candidate[score_field]
        if isinstance(score, bool) or not isinstance(score, (int, float, np.integer, np.floating)):
            raise ValueError(f"{score_field} must be numeric")
        if not np.isfinite(score):
            raise ValueError(f"{score_field} must be finite")
        if not (0 <= score <= 100):
            raise ValueError(f"{score_field} out of range")
    
    if candidate['recruitment_channel'] not in ('Channel_A', 'Channel_B'):
        raise ValueError("recruitment_channel must be 'Channel_A' or 'Channel_B'")
    
    if is_training:
        historical_hired = candidate['historical_hired']
        if not isinstance(historical_hired, (int, np.integer)) or isinstance(historical_hired, bool):
            raise ValueError("historical_hired must be an integer 0 or 1")
        if historical_hired not in (0, 1):
            raise ValueError("historical_hired must be 0 or 1")

def is_eligible(candidate):
    return candidate['has_valid_registration'] and candidate['meets_required_shift_availability']

def extract_features(candidate):
    return [
        1.0 if candidate['gender'] == 'Male' else 0.0,
        float(candidate['relevant_experience_years']),
        float(candidate['clinical_assessment_score']),
        float(candidate['communication_assessment_score']),
        float(candidate['patient_care_assessment_score']),
        1.0 if candidate['recruitment_channel'] == 'Channel_A' else 0.0
    ]

def train_model(training_records, random_state=42):
    if not isinstance(random_state, (int, np.integer)) or isinstance(random_state, bool):
        raise ValueError("random_state must be a non-Boolean integer")
    if not (0 <= random_state < 2**32):
        raise ValueError("random_state out of valid range")
    
    if not isinstance(training_records, list):
        raise ValueError("training_records must be a list")
    if len(training_records) < 2:
        raise ValueError("training_records must have at least 2 records")
    
    for record in training_records:
        if not isinstance(record, dict):
            raise ValueError("Each record must be a dictionary")
        validate_candidate(record, is_training=True)
    
    eligible_records = [r for r in training_records if is_eligible(r)]
    
    if not eligible_records:
        raise ValueError("No eligible training records")
    
    targets = [r['historical_hired'] for r in eligible_records]
    if len(set(targets)) < 2:
        raise ValueError("Both target classes must be present in eligible training records")
    
    X = np.array([extract_features(r) for r in eligible_records], dtype=np.float64)
    y = np.array(targets, dtype=np.int64)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    clf = LogisticRegression(
        solver='liblinear',
        C=1.0,
        max_iter=1000,
        random_state=int(random_state)
    )
    clf.fit(X_scaled, y)
    
    return {
        'scaler': scaler,
        'classifier': clf
    }

def score_candidates(model_bundle, candidate_records):
    if model_bundle is None:
        raise ValueError("model_bundle cannot be None")
    if not isinstance(model_bundle, dict):
        raise ValueError("model_bundle must be a dictionary")
    if 'scaler' not in model_bundle or 'classifier' not in model_bundle:
        raise ValueError("Invalid model bundle")
    
    scaler = model_bundle['scaler']
    classifier = model_bundle['classifier']
    
    if not hasattr(classifier, 'coef_') or not hasattr(classifier, 'intercept_'):
        raise ValueError("Unfitted model bundle")
    if not hasattr(scaler, 'mean_') or not hasattr(scaler, 'scale_'):
        raise ValueError("Unfitted model bundle")
    
    if not isinstance(candidate_records, list):
        raise ValueError("candidate_records must be a list")
    
    if len(candidate_records) == 0:
        return []
    
    for record in candidate_records:
        if not isinstance(record, dict):
            raise ValueError("Each record must be a dictionary")
        validate_candidate(record, is_training=False)
    
    results = []
    for record in candidate_records:
        eligible = is_eligible(record)
        
        result = {
            'candidate_id': record['candidate_id'],
            'eligible': eligible,
            'hiring_probability': 0.0,
            'selected': False
        }
        
        if eligible:
            features = extract_features(record)
            X = np.array([features], dtype=np.float64)
            X_scaled = scaler.transform(X)
            proba = classifier.predict_proba(X_scaled)[0]
            prob_class_1 = float(proba[1])
            
            result['hiring_probability'] = prob_class_1
            result['selected'] = bool(prob_class_1 >= 0.5)
        
        results.append(result)
    
    return results
