import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

def _validate_candidate_id(candidate_id):
    if not isinstance(candidate_id, str):
        raise ValueError("candidate_id must be a string")
    if not candidate_id or all(c.isspace() for c in candidate_id):
        raise ValueError("candidate_id must contain non-whitespace character")

def _validate_gender(gender):
    if gender not in ("Male", "Female"):
        raise ValueError(f"gender must be exactly 'Male' or 'Female', got {repr(gender)}")

def _validate_boolean_field(value, field_name):
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a Boolean")

def _validate_numeric_field(value, field_name, min_val, max_val):
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must not be a Boolean")
    if not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be int or float")
    if not np.isfinite(value):
        raise ValueError(f"{field_name} must be finite")
    if not (min_val <= value <= max_val):
        raise ValueError(f"{field_name} must be between {min_val} and {max_val}")

def _validate_channel(channel):
    if channel not in ("Channel_A", "Channel_B"):
        raise ValueError(f"recruitment_channel must be exactly 'Channel_A' or 'Channel_B'")

def _validate_candidate_record(record, require_target=False):
    expected_fields = {
        "candidate_id", "gender", "has_valid_registration",
        "relevant_experience_years", "clinical_assessment_score",
        "communication_assessment_score", "patient_care_assessment_score",
        "meets_required_shift_availability", "recruitment_channel"
    }
    
    if require_target:
        expected_fields.add("historical_hired")
    
    if not isinstance(record, dict):
        raise ValueError("Each record must be a dictionary")
    
    record_fields = set(record.keys())
    unknown = record_fields - expected_fields
    if unknown:
        raise ValueError(f"Unknown fields: {unknown}")
    
    missing = expected_fields - record_fields
    if missing:
        raise ValueError(f"Missing fields: {missing}")
    
    _validate_candidate_id(record["candidate_id"])
    _validate_gender(record["gender"])
    _validate_boolean_field(record["has_valid_registration"], "has_valid_registration")
    _validate_numeric_field(record["relevant_experience_years"], "relevant_experience_years", 0, 40)
    _validate_numeric_field(record["clinical_assessment_score"], "clinical_assessment_score", 0, 100)
    _validate_numeric_field(record["communication_assessment_score"], "communication_assessment_score", 0, 100)
    _validate_numeric_field(record["patient_care_assessment_score"], "patient_care_assessment_score", 0, 100)
    _validate_boolean_field(record["meets_required_shift_availability"], "meets_required_shift_availability")
    _validate_channel(record["recruitment_channel"])
    
    if require_target:
        target = record["historical_hired"]
        if not isinstance(target, int) or isinstance(target, bool):
            raise ValueError("historical_hired must be an integer (not Boolean)")
        if target not in (0, 1):
            raise ValueError("historical_hired must be 0 or 1")
    
    return record

def train_model(training_records, random_state=42):
    if not isinstance(random_state, int) or isinstance(random_state, bool):
        raise ValueError("random_state must be an integer (not Boolean)")
    if not (0 <= random_state < 2**32):
        raise ValueError(f"random_state must be between 0 and {2**32-1}")
    
    if not isinstance(training_records, list):
        raise ValueError("training_records must be a list")
    
    if len(training_records) < 2:
        raise ValueError("training_records must have at least 2 records")
    
    validated_records = []
    for record in training_records:
        validated_records.append(_validate_candidate_record(record, require_target=True))
    
    eligible_records = [
        r for r in validated_records
        if r["has_valid_registration"] and r["meets_required_shift_availability"]
    ]
    
    if not eligible_records:
        raise ValueError("No eligible training records")
    
    targets = [r["historical_hired"] for r in eligible_records]
    if 0 not in targets or 1 not in targets:
        raise ValueError("Both classes (0 and 1) must be present in eligible records")
    
    features_list = []
    for r in eligible_records:
        features = [
            1.0 if r["gender"] == "Female" else 0.0,
            float(r["relevant_experience_years"]),
            float(r["clinical_assessment_score"]),
            float(r["communication_assessment_score"]),
            float(r["patient_care_assessment_score"]),
            1.0 if r["recruitment_channel"] == "Channel_B" else 0.0,
        ]
        features_list.append(features)
    
    X = np.array(features_list, dtype=np.float64)
    y = np.array(targets, dtype=np.int64)
    
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
        "scaler": scaler,
        "model": model
    }

def score_candidates(model_bundle, candidate_records):
    if model_bundle is None:
        raise ValueError("model_bundle cannot be None")
    
    if not isinstance(model_bundle, dict):
        raise ValueError("model_bundle must be a dictionary")
    
    if "scaler" not in model_bundle or "model" not in model_bundle:
        raise ValueError("model_bundle is not a valid fitted bundle")
    
    scaler = model_bundle["scaler"]
    model = model_bundle["model"]
    
    if not isinstance(candidate_records, list):
        raise ValueError("candidate_records must be a list")
    
    validated_candidates = []
    for record in candidate_records:
        validated_candidates.append(_validate_candidate_record(record, require_target=False))
    
    results = []
    for candidate in validated_candidates:
        candidate_id = candidate["candidate_id"]
        
        eligible = (
            candidate["has_valid_registration"] and
            candidate["meets_required_shift_availability"]
        )
        
        if eligible:
            features = [
                1.0 if candidate["gender"] == "Female" else 0.0,
                float(candidate["relevant_experience_years"]),
                float(candidate["clinical_assessment_score"]),
                float(candidate["communication_assessment_score"]),
                float(candidate["patient_care_assessment_score"]),
                1.0 if candidate["recruitment_channel"] == "Channel_B" else 0.0,
            ]
            X = np.array([features], dtype=np.float64)
            X_scaled = scaler.transform(X)
            
            proba = model.predict_proba(X_scaled)[0]
            hiring_probability = float(proba[1])
            selected = hiring_probability >= 0.5
        else:
            hiring_probability = 0.0
            selected = False
        
        results.append({
            "candidate_id": candidate_id,
            "eligible": eligible,
            "hiring_probability": hiring_probability,
            "selected": selected
        })
    
    return results
