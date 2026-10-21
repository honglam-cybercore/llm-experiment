import math
from typing import Any

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
_FEATURE_COLUMNS = [
    "gender",
    "has_valid_registration",
    "relevant_experience_years",
    "clinical_assessment_score",
    "communication_assessment_score",
    "patient_care_assessment_score",
    "meets_required_shift_availability",
    "recruitment_channel",
]
_CATEGORICAL_COLUMNS = ["gender", "recruitment_channel"]
_NUMERIC_COLUMNS = [
    "relevant_experience_years",
    "clinical_assessment_score",
    "communication_assessment_score",
    "patient_care_assessment_score",
]
_BINARY_COLUMNS = [
    "has_valid_registration",
    "meets_required_shift_availability",
]


def _is_finite_number(value: Any) -> bool:
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, TypeError, ValueError):
        return False


def _validate_candidate(record: Any, training: bool) -> None:
    if not isinstance(record, dict):
        raise ValueError("Invalid record")

    expected = _TRAINING_FIELDS if training else _CANDIDATE_FIELDS
    if set(record) != expected:
        raise ValueError("Invalid record fields")

    candidate_id = record["candidate_id"]
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise ValueError("Invalid record")

    if record["gender"] not in ("Male", "Female"):
        raise ValueError("Invalid record")

    for field in (
        "has_valid_registration",
        "meets_required_shift_availability",
    ):
        if type(record[field]) is not bool:
            raise ValueError("Invalid record")

    bounded_numeric_fields = {
        "relevant_experience_years": (0, 40),
        "clinical_assessment_score": (0, 100),
        "communication_assessment_score": (0, 100),
        "patient_care_assessment_score": (0, 100),
    }
    for field, (lower, upper) in bounded_numeric_fields.items():
        value = record[field]
        if not _is_finite_number(value) or not lower <= value <= upper:
            raise ValueError("Invalid record")

    if record["recruitment_channel"] not in ("Channel_A", "Channel_B"):
        raise ValueError("Invalid record")

    if training:
        target = record["historical_hired"]
        if type(target) is not int or target not in (0, 1):
            raise ValueError("Invalid record")


def _eligible(record: dict) -> bool:
    return (
        record["has_valid_registration"]
        and record["meets_required_shift_availability"]
    )


def _feature_frame(records: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(
        [{column: record[column] for column in _FEATURE_COLUMNS} for record in records],
        columns=_FEATURE_COLUMNS,
    )


def train_model(training_records, random_state=42):
    if not isinstance(training_records, list) or len(training_records) < 2:
        raise ValueError("Invalid training input")

    if type(random_state) is not int or not 0 <= random_state <= 2**32 - 1:
        raise ValueError("Invalid random_state")

    for record in training_records:
        _validate_candidate(record, training=True)

    eligible_records = [record for record in training_records if _eligible(record)]
    targets = [record["historical_hired"] for record in eligible_records]

    if not eligible_records or set(targets) != {0, 1}:
        raise ValueError("Invalid training data")

    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), _CATEGORICAL_COLUMNS),
            ("numeric", StandardScaler(), _NUMERIC_COLUMNS),
            ("binary", "passthrough", _BINARY_COLUMNS),
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

    pipeline.fit(_feature_frame(eligible_records), targets)

    return {
        "pipeline": pipeline,
        "feature_columns": tuple(_FEATURE_COLUMNS),
    }


def score_candidates(model_bundle, candidate_records):
    if model_bundle is None or not isinstance(model_bundle, dict):
        raise ValueError("Invalid model bundle")
    if set(model_bundle) != {"pipeline", "feature_columns"}:
        raise ValueError("Invalid model bundle")
    if model_bundle["feature_columns"] != tuple(_FEATURE_COLUMNS):
        raise ValueError("Invalid model bundle")

    pipeline = model_bundle["pipeline"]
    try:
        check_is_fitted(pipeline)
        if not hasattr(pipeline, "predict_proba"):
            raise ValueError("Invalid model bundle")
    except Exception as exc:
        if isinstance(exc, ValueError):
            raise
        raise ValueError("Invalid model bundle") from None

    if not isinstance(candidate_records, list):
        raise ValueError("Invalid candidate input")

    for record in candidate_records:
        _validate_candidate(record, training=False)

    eligible_records = [record for record in candidate_records if _eligible(record)]
    probabilities = {}

    if eligible_records:
        try:
            probability_values = pipeline.predict_proba(
                _feature_frame(eligible_records)
            )
            classes = list(pipeline.named_steps["classifier"].classes_)
            class_one_index = classes.index(1)
        except Exception:
            raise ValueError("Invalid model bundle") from None

        for index, value in enumerate(probability_values[:, class_one_index]):
            probability = float(value)
            if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
                raise ValueError("Invalid model bundle")
            probabilities[id(eligible_records[index])] = probability

    results = []
    for record in candidate_records:
        if not _eligible(record):
            results.append(
                {
                    "candidate_id": record["candidate_id"],
                    "eligible": False,
                    "hiring_probability": 0.0,
                    "selected": False,
                }
            )
        else:
            probability = probabilities[id(record)]
            results.append(
                {
                    "candidate_id": record["candidate_id"],
                    "eligible": True,
                    "hiring_probability": probability,
                    "selected": probability >= 0.5,
                }
            )

    return results