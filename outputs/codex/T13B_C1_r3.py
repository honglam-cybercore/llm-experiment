import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.exceptions import NotFittedError
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
_NUMERIC_RANGES = {
    "relevant_experience_years": (0.0, 40.0),
    "clinical_assessment_score": (0.0, 100.0),
    "communication_assessment_score": (0.0, 100.0),
    "patient_care_assessment_score": (0.0, 100.0),
}
_FEATURE_COLUMNS = [
    "gender",
    "relevant_experience_years",
    "clinical_assessment_score",
    "communication_assessment_score",
    "patient_care_assessment_score",
    "recruitment_channel",
]
_CATEGORICAL_COLUMNS = ["gender", "recruitment_channel"]
_NUMERIC_COLUMNS = [
    "relevant_experience_years",
    "clinical_assessment_score",
    "communication_assessment_score",
    "patient_care_assessment_score",
]


@dataclass
class _ModelBundle:
    pipeline: Pipeline
    fitted: bool = True


def _require_exact_fields(record: Any, fields: set[str]) -> None:
    if not isinstance(record, dict) or set(record.keys()) != fields:
        raise ValueError("Invalid record fields")


def _validate_candidate(record: Any, training: bool = False) -> None:
    _require_exact_fields(record, _TRAINING_FIELDS if training else _CANDIDATE_FIELDS)

    candidate_id = record["candidate_id"]
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise ValueError("Invalid candidate identifier")

    if record["gender"] not in ("Male", "Female") or not isinstance(
        record["gender"], str
    ):
        raise ValueError("Invalid gender")

    for field in ("has_valid_registration", "meets_required_shift_availability"):
        if type(record[field]) is not bool:
            raise ValueError("Invalid Boolean field")

    for field, (lower, upper) in _NUMERIC_RANGES.items():
        value = record[field]
        if type(value) not in (int, float):
            raise ValueError("Invalid numeric field")
        if not math.isfinite(value) or not lower <= value <= upper:
            raise ValueError("Invalid numeric field")

    if record["recruitment_channel"] not in ("Channel_A", "Channel_B") or not isinstance(
        record["recruitment_channel"], str
    ):
        raise ValueError("Invalid recruitment channel")

    if training:
        target = record["historical_hired"]
        if type(target) is not int or target not in (0, 1):
            raise ValueError("Invalid target")


def _records_frame(records: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame([{field: record[field] for field in _FEATURE_COLUMNS} for record in records])


def train_model(training_records, random_state=42):
    if not isinstance(training_records, list) or not training_records:
        raise ValueError("Training records must be a non-empty list")
    if type(random_state) is not int or not 0 <= random_state <= 2**32 - 1:
        raise ValueError("Invalid random state")
    if len(training_records) < 2:
        raise ValueError("At least two training records are required")

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
        raise ValueError("Eligible training records must contain both target classes")

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), _NUMERIC_COLUMNS),
            (
                "categorical",
                OneHotEncoder(handle_unknown="error", sparse=True),
                _CATEGORICAL_COLUMNS,
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

    frame = _records_frame(eligible_records)
    pipeline.fit(frame, np.asarray(targets, dtype=np.int64))
    return _ModelBundle(pipeline=pipeline)


def score_candidates(model_bundle, candidate_records):
    if not isinstance(model_bundle, _ModelBundle) or not model_bundle.fitted:
        raise ValueError("Invalid model bundle")
    if not isinstance(candidate_records, list):
        raise ValueError("Candidate records must be a list")

    try:
        check_is_fitted(model_bundle.pipeline)
    except (TypeError, AttributeError, NotFittedError, ValueError):
        raise ValueError("Invalid model bundle") from None

    for record in candidate_records:
        _validate_candidate(record)

    if not candidate_records:
        return []

    eligible_records = [
        record
        for record in candidate_records
        if record["has_valid_registration"]
        and record["meets_required_shift_availability"]
    ]

    probabilities = {}
    if eligible_records:
        frame = _records_frame(eligible_records)
        try:
            values = model_bundle.pipeline.predict_proba(frame)[:, 1]
        except Exception:
            raise ValueError("Unable to score candidates") from None

        for record, probability in zip(eligible_records, values):
            probability = float(probability)
            if not math.isfinite(probability):
                raise ValueError("Invalid model probability")
            probability = min(1.0, max(0.0, probability))
            probabilities[id(record)] = probability

    results = []
    for record in candidate_records:
        if record["has_valid_registration"] and record["meets_required_shift_availability"]:
            probability = probabilities[id(record)]
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
