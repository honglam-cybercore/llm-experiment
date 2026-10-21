import math
from numbers import Real

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.utils.validation import check_is_fitted


_CANDIDATE_FIELDS = {
    "candidate_id",
    "gender",
    "has_valid_registration",
    "relevant_experience_years",
    "clinical_assessment_score",
    "communication_assessment_score",
    "patient_care_assessment_score",
    "meets_required_shift_availability",
    "recruitment_channel",
}

_TRAINING_FIELDS = _CANDIDATE_FIELDS | {"historical_hired"}

_FEATURE_FIELDS = [
    "gender",
    "has_valid_registration",
    "relevant_experience_years",
    "clinical_assessment_score",
    "communication_assessment_score",
    "patient_care_assessment_score",
    "meets_required_shift_availability",
    "recruitment_channel",
]

_CATEGORICAL_FIELDS = ["gender", "recruitment_channel"]
_NUMERIC_FIELDS = [
    "has_valid_registration",
    "relevant_experience_years",
    "clinical_assessment_score",
    "communication_assessment_score",
    "patient_care_assessment_score",
    "meets_required_shift_availability",
]


def _is_python_number(value):
    return type(value) in (int, float) and math.isfinite(float(value))


def _validate_common_record(record, fields):
    if not isinstance(record, dict) or set(record.keys()) != fields:
        raise ValueError("Invalid record")

    candidate_id = record["candidate_id"]
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise ValueError("Invalid record")

    if record["gender"] not in ("Male", "Female"):
        raise ValueError("Invalid record")

    if type(record["has_valid_registration"]) is not bool:
        raise ValueError("Invalid record")

    experience = record["relevant_experience_years"]
    if not _is_python_number(experience) or not 0 <= float(experience) <= 40:
        raise ValueError("Invalid record")

    for field in (
        "clinical_assessment_score",
        "communication_assessment_score",
        "patient_care_assessment_score",
    ):
        value = record[field]
        if not _is_python_number(value) or not 0 <= float(value) <= 100:
            raise ValueError("Invalid record")

    if type(record["meets_required_shift_availability"]) is not bool:
        raise ValueError("Invalid record")

    if record["recruitment_channel"] not in ("Channel_A", "Channel_B"):
        raise ValueError("Invalid record")


def _validate_training_record(record):
    _validate_common_record(record, _TRAINING_FIELDS)
    if type(record["historical_hired"]) is not int or record["historical_hired"] not in (0, 1):
        raise ValueError("Invalid record")


def _validate_candidate_record(record):
    _validate_common_record(record, _CANDIDATE_FIELDS)


def _prepare_features(records):
    rows = []
    for record in records:
        row = dict(record)
        row["has_valid_registration"] = int(row["has_valid_registration"])
        row["meets_required_shift_availability"] = int(
            row["meets_required_shift_availability"]
        )
        rows.append({field: row[field] for field in _FEATURE_FIELDS})
    return pd.DataFrame(rows, columns=_FEATURE_FIELDS)


def train_model(training_records, random_state=42):
    if type(random_state) is not int or not 0 <= random_state <= 2**32 - 1:
        raise ValueError("Invalid random_state")

    if not isinstance(training_records, list) or len(training_records) < 2:
        raise ValueError("Invalid training data")

    for record in training_records:
        _validate_training_record(record)

    eligible_records = [
        record
        for record in training_records
        if record["has_valid_registration"]
        and record["meets_required_shift_availability"]
    ]

    if len(eligible_records) < 2:
        raise ValueError("Insufficient eligible training data")

    targets = [record["historical_hired"] for record in eligible_records]
    if set(targets) != {0, 1}:
        raise ValueError("Training data must contain both target classes")

    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), _CATEGORICAL_FIELDS),
            ("numeric", StandardScaler(), _NUMERIC_FIELDS),
        ]
    )

    estimator = LogisticRegression(
        solver="liblinear",
        C=1.0,
        max_iter=1000,
        random_state=random_state,
    )

    pipeline = Pipeline(
        [
            ("preprocessor", preprocessor),
            ("classifier", estimator),
        ]
    )

    features = _prepare_features(eligible_records)
    pipeline.fit(features, np.asarray(targets, dtype=int))

    return {
        "pipeline": pipeline,
        "feature_fields": tuple(_FEATURE_FIELDS),
    }


def score_candidates(model_bundle, candidate_records):
    if not isinstance(model_bundle, dict):
        raise ValueError("Invalid model bundle")

    if set(model_bundle.keys()) != {"pipeline", "feature_fields"}:
        raise ValueError("Invalid model bundle")

    if model_bundle["feature_fields"] != tuple(_FEATURE_FIELDS):
        raise ValueError("Invalid model bundle")

    pipeline = model_bundle["pipeline"]
    try:
        check_is_fitted(pipeline)
    except Exception:
        raise ValueError("Invalid model bundle") from None

    if not isinstance(candidate_records, list):
        raise ValueError("Invalid candidate data")

    for record in candidate_records:
        _validate_candidate_record(record)

    eligible_records = [
        record
        for record in candidate_records
        if record["has_valid_registration"]
        and record["meets_required_shift_availability"]
    ]

    probabilities = []
    if eligible_records:
        try:
            features = _prepare_features(eligible_records)
            raw_probabilities = pipeline.predict_proba(features)
            classes = list(pipeline.named_steps["classifier"].classes_)
            class_one_index = classes.index(1)
            probabilities = [
                float(probability[class_one_index])
                for probability in raw_probabilities
            ]
        except Exception:
            raise ValueError("Unable to score candidates") from None

        if any(
            not math.isfinite(probability) or not 0 <= probability <= 1
            for probability in probabilities
        ):
            raise ValueError("Unable to score candidates")

    results = []
    eligible_index = 0

    for record in candidate_records:
        if record["has_valid_registration"] and record["meets_required_shift_availability"]:
            probability = probabilities[eligible_index]
            eligible_index += 1
            results.append(
                {
                    "candidate_id": record["candidate_id"],
                    "eligible": True,
                    "hiring_probability": probability,
                    "selected": probability >= 0.5,
                }
            )
        else:
            results.append(
                {
                    "candidate_id": record["candidate_id"],
                    "eligible": False,
                    "hiring_probability": 0.0,
                    "selected": False,
                }
            )

    return results