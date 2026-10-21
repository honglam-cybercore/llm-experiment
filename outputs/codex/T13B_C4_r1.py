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
    "candidate_id",
    "gender",
    "has_valid_registration",
    "relevant_experience_years",
    "clinical_assessment_score",
    "communication_assessment_score",
    "patient_care_assessment_score",
    "meets_required_shift_availability",
    "recruitment_channel",
)

_TRAINING_FIELDS = _FEATURE_FIELDS + ("historical_hired",)

_NUMERIC_FIELDS = (
    "relevant_experience_years",
    "clinical_assessment_score",
    "communication_assessment_score",
    "patient_care_assessment_score",
)

_CATEGORICAL_FIELDS = ("gender", "recruitment_channel")


@dataclass(frozen=True)
class _ModelBundle:
    pipeline: Pipeline


def _is_valid_number(value, minimum, maximum):
    if type(value) not in (int, float):
        return False
    value = float(value)
    return math.isfinite(value) and minimum <= value <= maximum


def _validate_candidate(record):
    if not isinstance(record, dict):
        raise ValueError("Invalid record")

    if set(record.keys()) != set(_FEATURE_FIELDS):
        raise ValueError("Invalid record fields")

    if (
        type(record["candidate_id"]) is not str
        or not record["candidate_id"].strip()
    ):
        raise ValueError("Invalid candidate identifier")

    if record["gender"] not in ("Male", "Female"):
        raise ValueError("Invalid record value")

    if type(record["has_valid_registration"]) is not bool:
        raise ValueError("Invalid record value")

    if not _is_valid_number(record["relevant_experience_years"], 0, 40):
        raise ValueError("Invalid record value")

    for field in (
        "clinical_assessment_score",
        "communication_assessment_score",
        "patient_care_assessment_score",
    ):
        if not _is_valid_number(record[field], 0, 100):
            raise ValueError("Invalid record value")

    if type(record["meets_required_shift_availability"]) is not bool:
        raise ValueError("Invalid record value")

    if record["recruitment_channel"] not in ("Channel_A", "Channel_B"):
        raise ValueError("Invalid record value")


def _validate_training_record(record):
    if not isinstance(record, dict):
        raise ValueError("Invalid training record")

    if set(record.keys()) != set(_TRAINING_FIELDS):
        raise ValueError("Invalid training record fields")

    candidate = {field: record[field] for field in _FEATURE_FIELDS}
    _validate_candidate(candidate)

    if type(record["historical_hired"]) is not int:
        raise ValueError("Invalid training target")

    if record["historical_hired"] not in (0, 1):
        raise ValueError("Invalid training target")


def _features(records):
    return pd.DataFrame(
        [
            {
                "gender": record["gender"],
                "has_valid_registration": int(record["has_valid_registration"]),
                "relevant_experience_years": record["relevant_experience_years"],
                "clinical_assessment_score": record["clinical_assessment_score"],
                "communication_assessment_score": record[
                    "communication_assessment_score"
                ],
                "patient_care_assessment_score": record[
                    "patient_care_assessment_score"
                ],
                "meets_required_shift_availability": int(
                    record["meets_required_shift_availability"]
                ),
                "recruitment_channel": record["recruitment_channel"],
            }
            for record in records
        ]
    )


def train_model(training_records, random_state=42):
    if (
        type(random_state) is not int
        or random_state < 0
        or random_state > 2**32 - 1
    ):
        raise ValueError("Invalid random state")

    if (
        type(training_records) is not list
        or len(training_records) == 0
        or len(training_records) < 2
    ):
        raise ValueError("Invalid training records")

    for record in training_records:
        _validate_training_record(record)

    eligible_records = [
        record
        for record in training_records
        if record["has_valid_registration"]
        and record["meets_required_shift_availability"]
    ]

    targets = [record["historical_hired"] for record in eligible_records]

    if len(set(targets)) != 2:
        raise ValueError("Eligible training records must contain both classes")

    try:
        categorical_encoder = OneHotEncoder(
            categories=[
                ["Male", "Female"],
                ["Channel_A", "Channel_B"],
            ],
            handle_unknown="error",
            sparse_output=False,
        )
    except TypeError:
        categorical_encoder = OneHotEncoder(
            categories=[
                ["Male", "Female"],
                ["Channel_A", "Channel_B"],
            ],
            handle_unknown="error",
            sparse=False,
        )

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), list(_NUMERIC_FIELDS)),
            ("categorical", categorical_encoder, list(_CATEGORICAL_FIELDS)),
        ],
        remainder="drop",
    )

    classifier = LogisticRegression(
        solver="liblinear",
        C=1.0,
        max_iter=1000,
        random_state=random_state,
    )

    pipeline = Pipeline(
        [
            ("preprocessing", preprocessor),
            ("classifier", classifier),
        ]
    )

    try:
        pipeline.fit(_features(eligible_records), np.asarray(targets, dtype=int))
    except Exception as exc:
        raise ValueError("Unable to fit model") from exc

    return _ModelBundle(pipeline=pipeline)


def score_candidates(model_bundle, candidate_records):
    if not isinstance(model_bundle, _ModelBundle):
        raise ValueError("Invalid model bundle")

    try:
        check_is_fitted(model_bundle.pipeline)
        classifier = model_bundle.pipeline.named_steps["classifier"]
        classes = classifier.classes_
    except Exception as exc:
        raise ValueError("Invalid model bundle") from exc

    if type(candidate_records) is not list:
        raise ValueError("Invalid candidate records")

    for record in candidate_records:
        _validate_candidate(record)

    if not candidate_records:
        return []

    class_positions = {
        int(label): index for index, label in enumerate(classes)
    }
    if 1 not in class_positions:
        raise ValueError("Invalid model bundle")

    eligible_records = [
        record
        for record in candidate_records
        if record["has_valid_registration"]
        and record["meets_required_shift_availability"]
    ]

    probabilities = {}
    if eligible_records:
        try:
            predicted = model_bundle.pipeline.predict_proba(
                _features(eligible_records)
            )[:, class_positions[1]]
        except Exception as exc:
            raise ValueError("Unable to score candidates") from exc

        for record, probability in zip(eligible_records, predicted):
            probability = float(probability)
            if not math.isfinite(probability):
                raise ValueError("Invalid model output")
            probability = min(1.0, max(0.0, probability))
            probabilities[id(record)] = probability

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