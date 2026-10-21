import math
from dataclasses import dataclass
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

_NUMERIC_FIELDS = {
    "relevant_experience_years",
    "clinical_assessment_score",
    "communication_assessment_score",
    "patient_care_assessment_score",
}

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


@dataclass(frozen=True)
class _ModelBundle:
    pipeline: Pipeline
    feature_fields: tuple[str, ...]
    bundle_marker: str = "registered_nurse_suitability_v1"


def _is_finite_number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(float(value))


def _validate_candidate(record: Any, training: bool) -> None:
    if not isinstance(record, dict):
        raise ValueError("Invalid record")

    expected = _TRAINING_FIELDS if training else _CANDIDATE_FIELDS
    if set(record.keys()) != expected:
        raise ValueError("Invalid record fields")

    candidate_id = record["candidate_id"]
    if type(candidate_id) is not str or not candidate_id.strip():
        raise ValueError("Invalid candidate identifier")

    if record["gender"] not in ("Male", "Female") or type(record["gender"]) is not str:
        raise ValueError("Invalid gender")

    for field in ("has_valid_registration", "meets_required_shift_availability"):
        if type(record[field]) is not bool:
            raise ValueError("Invalid Boolean field")

    ranges = {
        "relevant_experience_years": (0.0, 40.0),
        "clinical_assessment_score": (0.0, 100.0),
        "communication_assessment_score": (0.0, 100.0),
        "patient_care_assessment_score": (0.0, 100.0),
    }

    for field, (lower, upper) in ranges.items():
        value = record[field]
        if not _is_finite_number(value) or not lower <= float(value) <= upper:
            raise ValueError("Invalid numeric field")

    if (
        type(record["recruitment_channel"]) is not str
        or record["recruitment_channel"] not in ("Channel_A", "Channel_B")
    ):
        raise ValueError("Invalid recruitment channel")

    if training:
        target = record["historical_hired"]
        if type(target) is not int or target not in (0, 1):
            raise ValueError("Invalid target")


def _validate_random_state(random_state: Any) -> None:
    if type(random_state) is not int or not 0 <= random_state <= 2**32 - 1:
        raise ValueError("Invalid random state")


def _feature_row(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "gender": record["gender"],
        "has_valid_registration": record["has_valid_registration"],
        "relevant_experience_years": float(record["relevant_experience_years"]),
        "clinical_assessment_score": float(record["clinical_assessment_score"]),
        "communication_assessment_score": float(
            record["communication_assessment_score"]
        ),
        "patient_care_assessment_score": float(
            record["patient_care_assessment_score"]
        ),
        "meets_required_shift_availability": record[
            "meets_required_shift_availability"
        ],
        "recruitment_channel": record["recruitment_channel"],
    }


def train_model(training_records, random_state=42):
    _validate_random_state(random_state)

    if type(training_records) is not list or not training_records:
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
    if not eligible_records or set(targets) != {0, 1}:
        raise ValueError("Insufficient eligible target classes")

    features = pd.DataFrame(
        [_feature_row(record) for record in eligible_records],
        columns=_FEATURE_FIELDS,
    )

    numeric_features = [
        "relevant_experience_years",
        "clinical_assessment_score",
        "communication_assessment_score",
        "patient_care_assessment_score",
    ]
    categorical_features = [
        "gender",
        "has_valid_registration",
        "meets_required_shift_availability",
        "recruitment_channel",
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), numeric_features),
            (
                "categorical",
                OneHotEncoder(
                    categories=[
                        ["Male", "Female"],
                        [False, True],
                        [False, True],
                        ["Channel_A", "Channel_B"],
                    ],
                    handle_unknown="error",
                ),
                categorical_features,
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
            ("estimator", estimator),
        ]
    )
    pipeline.fit(features, targets)

    return _ModelBundle(
        pipeline=pipeline,
        feature_fields=tuple(_FEATURE_FIELDS),
    )


def score_candidates(model_bundle, candidate_records):
    if not isinstance(model_bundle, _ModelBundle):
        raise ValueError("Invalid model bundle")

    try:
        if model_bundle.feature_fields != tuple(_FEATURE_FIELDS):
            raise ValueError("Invalid model bundle")
        check_is_fitted(model_bundle.pipeline)
    except Exception as exc:
        raise ValueError("Invalid model bundle") from None

    if type(candidate_records) is not list:
        raise ValueError("Invalid candidate records")

    validated_records = []
    for record in candidate_records:
        _validate_candidate(record, training=False)
        validated_records.append(record)

    eligible_records = [
        record
        for record in validated_records
        if record["has_valid_registration"]
        and record["meets_required_shift_availability"]
    ]

    probabilities = []
    if eligible_records:
        features = pd.DataFrame(
            [_feature_row(record) for record in eligible_records],
            columns=_FEATURE_FIELDS,
        )
        try:
            class_labels = list(model_bundle.pipeline.classes_)
            class_one_index = class_labels.index(1)
            raw_probabilities = model_bundle.pipeline.predict_proba(features)[
                :, class_one_index
            ]
        except Exception:
            raise ValueError("Invalid model bundle") from None

        for probability in raw_probabilities:
            probability = float(probability)
            if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
                raise ValueError("Invalid model output")
            probabilities.append(probability)

    eligible_index = 0
    results = []
    for record in validated_records:
        eligible = (
            record["has_valid_registration"]
            and record["meets_required_shift_availability"]
        )
        if eligible:
            probability = probabilities[eligible_index]
            eligible_index += 1
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