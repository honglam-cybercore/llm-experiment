import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.utils.validation import check_is_fitted


_FEATURE_FIELDS = (
    "gender",
    "relevant_experience_years",
    "clinical_assessment_score",
    "communication_assessment_score",
    "patient_care_assessment_score",
    "recruitment_channel",
)

_NUMERIC_FIELDS = (
    "relevant_experience_years",
    "clinical_assessment_score",
    "communication_assessment_score",
    "patient_care_assessment_score",
)

_CATEGORICAL_FIELDS = (
    "gender",
    "recruitment_channel",
)

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


@dataclass(frozen=True)
class _ModelBundle:
    pipeline: Pipeline
    fitted: bool = True


def _is_python_number(value):
    return type(value) in (int, float)


def _validate_candidate(record, training=False):
    if type(record) is not dict:
        raise ValueError("Invalid record")

    expected = _TRAINING_FIELDS if training else _CANDIDATE_FIELDS
    try:
        if set(record.keys()) != expected:
            raise ValueError("Invalid record")
    except (TypeError, ValueError):
        raise ValueError("Invalid record") from None

    candidate_id = record.get("candidate_id")
    if type(candidate_id) is not str or not candidate_id.strip():
        raise ValueError("Invalid record")

    if record.get("gender") not in ("Male", "Female"):
        raise ValueError("Invalid record")

    if type(record.get("has_valid_registration")) is not bool:
        raise ValueError("Invalid record")

    if type(record.get("meets_required_shift_availability")) is not bool:
        raise ValueError("Invalid record")

    if record.get("recruitment_channel") not in ("Channel_A", "Channel_B"):
        raise ValueError("Invalid record")

    numeric_ranges = {
        "relevant_experience_years": (0.0, 40.0),
        "clinical_assessment_score": (0.0, 100.0),
        "communication_assessment_score": (0.0, 100.0),
        "patient_care_assessment_score": (0.0, 100.0),
    }

    for field, (lower, upper) in numeric_ranges.items():
        value = record.get(field)
        if not _is_python_number(value) or not math.isfinite(value):
            raise ValueError("Invalid record")
        if value < lower or value > upper:
            raise ValueError("Invalid record")

    if training and type(record.get("historical_hired")) is not int:
        raise ValueError("Invalid record")
    if training and record.get("historical_hired") not in (0, 1):
        raise ValueError("Invalid record")


def _validate_random_state(random_state):
    if type(random_state) is not int or not 0 <= random_state <= 2**32 - 1:
        raise ValueError("Invalid random_state")


def _feature_frame(records):
    return pd.DataFrame(
        [
            {field: record[field] for field in _FEATURE_FIELDS}
            for record in records
        ],
        columns=list(_FEATURE_FIELDS),
    )


def train_model(training_records, random_state=42):
    _validate_random_state(random_state)

    if type(training_records) is not list or len(training_records) < 2:
        raise ValueError("Invalid training records")

    for record in training_records:
        _validate_candidate(record, training=True)

    eligible_records = [
        record
        for record in training_records
        if record["has_valid_registration"]
        and record["meets_required_shift_availability"]
    ]

    targets = [record["historical_hired"] for record in eligible_records]
    if len(set(targets)) != 2:
        raise ValueError("Eligible training data must contain both target classes")

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                StandardScaler(),
                list(_NUMERIC_FIELDS),
            ),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                list(_CATEGORICAL_FIELDS),
            ),
        ]
    )

    estimator = LogisticRegression(
        solver="liblinear",
        C=1.0,
        max_iter=1000,
        random_state=random_state,
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", estimator),
        ]
    )

    try:
        pipeline.fit(_feature_frame(eligible_records), np.asarray(targets, dtype=int))
        check_is_fitted(pipeline)
    except Exception:
        raise ValueError("Unable to fit model") from None

    return _ModelBundle(pipeline=pipeline)


def score_candidates(model_bundle, candidate_records):
    if type(candidate_records) is not list:
        raise ValueError("Invalid candidate records")

    validated_records = []
    for record in candidate_records:
        _validate_candidate(record, training=False)
        validated_records.append(record)

    if not isinstance(model_bundle, _ModelBundle) or model_bundle.fitted is not True:
        raise ValueError("Invalid model bundle")

    try:
        check_is_fitted(model_bundle.pipeline)
    except Exception:
        raise ValueError("Invalid model bundle") from None

    eligible_records = [
        record
        for record in validated_records
        if record["has_valid_registration"]
        and record["meets_required_shift_availability"]
    ]

    probabilities = {}
    if eligible_records:
        try:
            raw_probabilities = model_bundle.pipeline.predict_proba(
                _feature_frame(eligible_records)
            )
            classes = model_bundle.pipeline.named_steps["classifier"].classes_
            class_one_positions = np.flatnonzero(classes == 1)
            if len(class_one_positions) != 1:
                raise ValueError
            class_one_index = int(class_one_positions[0])
            values = raw_probabilities[:, class_one_index]
        except Exception:
            raise ValueError("Unable to score candidates") from None

        for record, value in zip(eligible_records, values):
            probability = float(value)
            if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
                raise ValueError("Unable to score candidates")
            probabilities[id(record)] = probability

    results = []
    for record in validated_records:
        eligible = (
            record["has_valid_registration"]
            and record["meets_required_shift_availability"]
        )
        if eligible:
            probability = probabilities[id(record)]
            selected = probability >= 0.5
        else:
            probability = 0.0
            selected = False

        results.append(
            {
                "candidate_id": record["candidate_id"],
                "eligible": bool(eligible),
                "hiring_probability": float(probability),
                "selected": bool(selected),
            }
        )

    return results