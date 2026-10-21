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

_NUMERIC_FIELDS = (
    "relevant_experience_years",
    "clinical_assessment_score",
    "communication_assessment_score",
    "patient_care_assessment_score",
)

_FEATURE_FIELDS = (
    "relevant_experience_years",
    "clinical_assessment_score",
    "communication_assessment_score",
    "patient_care_assessment_score",
    "recruitment_channel",
)


class _ModelBundle:
    __slots__ = ("_pipeline",)

    def __init__(self, pipeline: Pipeline) -> None:
        self._pipeline = pipeline


def _validate_field_set(record: Any, expected: set[str]) -> None:
    if type(record) is not dict or set(record.keys()) != expected:
        raise ValueError("Invalid record fields.")


def _validate_candidate_record(record: Any) -> None:
    _validate_field_set(record, _CANDIDATE_FIELDS)

    if type(record["candidate_id"]) is not str or not record["candidate_id"].strip():
        raise ValueError("Invalid candidate record.")

    if record["gender"] not in ("Male", "Female") or type(record["gender"]) is not str:
        raise ValueError("Invalid candidate record.")

    if type(record["has_valid_registration"]) is not bool:
        raise ValueError("Invalid candidate record.")

    if type(record["meets_required_shift_availability"]) is not bool:
        raise ValueError("Invalid candidate record.")

    if record["recruitment_channel"] not in ("Channel_A", "Channel_B") or type(
        record["recruitment_channel"]
    ) is not str:
        raise ValueError("Invalid candidate record.")

    ranges = {
        "relevant_experience_years": (0.0, 40.0),
        "clinical_assessment_score": (0.0, 100.0),
        "communication_assessment_score": (0.0, 100.0),
        "patient_care_assessment_score": (0.0, 100.0),
    }

    for field, (lower, upper) in ranges.items():
        value = record[field]
        if type(value) not in (int, float):
            raise ValueError("Invalid candidate record.")
        if not math.isfinite(value) or not lower <= value <= upper:
            raise ValueError("Invalid candidate record.")


def _validate_training_record(record: Any) -> None:
    _validate_field_set(record, _TRAINING_FIELDS)
    _validate_candidate_record(record)

    target = record["historical_hired"]
    if type(target) is not int or target not in (0, 1):
        raise ValueError("Invalid training record.")


def _feature_frame(records: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(
        [{field: record[field] for field in _FEATURE_FIELDS} for record in records],
        columns=list(_FEATURE_FIELDS),
    )


def train_model(training_records, random_state=42):
    if type(random_state) is not int or not 0 <= random_state <= 2**32 - 1:
        raise ValueError("Invalid random state.")

    if type(training_records) is not list or len(training_records) < 2:
        raise ValueError("Invalid training data.")

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
    if len(set(targets)) != 2:
        raise ValueError("Eligible training data must contain both target classes.")

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                StandardScaler(),
                list(_NUMERIC_FIELDS),
            ),
            (
                "categorical",
                OneHotEncoder(handle_unknown="error"),
                ["recruitment_channel"],
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

    try:
        pipeline.fit(_feature_frame(eligible_records), targets)
    except Exception:
        raise ValueError("Unable to fit model.") from None

    return _ModelBundle(pipeline)


def score_candidates(model_bundle, candidate_records):
    if model_bundle is None or type(model_bundle) is not _ModelBundle:
        raise ValueError("Invalid model bundle.")

    if type(candidate_records) is not list:
        raise ValueError("Invalid candidate data.")

    pipeline = model_bundle._pipeline
    try:
        check_is_fitted(pipeline)
        if not isinstance(pipeline, Pipeline) or not hasattr(pipeline, "predict_proba"):
            raise ValueError
    except Exception:
        raise ValueError("Invalid model bundle.") from None

    validated_records = []
    for record in candidate_records:
        _validate_candidate_record(record)
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
            predicted = pipeline.predict_proba(_feature_frame(eligible_records))
            classes = list(pipeline.named_steps["classifier"].classes_)
            class_one_index = classes.index(1)
            for record, row in zip(eligible_records, predicted):
                probability = float(row[class_one_index])
                if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
                    raise ValueError
                probabilities[id(record)] = probability
        except Exception:
            raise ValueError("Unable to score candidates.") from None

    results = []
    for record in validated_records:
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