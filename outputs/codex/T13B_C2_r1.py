import math
from typing import Any

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

_NUMERIC_FIELDS = (
    "relevant_experience_years",
    "clinical_assessment_score",
    "communication_assessment_score",
    "patient_care_assessment_score",
)

_FEATURE_FIELDS = (
    "gender",
    "relevant_experience_years",
    "clinical_assessment_score",
    "communication_assessment_score",
    "patient_care_assessment_score",
    "recruitment_channel",
)


class _ModelBundle:
    __slots__ = ("pipeline", "_fitted")

    def __init__(self, pipeline: Pipeline):
        self.pipeline = pipeline
        self._fitted = True


def _error() -> ValueError:
    return ValueError("Invalid input.")


def _validate_numeric(value: Any, lower: float, upper: float) -> None:
    if type(value) not in (int, float):
        raise _error()
    if not math.isfinite(value) or value < lower or value > upper:
        raise _error()


def _validate_record(record: Any, training: bool) -> None:
    if not isinstance(record, dict):
        raise _error()

    required = _TRAINING_FIELDS if training else _CANDIDATE_FIELDS
    if set(record.keys()) != required:
        raise _error()

    candidate_id = record["candidate_id"]
    if type(candidate_id) is not str or not candidate_id.strip():
        raise _error()

    if record["gender"] not in ("Male", "Female"):
        raise _error()

    if type(record["has_valid_registration"]) is not bool:
        raise _error()

    _validate_numeric(record["relevant_experience_years"], 0, 40)
    _validate_numeric(record["clinical_assessment_score"], 0, 100)
    _validate_numeric(record["communication_assessment_score"], 0, 100)
    _validate_numeric(record["patient_care_assessment_score"], 0, 100)

    if type(record["meets_required_shift_availability"]) is not bool:
        raise _error()

    if record["recruitment_channel"] not in ("Channel_A", "Channel_B"):
        raise _error()

    if training:
        if type(record["historical_hired"]) is not int:
            raise _error()
        if record["historical_hired"] not in (0, 1):
            raise _error()


def _feature_frame(records: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(
        [{field: record[field] for field in _FEATURE_FIELDS} for record in records],
        columns=list(_FEATURE_FIELDS),
    )


def _build_pipeline(random_state: int) -> Pipeline:
    categorical_features = ["gender", "recruitment_channel"]
    numeric_features = [
        "relevant_experience_years",
        "clinical_assessment_score",
        "communication_assessment_score",
        "patient_care_assessment_score",
    ]

    preprocessing = ColumnTransformer(
        transformers=[
            (
                "numeric",
                StandardScaler(),
                numeric_features,
            ),
            (
                "categorical",
                OneHotEncoder(
                    categories=[
                        ["Male", "Female"],
                        ["Channel_A", "Channel_B"],
                    ],
                    handle_unknown="error",
                ),
                categorical_features,
            ),
        ]
    )

    classifier = LogisticRegression(
        solver="liblinear",
        C=1.0,
        max_iter=1000,
        random_state=random_state,
    )

    return Pipeline(
        steps=[
            ("preprocessing", preprocessing),
            ("classifier", classifier),
        ]
    )


def train_model(training_records, random_state=42):
    if type(random_state) is not int or not 0 <= random_state <= 2**32 - 1:
        raise _error()

    if not isinstance(training_records, list) or len(training_records) < 2:
        raise _error()

    for record in training_records:
        _validate_record(record, training=True)

    eligible_records = [
        record
        for record in training_records
        if record["has_valid_registration"]
        and record["meets_required_shift_availability"]
    ]

    targets = [record["historical_hired"] for record in eligible_records]
    if set(targets) != {0, 1}:
        raise _error()

    pipeline = _build_pipeline(random_state)

    try:
        pipeline.fit(_feature_frame(eligible_records), np.asarray(targets, dtype=int))
    except Exception as exc:
        raise _error() from exc

    return _ModelBundle(pipeline)


def score_candidates(model_bundle, candidate_records):
    if not isinstance(model_bundle, _ModelBundle):
        raise _error()

    if getattr(model_bundle, "_fitted", False) is not True:
        raise _error()

    if not isinstance(getattr(model_bundle, "pipeline", None), Pipeline):
        raise _error()

    try:
        check_is_fitted(model_bundle.pipeline)
    except Exception as exc:
        raise _error() from exc

    if not isinstance(candidate_records, list):
        raise _error()

    for record in candidate_records:
        _validate_record(record, training=False)

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
        try:
            classifier = model_bundle.pipeline.named_steps["classifier"]
            classes = np.asarray(classifier.classes_)
            class_one_positions = np.flatnonzero(classes == 1)
            if len(class_one_positions) != 1:
                raise _error()

            class_one_index = int(class_one_positions[0])
            predicted = model_bundle.pipeline.predict_proba(
                _feature_frame(eligible_records)
            )[:, class_one_index]
        except ValueError:
            raise
        except Exception as exc:
            raise _error() from exc

        for record, probability in zip(eligible_records, predicted):
            probability = float(probability)
            if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
                raise _error()
            probabilities[id(record)] = probability

    results = []
    for record in candidate_records:
        if not (
            record["has_valid_registration"]
            and record["meets_required_shift_availability"]
        ):
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