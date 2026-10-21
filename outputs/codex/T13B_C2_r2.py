import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.utils.validation import check_is_fitted


_FEATURE_FIELDS = {
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

_TRAINING_FIELDS = _FEATURE_FIELDS | {"historical_hired"}

_NUMERIC_FIELDS = [
    "relevant_experience_years",
    "clinical_assessment_score",
    "communication_assessment_score",
    "patient_care_assessment_score",
]

_CATEGORICAL_FIELDS = ["gender", "recruitment_channel"]
_BOOLEAN_FIELDS = [
    "has_valid_registration",
    "meets_required_shift_availability",
]


@dataclass
class _ModelBundle:
    pipeline: Pipeline
    class_one_probability_index: int
    _fitted: bool = True


def _validate_record(record, training):
    if not isinstance(record, dict):
        raise ValueError("Invalid record")

    expected = _TRAINING_FIELDS if training else _FEATURE_FIELDS
    if set(record.keys()) != expected:
        raise ValueError("Invalid record fields")

    candidate_id = record["candidate_id"]
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise ValueError("Invalid record")

    if type(record["gender"]) is not str or record["gender"] not in {
        "Male",
        "Female",
    }:
        raise ValueError("Invalid record")

    for field in _BOOLEAN_FIELDS:
        if type(record[field]) is not bool:
            raise ValueError("Invalid record")

    numeric_bounds = {
        "relevant_experience_years": (0, 40),
        "clinical_assessment_score": (0, 100),
        "communication_assessment_score": (0, 100),
        "patient_care_assessment_score": (0, 100),
    }

    for field, (lower, upper) in numeric_bounds.items():
        value = record[field]
        if type(value) not in (int, float):
            raise ValueError("Invalid record")
        if not math.isfinite(value) or value < lower or value > upper:
            raise ValueError("Invalid record")

    if type(record["recruitment_channel"]) is not str or record[
        "recruitment_channel"
    ] not in {"Channel_A", "Channel_B"}:
        raise ValueError("Invalid record")

    if training:
        target = record["historical_hired"]
        if type(target) is not int or target not in (0, 1):
            raise ValueError("Invalid record")


def _feature_frame(records):
    return pd.DataFrame(
        [{field: record[field] for field in _FEATURE_FIELDS} for record in records],
        columns=[
            "candidate_id",
            "gender",
            "has_valid_registration",
            "relevant_experience_years",
            "clinical_assessment_score",
            "communication_assessment_score",
            "patient_care_assessment_score",
            "meets_required_shift_availability",
            "recruitment_channel",
        ],
    ).drop(columns=["candidate_id"])


def train_model(training_records, random_state=42):
    if not isinstance(training_records, list) or len(training_records) < 2:
        raise ValueError("Invalid training data")

    if type(random_state) is not int or not 0 <= random_state <= 2**32 - 1:
        raise ValueError("Invalid random state")

    for record in training_records:
        _validate_record(record, training=True)

    eligible_records = [
        record
        for record in training_records
        if record["has_valid_registration"]
        and record["meets_required_shift_availability"]
    ]

    targets = [record["historical_hired"] for record in eligible_records]
    if len(set(targets)) != 2:
        raise ValueError("Insufficient target classes")

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", "passthrough", _NUMERIC_FIELDS),
            (
                "categorical",
                OneHotEncoder(
                    handle_unknown="ignore",
                    categories=[
                        ["Male", "Female"],
                        ["Channel_A", "Channel_B"],
                    ],
                ),
                _CATEGORICAL_FIELDS,
            ),
        ]
    )

    classifier = LogisticRegression(
        solver="liblinear",
        C=1.0,
        max_iter=1000,
        random_state=random_state,
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )

    features = _feature_frame(eligible_records)
    pipeline.fit(features, np.asarray(targets, dtype=int))

    classes = list(pipeline.named_steps["classifier"].classes_)
    try:
        class_one_probability_index = classes.index(1)
    except ValueError as exc:
        raise ValueError("Invalid fitted model") from exc

    return _ModelBundle(
        pipeline=pipeline,
        class_one_probability_index=class_one_probability_index,
    )


def score_candidates(model_bundle, candidate_records):
    if not isinstance(model_bundle, _ModelBundle):
        raise ValueError("Invalid model bundle")
    if not model_bundle._fitted:
        raise ValueError("Invalid model bundle")

    try:
        check_is_fitted(model_bundle.pipeline)
        classifier = model_bundle.pipeline.named_steps["classifier"]
        classes = list(classifier.classes_)
        if model_bundle.class_one_probability_index != classes.index(1):
            raise ValueError("Invalid model bundle")
    except (AttributeError, TypeError, ValueError):
        raise ValueError("Invalid model bundle")

    if not isinstance(candidate_records, list):
        raise ValueError("Invalid candidate data")

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
            feature_values = _feature_frame(eligible_records)
            predicted = model_bundle.pipeline.predict_proba(feature_values)
            for record, row in zip(eligible_records, predicted):
                probability = float(row[model_bundle.class_one_probability_index])
                if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
                    raise ValueError("Invalid prediction")
                probabilities[id(record)] = probability
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("Invalid model bundle") from exc

    results = []
    for record in candidate_records:
        if (
            record["has_valid_registration"]
            and record["meets_required_shift_availability"]
        ):
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