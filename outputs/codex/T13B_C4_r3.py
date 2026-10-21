import math
from dataclasses import dataclass

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

_CATEGORICAL_FEATURES = ["gender", "recruitment_channel"]
_NUMERIC_FEATURES = [
    "relevant_experience_years",
    "clinical_assessment_score",
    "communication_assessment_score",
    "patient_care_assessment_score",
]

_FEATURE_COLUMNS = _CATEGORICAL_FEATURES + _NUMERIC_FEATURES


def _require_fields(record, fields):
    if not isinstance(record, dict) or set(record.keys()) != fields:
        raise ValueError("invalid record fields")


def _validate_string(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("invalid string field")


def _validate_bool(value):
    if type(value) is not bool:
        raise ValueError("invalid boolean field")


def _validate_number(value, lower, upper):
    if type(value) not in (int, float):
        raise ValueError("invalid numeric field")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("invalid numeric field")
    if value < lower or value > upper:
        raise ValueError("numeric field out of range")


def _validate_candidate(record):
    _require_fields(record, _CANDIDATE_FIELDS)

    _validate_string(record["candidate_id"])

    if record["gender"] not in ("Male", "Female"):
        raise ValueError("invalid gender")
    if record["recruitment_channel"] not in ("Channel_A", "Channel_B"):
        raise ValueError("invalid recruitment channel")

    _validate_bool(record["has_valid_registration"])
    _validate_bool(record["meets_required_shift_availability"])

    _validate_number(record["relevant_experience_years"], 0, 40)
    _validate_number(record["clinical_assessment_score"], 0, 100)
    _validate_number(record["communication_assessment_score"], 0, 100)
    _validate_number(record["patient_care_assessment_score"], 0, 100)


def _validate_training_record(record):
    _require_fields(record, _TRAINING_FIELDS)
    _validate_candidate(record)

    if type(record["historical_hired"]) is not int:
        raise ValueError("invalid target")
    if record["historical_hired"] not in (0, 1):
        raise ValueError("invalid target")


def _records_dataframe(records):
    return pd.DataFrame(
        [{column: record[column] for column in _FEATURE_COLUMNS} for record in records],
        columns=_FEATURE_COLUMNS,
    )


@dataclass
class _ModelBundle:
    pipeline: Pipeline


def train_model(training_records, random_state=42):
    if not isinstance(training_records, list) or not training_records:
        raise ValueError("training records must be a non-empty list")

    if type(random_state) is not int or not (0 <= random_state <= 2**32 - 1):
        raise ValueError("invalid random state")

    validated_records = []
    for record in training_records:
        _validate_training_record(record)
        validated_records.append(record)

    eligible_records = [
        record
        for record in validated_records
        if record["has_valid_registration"]
        and record["meets_required_shift_availability"]
    ]

    targets = [record["historical_hired"] for record in eligible_records]
    if not eligible_records or set(targets) != {0, 1}:
        raise ValueError("eligible records must contain both target classes")

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(
                    categories=[["Male", "Female"], ["Channel_A", "Channel_B"]],
                    handle_unknown="ignore",
                ),
                _CATEGORICAL_FEATURES,
            ),
            ("numeric", StandardScaler(), _NUMERIC_FEATURES),
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
        steps=[
            ("preprocessing", preprocessor),
            ("classifier", classifier),
        ]
    )

    pipeline.fit(_records_dataframe(eligible_records), targets)
    return _ModelBundle(pipeline=pipeline)


def score_candidates(model_bundle, candidate_records):
    if not isinstance(model_bundle, _ModelBundle):
        raise ValueError("invalid model bundle")

    if not isinstance(candidate_records, list):
        raise ValueError("candidate records must be a list")

    try:
        check_is_fitted(model_bundle.pipeline)
    except Exception:
        raise ValueError("unfitted model bundle") from None

    validated_records = []
    for record in candidate_records:
        _validate_candidate(record)
        validated_records.append(record)

    if not validated_records:
        return []

    eligible_records = [
        record
        for record in validated_records
        if record["has_valid_registration"]
        and record["meets_required_shift_availability"]
    ]

    probabilities = {}
    if eligible_records:
        try:
            probability_matrix = model_bundle.pipeline.predict_proba(
                _records_dataframe(eligible_records)
            )
            classes = list(model_bundle.pipeline.named_steps["classifier"].classes_)
            class_one_index = classes.index(1)
        except Exception:
            raise ValueError("unable to score candidates") from None

        for record, row in zip(eligible_records, probability_matrix):
            probability = float(row[class_one_index])
            if not math.isfinite(probability) or not 0 <= probability <= 1:
                raise ValueError("invalid model probability")
            probabilities[id(record)] = probability

    results = []
    for record in validated_records:
        if (
            record["has_valid_registration"]
            and record["meets_required_shift_availability"]
        ):
            probability = probabilities[id(record)]
            eligible = True
            selected = probability >= 0.5
        else:
            probability = 0.0
            eligible = False
            selected = False

        results.append(
            {
                "candidate_id": record["candidate_id"],
                "eligible": eligible,
                "hiring_probability": probability,
                "selected": selected,
            }
        )

    return results