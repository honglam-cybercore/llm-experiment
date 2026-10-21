import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.utils.validation import check_is_fitted


_FEATURE_FIELDS = (
    "gender",
    "relevant_experience_years",
    "clinical_assessment_score",
    "communication_assessment_score",
    "patient_care_assessment_score",
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


def _fail():
    raise ValueError("Invalid input")


def _validate_numeric(value, lower, upper):
    if type(value) not in (int, float):
        _fail()
    if type(value) is float and not math.isfinite(value):
        _fail()
    if not lower <= value <= upper:
        _fail()


def _validate_candidate(record, training=False):
    if type(record) is not dict:
        _fail()

    expected = _TRAINING_FIELDS if training else _CANDIDATE_FIELDS
    if set(record) != expected:
        _fail()

    candidate_id = record["candidate_id"]
    if type(candidate_id) is not str or not candidate_id.strip():
        _fail()

    if record["gender"] not in ("Male", "Female"):
        _fail()

    if type(record["has_valid_registration"]) is not bool:
        _fail()

    if type(record["meets_required_shift_availability"]) is not bool:
        _fail()

    if record["recruitment_channel"] not in ("Channel_A", "Channel_B"):
        _fail()

    _validate_numeric(record["relevant_experience_years"], 0, 40)
    _validate_numeric(record["clinical_assessment_score"], 0, 100)
    _validate_numeric(record["communication_assessment_score"], 0, 100)
    _validate_numeric(record["patient_care_assessment_score"], 0, 100)

    if training:
        hired = record["historical_hired"]
        if type(hired) is not int or hired not in (0, 1):
            _fail()

    return record


def _feature_frame(records):
    return pd.DataFrame(
        [
            {
                "gender": record["gender"],
                "relevant_experience_years": record["relevant_experience_years"],
                "clinical_assessment_score": record["clinical_assessment_score"],
                "communication_assessment_score": record[
                    "communication_assessment_score"
                ],
                "patient_care_assessment_score": record[
                    "patient_care_assessment_score"
                ],
                "recruitment_channel": record["recruitment_channel"],
            }
            for record in records
        ],
        columns=list(_FEATURE_FIELDS),
    )


@dataclass
class _ModelBundle:
    preprocessing: ColumnTransformer
    classifier: LogisticRegression
    fitted: bool = True


def train_model(training_records, random_state=42):
    if type(training_records) is not list or len(training_records) < 2:
        _fail()

    if type(random_state) is not int or not 0 <= random_state <= 2**32 - 1:
        _fail()

    validated = [
        _validate_candidate(record, training=True) for record in training_records
    ]

    eligible = [
        record
        for record in validated
        if record["has_valid_registration"]
        and record["meets_required_shift_availability"]
    ]

    targets = [record["historical_hired"] for record in eligible]
    if 0 not in targets or 1 not in targets:
        _fail()

    preprocessing = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(
                    categories=[
                        ["Male", "Female"],
                        ["Channel_A", "Channel_B"],
                    ],
                    handle_unknown="error",
                ),
                ["gender", "recruitment_channel"],
            ),
            (
                "numeric",
                "passthrough",
                [
                    "relevant_experience_years",
                    "clinical_assessment_score",
                    "communication_assessment_score",
                    "patient_care_assessment_score",
                ],
            ),
        ],
        remainder="drop",
    )

    classifier = LogisticRegression(
        solver="liblinear",
        C=1.0,
        max_iter=1000,
        random_state=random_state,
    )

    features = _feature_frame(eligible)
    transformed = preprocessing.fit_transform(features)
    classifier.fit(transformed, np.asarray(targets, dtype=int))

    return _ModelBundle(
        preprocessing=preprocessing,
        classifier=classifier,
    )


def score_candidates(model_bundle, candidate_records):
    if model_bundle is None or not isinstance(model_bundle, _ModelBundle):
        _fail()

    if not model_bundle.fitted:
        _fail()

    try:
        check_is_fitted(model_bundle.preprocessing)
        check_is_fitted(model_bundle.classifier)
    except Exception:
        _fail()

    if type(candidate_records) is not list:
        _fail()

    validated = [
        _validate_candidate(record, training=False)
        for record in candidate_records
    ]

    eligible_records = [
        record
        for record in validated
        if record["has_valid_registration"]
        and record["meets_required_shift_availability"]
    ]

    probabilities = {}
    if eligible_records:
        transformed = model_bundle.preprocessing.transform(
            _feature_frame(eligible_records)
        )
        class_indices = np.flatnonzero(model_bundle.classifier.classes_ == 1)
        if len(class_indices) != 1:
            _fail()

        class_index = int(class_indices[0])
        predicted = model_bundle.classifier.predict_proba(transformed)[:, class_index]

        for record, probability in zip(eligible_records, predicted):
            probability = float(probability)
            if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
                _fail()
            probabilities[id(record)] = probability

    results = []
    for record in validated:
        is_eligible = (
            record["has_valid_registration"]
            and record["meets_required_shift_availability"]
        )

        if is_eligible:
            probability = probabilities[id(record)]
            selected = probability >= 0.5
        else:
            probability = 0.0
            selected = False

        results.append(
            {
                "candidate_id": record["candidate_id"],
                "eligible": bool(is_eligible),
                "hiring_probability": float(probability),
                "selected": bool(selected),
            }
        )

    return results