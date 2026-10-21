import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder


def validate_candidate_record(record, is_training=False):
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
        raise ValueError("Record has unknown or missing fields")
    
    if not isinstance(record['candidate_id'], str) or not record['candidate_id'].strip():
        raise ValueError("candidate_id must be a non-empty string with non-whitespace characters")
    
    if record['gender'] not in ('Male', 'Female'):
        raise ValueError("gender must be 'Male' or 'Female'")
    
    if not isinstance(record['has_valid_registration'], bool):
        raise ValueError("has_valid_registration must be a boolean")
    if not isinstance(record['meets_required_shift_availability'], bool):
        raise ValueError("meets_required_shift_availability must be a boolean")
    
    numeric_fields = [
        'relevant_experience_years', 'clinical_assessment_score',
        'communication_assessment_score', 'patient_care_assessment_score'
    ]
    
    for field in numeric_fields:
        value = record[field]
        if isinstance(value, bool):
            raise ValueError(f"{field} cannot be a boolean")
        if not isinstance(value, (int, float)):
            raise ValueError(f"{field} must be numeric")
        if not np.isfinite(value):
            raise ValueError(f"{field} must be finite")
    
    if not (0 <= record['relevant_experience_years'] <= 40):
        raise ValueError("relevant_experience_years must be between 0 and 40")
    if not (0 <= record['clinical_assessment_score'] <= 100):
        raise ValueError("clinical_assessment_score must be between 0 and 100")
    if not (0 <= record['communication_assessment_score'] <= 100):
        raise ValueError("communication_assessment_score must be between 0 and 100")
    if not (0 <= record['patient_care_assessment_score'] <= 100):
        raise ValueError("patient_care_assessment_score must be between 0 and 100")
    
    if record['recruitment_channel'] not in ('Channel_A', 'Channel_B'):
        raise ValueError("recruitment_channel must be 'Channel_A' or 'Channel_B'")
    
    if is_training:
        if not isinstance(record['historical_hired'], int) or isinstance(record['historical_hired'], bool):
            raise ValueError("historical_hired must be an integer (0 or 1)")
        if record['historical_hired'] not in (0, 1):
            raise ValueError("historical_hired must be 0 or 1")


def train_model(training_records, random_state=42):
    if not isinstance(random_state, int) or isinstance(random_state, bool):
        raise ValueError("random_state must be a non-Boolean integer")
    if not (0 <= random_state < 2**32):
        raise ValueError("random_state must be between 0 and 2**32-1")
    
    if not isinstance(training_records, list):
        raise ValueError("training_records must be a list")
    if len(training_records) < 2:
        raise ValueError("training_records must have at least 2 records")
    
    for record in training_records:
        validate_candidate_record(record, is_training=True)
    
    eligible_records = []
    for record in training_records:
        if record['has_valid_registration'] and record['meets_required_shift_availability']:
            eligible_records.append(record)
    
    if not eligible_records:
        raise ValueError("No eligible records in training data")
    
    targets = [r['historical_hired'] for r in eligible_records]
    if 0 not in targets or 1 not in targets:
        raise ValueError("Training data must contain both target classes (0 and 1)")
    
    df = pd.DataFrame(eligible_records)
    
    gender_encoder = LabelEncoder()
    gender_encoder.fit(['Male', 'Female'])
    df['gender_encoded'] = gender_encoder.transform(df['gender'])
    
    channel_encoder = LabelEncoder()
    channel_encoder.fit(['Channel_A', 'Channel_B'])
    df['channel_encoded'] = channel_encoder.transform(df['recruitment_channel'])
    
    feature_columns = [
        'relevant_experience_years',
        'clinical_assessment_score',
        'communication_assessment_score',
        'patient_care_assessment_score',
        'gender_encoded',
        'channel_encoded'
    ]
    
    X = df[feature_columns].values
    y = df['historical_hired'].values
    
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
        'gender_encoder': gender_encoder,
        'channel_encoder': channel_encoder,
        'feature_columns': feature_columns
    }


def score_candidates(model_bundle, candidate_records):
    if model_bundle is None:
        raise ValueError("model_bundle cannot be None")
    if not isinstance(model_bundle, dict):
        raise ValueError("model_bundle must be a dictionary")
    
    required_bundle_keys = {'model', 'scaler', 'gender_encoder', 'channel_encoder', 'feature_columns'}
    if set(model_bundle.keys()) != required_bundle_keys:
        raise ValueError("model_bundle is not a valid fitted bundle")
    
    if not hasattr(model_bundle['model'], 'coef_'):
        raise ValueError("model_bundle contains an unfitted model")
    
    if not isinstance(candidate_records, list):
        raise ValueError("candidate_records must be a list")
    
    if len(candidate_records) == 0:
        return []
    
    for record in candidate_records:
        validate_candidate_record(record, is_training=False)
    
    results = []
    
    for record in candidate_records:
        candidate_id = record['candidate_id']
        eligible = record['has_valid_registration'] and record['meets_required_shift_availability']
        
        if eligible:
            gender_code = model_bundle['gender_encoder'].transform([record['gender']])[0]
            channel_code = model_bundle['channel_encoder'].transform([record['recruitment_channel']])[0]
            
            X = np.array([[
                record['relevant_experience_years'],
                record['clinical_assessment_score'],
                record['communication_assessment_score'],
                record['patient_care_assessment_score'],
                gender_code,
                channel_code
            ]])
            
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
