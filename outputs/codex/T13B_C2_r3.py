import math

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.utils.validation import check_is_fitted


_BASE_FIELDS = {
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

_TRAINING_FIELDS = _BASE_FIELDS | {"historical_hired"}

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
    "has_valid_registration",
    "relevant_experience_years",
    "clinical_assessment_score",
    "communication_assessment_score",
    "patient_care_assessment_score",
    "meets_required_shift_availability",
]


def _fail():
    raise ValueError("invalid input")


def _validate_random_state(random_state):
    if type(random_state) is not int or not 0 <= random_state <= 2**32 - 1:
        _fail()


def _validate_record(record, training):
    if not isinstance(record, dict):
        _fail()

    expected = _TRAINING_FIELDS if training else _BASE_FIELDS
    if set(record.keys()) != expected:
        _fail()

    candidate_id = record["candidate_id"]
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        _fail()

    if record["gender"] not in ("Male", "Female"):
        _fail()

    if type(record["has_valid_registration"]) is not bool:
        _fail()

    if type(record["meets_required_shift_availability"]) is not bool:
        _fail()

    for field, lower, upper in (
        ("relevant_experience_years", 0, 40),
        ("clinical_assessment_score", 0, 100),
        ("communication_assessment_score", 0, 100),
        ("patient_care_assessment_score", 0, 100),
    ):
        value = record[field]
        if type(value) not in (int, float):
            _fail()
        if not math.isfinite(value) or not lower <= value <= upper:
            _fail()

    if record["recruitment_channel"] not in ("Channel_A", "Channel_B"):
        _fail()

    if training:
        target = record["historical_hired"]
        if type(target) is not int or target not in (0, 1):
            _fail()


def _feature_frame(records):
    rows = []
    for record in records:
        row = {column: record[column] for column in _FEATURE_COLUMNS}
        row["has_valid_registration"] = int(row["has_valid_registration"])
        row["meets_required_shift_availability"] = int(
            row["meets_required_shift_availability"]
        )
        rows.append(row)
    return pd.DataFrame(rows, columns=_FEATURE_COLUMNS)


def _is_eligible(record):
    return (
        record["has_valid_registration"]
        and record["meets_required_shift_availability"]
    )


def train_model(training_records, random_state=42):
    _validate_random_state(random_state)

    if not isinstance(training_records, list) or not training_records:
        _fail()
    if len(training_records) < 2:
        _fail()

    for record in training_records:
        _validate_record(record, training=True)

    eligible_records = [
        record for record in training_records if _is_eligible(record)
    ]
    targets = [record["historical_hired"] for record in eligible_records]

    if not eligible_records or set(targets) != {0, 1}:
        _fail()

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), _NUMERIC_COLUMNS),
            (
                "categorical",
                OneHotEncoder(
                    categories=[["Male", "Female"], ["Channel_A", "Channel_B"]],
                    handle_unknown="ignore",
                ),
                _CATEGORICAL_COLUMNS,
            ),
        ]
    )

    classifier = LogisticRegression(
        solver="liblinear",
        C=1.0,
        max_iter=1000,
        random_state=random_state,
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )
    model.fit(_feature_frame(eligible_records), targets)

    return {"model": model}


def score_candidates(model_bundle, candidate_records):
    if not isinstance(model_bundle, dict):
        _fail()
    if set(model_bundle.keys()) != {"model"}:
        _fail()
    model = model_bundle.get("model")
    if model is None:
        _fail()

    try:
        check_is_fitted(model)
    except Exception:
        _fail()

    if not isinstance(candidate_records, list):
        _fail()

    for record in candidate_records:
        _validate_record(record, training=False)

    if not candidate_records:
        return []

    eligible_records = [record for record in candidate_records if _is_eligible(record)]
    probabilities = {}

    if eligible_records:
        try:
            probability_matrix = model.predict_proba(
                _feature_frame(eligible_records)
            )
            classes = list(model.named_steps["classifier"].classes_)
            class_one_index = classes.index(1)
        except Exception:
            _fail()

        for record, row in zip(eligible_records, probability_matrix):
            probability = float(row[class_one_index])
            if not math.isfinite(probability):
                _fail()
            probability = max(0.0, min(1.0, probability))
            probabilities[id(record)] = probability

    results = []
    for record in candidate_records:
        if _is_eligible(record):
            probability = probabilities[id(record)]
            results.append(
                {
                    "candidate_id": record["candidate_id"],
                    "eligible": True,
                    "hiring_probability": probability,
                    "selected": bool(probability >= 0.5),
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