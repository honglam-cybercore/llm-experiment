import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


def train_model(training_records, random_state=42):
    if not isinstance(random_state, int) or isinstance(random_state, bool):
        raise ValueError("random_state must be a non-Boolean Python integer")
    if not (0 <= random_state <= 2**32 - 1):
        raise ValueError("random_state must be between 0 and 2**32-1")
    
    if not isinstance(training_records, list):
        raise ValueError("training_records must be a list")
    if len(training_records) < 2:
        raise ValueError("training_records must have at least 2 records")
    
    for record in training_records:
        _validate_record(record, is_training=True)
    
    eligible_records = []
    for record in training_records:
        if record.get('has_valid_registration') and record.get('meets_required_shift_availability'):
            eligible_records.append(record)
    
    targets = [r['historical_hired'] for r in eligible_records]
    if len(set(targets)) != 2:
        raise ValueError("Both target classes must be present among eligible records")
    
    X_list = []
    y_list = []
    
    for record in eligible_records:
        x_row = [
            record['relevant_experience_years'],
            record['clinical_assessment_score'],
            record['communication_assessment_score'],
            record['patient_care_assessment_score'],
            1 if record['gender'] == 'Male' else 0,
            1 if record['recruitment_channel'] == 'Channel_A' else 0
        ]
        X_list.append(x_row)
        y_list.append(record['historical_hired'])
    
    X = np.array(X_list, dtype=float)
    y = np.array(y_list, dtype=int)
    
    scaler = StandardScaler()
    X[:, :4] = scaler.fit_transform(X[:, :4])
    
    model = LogisticRegression(solver='liblinear', C=1.0, max_iter=1000, random_state=random_state)
    model.fit(X, y)
    
    return {
        'model': model,
        'scaler': scaler,
        'random_state': random_state
    }


def score_candidates(model_bundle, candidate_records):
    if model_bundle is None:
        raise ValueError("model_bundle cannot be None")
    
    if not isinstance(model_bundle, dict) or 'model' not in model_bundle:
        raise ValueError("model_bundle must be a valid fitted bundle")
    
    if not isinstance(candidate_records, list):
        raise ValueError("candidate_records must be a list")
    
    for record in candidate_records:
        _validate_record(record, is_training=False)
    
    if len(candidate_records) == 0:
        return []
    
    results = []
    for record in candidate_records:
        eligible = record.get('has_valid_registration') and record.get('meets_required_shift_availability')
        
        if eligible:
            x_row = np.array([[
                record['relevant_experience_years'],
                record['clinical_assessment_score'],
                record['communication_assessment_score'],
                record['patient_care_assessment_score'],
                1 if record['gender'] == 'Male' else 0,
                1 if record['recruitment_channel'] == 'Channel_A' else 0
            ]], dtype=float)
            
            x_row[:, :4] = model_bundle['scaler'].transform(x_row[:, :4])
            
            prob = float(model_bundle['model'].predict_proba(x_row)[0][1])
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
        raise ValueError("Record must be a dictionary")
    
    expected_fields = {
        'candidate_id', 'gender', 'has_valid_registration',
        'relevant_experience_years', 'clinical_assessment_score',
        'communication_assessment_score', 'patient_care_assessment_score',
        'meets_required_shift_availability', 'recruitment_channel'
    }
    
    if is_training:
        expected_fields.add('historical_hired')
    
    if set(record.keys()) != expected_fields:
        raise ValueError("Record has unknown or missing fields")
    
    if not isinstance(record['candidate_id'], str):
        raise ValueError("candidate_id must be a string")
    if not record['candidate_id'] or record['candidate_id'].isspace():
        raise ValueError("candidate_id must contain non-whitespace characters")
    
    if record['gender'] not in ('Male', 'Female'):
        raise ValueError("gender must be 'Male' or 'Female'")
    
    if not isinstance(record['has_valid_registration'], bool):
        raise ValueError("has_valid_registration must be a Boolean")
    
    val = record['relevant_experience_years']
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise ValueError("relevant_experience_years must be numeric")
    if not np.isfinite(val) or not (0 <= val <= 40):
        raise ValueError("relevant_experience_years must be finite and in [0, 40]")
    
    val = record['clinical_assessment_score']
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise ValueError("clinical_assessment_score must be numeric")
    if not np.isfinite(val) or not (0 <= val <= 100):
        raise ValueError("clinical_assessment_score must be finite and in [0, 100]")
    
    val = record['communication_assessment_score']
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise ValueError("communication_assessment_score must be numeric")
    if not np.isfinite(val) or not (0 <= val <= 100):
        raise ValueError("communication_assessment_score must be finite and in [0, 100]")
    
    val = record['patient_care_assessment_score']
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise ValueError("patient_care_assessment_score must be numeric")
    if not np.isfinite(val) or not (0 <= val <= 100):
        raise ValueError("patient_care_assessment_score must be finite and in [0, 100]")
    
    if not isinstance(record['meets_required_shift_availability'], bool):
        raise ValueError("meets_required_shift_availability must be a Boolean")
    
    if record['recruitment_channel'] not in ('Channel_A', 'Channel_B'):
        raise ValueError("recruitment_channel must be 'Channel_A' or 'Channel_B'")
    
    if is_training:
        val = record['historical_hired']
        if not isinstance(val, int) or isinstance(val, bool):
            raise ValueError("historical_hired must be an integer")
        if val not in (0, 1):
            raise ValueError("historical_hired must be 0 or 1")
