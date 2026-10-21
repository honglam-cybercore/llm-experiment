"""Frozen fixtures and the robustness mutation catalogue for Task 13B.

Every table below is transcribed from the handover specification (B5). The
catalogue is built programmatically in the spec's own order and then checked
against the counts the spec states: 102 training cases, 85 prediction cases,
2 model-state cases, 189 in total. A mismatch raises at import time, so a
drifted catalogue cannot be used silently.
"""
from __future__ import annotations

import copy

EPS = 1e-8

TRAIN_FIELDS = ("candidate_id", "gender", "has_valid_registration",
                "relevant_experience_years", "clinical_assessment_score",
                "communication_assessment_score", "patient_care_assessment_score",
                "meets_required_shift_availability", "recruitment_channel",
                "historical_hired")
PRED_FIELDS = TRAIN_FIELDS[:-1]
NUMERIC = ("relevant_experience_years", "clinical_assessment_score",
           "communication_assessment_score", "patient_care_assessment_score")
ELIGIBILITY = ("has_valid_registration", "meets_required_shift_availability")

BASE_B = {
    "candidate_id": "BASE_B",
    "gender": "Male",
    "has_valid_registration": True,
    "relevant_experience_years": 5,
    "clinical_assessment_score": 50,
    "communication_assessment_score": 50,
    "patient_care_assessment_score": 50,
    "meets_required_shift_availability": True,
    "recruitment_channel": "Channel_A",
}


def base_b(**changes) -> dict:
    out = copy.deepcopy(BASE_B)
    out.update(changes)
    return out


def minimal_train() -> list[dict]:
    """MINIMAL_TRAIN: four profiles x Male/Female. Assessments all 20,40,80,100,
    experience 0,2,8,10, channel alternating A/B by profile, labels 0,0,1,1.
    Each call returns independent dictionaries."""
    rows = []
    for index, (level, exp, label) in enumerate(
            ((20, 0, 0), (40, 2, 0), (80, 8, 1), (100, 10, 1))):
        channel = "Channel_A" if index % 2 == 0 else "Channel_B"
        for gender, suffix in (("Male", "M"), ("Female", "F")):
            rows.append({
                "candidate_id": f"MINI_{index}_{suffix}",
                "gender": gender,
                "has_valid_registration": True,
                "relevant_experience_years": exp,
                "clinical_assessment_score": level,
                "communication_assessment_score": level,
                "patient_care_assessment_score": level,
                "meets_required_shift_availability": True,
                "recruitment_channel": channel,
                "historical_hired": label,
            })
    return rows


# --------------------------------------------------------------------------- #
# mutation catalogue
# --------------------------------------------------------------------------- #
NAN = float("nan")
INF = float("inf")

CONTAINER_VALUES = (("None", None), ("str", "records"), ("dict", {}), ("tuple", ()))
ROW_VALUES = (("None", None), ("list", []), ("str", "row"))
ID_VALUES = (("empty", ""), ("blank", "   "), ("None", None), ("int", 123))
GENDER_VALUES = (("None", None), ("int", 123), ("Unknown", "Unknown"), ("male", "male"))
BOOL_VALUES = (("str", "True"), ("one", 1), ("zero", 0), ("None", None))
NUMERIC_TYPE_VALUES = (("None", None), ("str", "50"), ("True", True), ("False", False),
                       ("NaN", NAN), ("posinf", INF), ("neginf", -INF),
                       ("complex", 1 + 2j), ("list", []))
CHANNEL_VALUES = (("None", None), ("int", 123), ("Unknown", "Unknown"),
                  ("channel_a", "channel_a"))
TARGET_VALUES = (("None", None), ("str", "1"), ("True", True), ("False", False),
                 ("float", 1.0), ("neg", -1), ("two", 2))
STATE_VALUES = (("None", None), ("True", True), ("float", 42.0), ("str", "42"),
                ("neg", -1), ("big", 2 ** 32))
NUMERIC_BOUNDS = {"relevant_experience_years": (-0.1, 40.1),
                  "clinical_assessment_score": (-0.1, 100.1),
                  "communication_assessment_score": (-0.1, 100.1),
                  "patient_care_assessment_score": (-0.1, 100.1)}


def _field_mutations(fields) -> list[tuple[str, str, dict]]:
    """(scenario, label, {"set"/"delete": ...}) in the spec's field order."""
    out: list[tuple[str, str, dict]] = []
    for f in fields:
        out.append(("Missing field", f"delete {f}", {"delete": f}))
    return out


def _row_mutations(include_target: bool) -> list[tuple[str, str, dict]]:
    """All first-row mutations in spec order (training: with the target field
    list; prediction: without)."""
    fields = TRAIN_FIELDS if include_target else PRED_FIELDS
    out: list[tuple[str, str, dict]] = []
    for label, value in ROW_VALUES:
        out.append(("Non-dictionary row", f"row={label}", {"replace_row": value}))
    for f in fields:
        out.append(("Missing field", f"delete {f}", {"delete": f}))
    for label, value in ID_VALUES:
        out.append(("Invalid ID", f"candidate_id={label}", {"set": ("candidate_id", value)}))
    for label, value in GENDER_VALUES:
        out.append(("Invalid gender", f"gender={label}", {"set": ("gender", value)}))
    for field in ELIGIBILITY:
        for label, value in BOOL_VALUES:
            out.append(("Invalid Boolean", f"{field}={label}", {"set": (field, value)}))
    for field in NUMERIC:
        for label, value in NUMERIC_TYPE_VALUES:
            out.append(("Invalid numeric type/value", f"{field}={label}",
                        {"set": (field, value)}))
        low, high = NUMERIC_BOUNDS[field]
        out.append(("Below minimum", f"{field}={low}", {"set": (field, low)}))
        out.append(("Above maximum", f"{field}={high}", {"set": (field, high)}))
    for label, value in CHANNEL_VALUES:
        out.append(("Invalid channel", f"recruitment_channel={label}",
                    {"set": ("recruitment_channel", value)}))
    out.append(("Unknown key", "add unexpected_field=1",
                {"set": ("unexpected_field", 1)}))
    out.append(("Validate ineligible row", "registration=False and clinical='invalid'",
                {"multi": (("has_valid_registration", False),
                           ("clinical_assessment_score", "invalid"))}))
    return out


def _build_training_catalogue():
    cases = []
    n = 0

    def add(scenario, label, spec):
        nonlocal n
        n += 1
        cases.append({"id": f"RT{n:03d}", "scenario": scenario, "label": label, **spec})

    for label, value in CONTAINER_VALUES:
        add("Wrong container", f"records={label}", {"records": value})
    add("Empty training", "records=[]", {"records": []})
    for scenario, label, spec in _row_mutations(include_target=True):
        add(scenario, label, {"row_mutation": spec})
    for label, value in TARGET_VALUES:
        add("Invalid target", f"historical_hired={label}",
            {"row_mutation": {"set": ("historical_hired", value)}})
    add("Too few records", "train on only the first valid row", {"only_first": True})
    add("One-class target", "every historical_hired=0", {"all_labels": 0})
    add("One-class target", "every historical_hired=1", {"all_labels": 1})
    add("No eligible training", "registration=False on every row", {"all_ineligible": True})
    add("One class after filtering", "label-1 rows ineligible, only label 0 left",
        {"label1_ineligible": True})
    for label, value in STATE_VALUES:
        add("Invalid random_state", f"random_state={label}", {"random_state": value})
    return cases


def _build_prediction_catalogue():
    cases = []
    n = 0

    def add(scenario, label, spec):
        nonlocal n
        n += 1
        cases.append({"id": f"RP{n:03d}", "scenario": scenario, "label": label, **spec})

    for label, value in CONTAINER_VALUES:
        add("Wrong container", f"records={label}", {"records": value})
    for scenario, label, spec in _row_mutations(include_target=False):
        add(scenario, label, {"row_mutation": spec})
    add("Forbidden target", "add historical_hired=1",
        {"row_mutation": {"set": ("historical_hired", 1)}})
    add("Forbidden sidecar", "add reference_merit_score=75.0",
        {"row_mutation": {"set": ("reference_merit_score", 75.0)}})
    add("Atomic validation", "batch [valid BASE_B, invalid gender='Unknown']",
        {"atomic": True})
    return cases


RT_CASES = _build_training_catalogue()
RP_CASES = _build_prediction_catalogue()
RM_CASES = ("RM01", "RM02")

# The spec states these totals; a catalogue that disagrees is a bug here.
assert len(RT_CASES) == 102, len(RT_CASES)
assert len(RP_CASES) == 85, len(RP_CASES)
assert len(RT_CASES) + len(RP_CASES) + len(RM_CASES) == 189
_RT = {c["id"]: c for c in RT_CASES}
_RP = {c["id"]: c for c in RP_CASES}
# Spot checks against rows quoted in the spec table.
assert _RT["RT009"]["row_mutation"] == {"delete": "candidate_id"}
assert _RT["RT018"]["row_mutation"] == {"delete": "historical_hired"}
assert _RT["RT035"]["row_mutation"]["set"] == ("relevant_experience_years", None)
assert _RT["RT044"]["row_mutation"]["set"] == ("relevant_experience_years", -0.1)
assert _RT["RT045"]["row_mutation"]["set"] == ("relevant_experience_years", 40.1)
assert _RT["RT056"]["row_mutation"]["set"] == ("clinical_assessment_score", 100.1)
assert _RT["RT078"]["row_mutation"]["set"] == ("patient_care_assessment_score", 100.1)
assert _RT["RT083"]["row_mutation"]["set"] == ("unexpected_field", 1)
assert "multi" in _RT["RT084"]["row_mutation"]
assert _RT["RT085"]["row_mutation"]["set"] == ("historical_hired", None)
assert _RT["RT091"]["row_mutation"]["set"] == ("historical_hired", 2)
assert _RT["RT092"].get("only_first") and _RT["RT095"].get("all_ineligible")
assert _RT["RT102"]["random_state"] == 2 ** 32
assert _RP["RP008"]["row_mutation"] == {"delete": "candidate_id"}
assert _RP["RP016"]["row_mutation"] == {"delete": "recruitment_channel"}
assert _RP["RP033"]["row_mutation"]["set"] == ("relevant_experience_years", None)
assert _RP["RP043"]["row_mutation"]["set"] == ("relevant_experience_years", 40.1)
assert _RP["RP076"]["row_mutation"]["set"] == ("patient_care_assessment_score", 100.1)
assert _RP["RP081"]["row_mutation"]["set"] == ("unexpected_field", 1)
assert "multi" in _RP["RP082"]["row_mutation"]
assert _RP["RP083"]["row_mutation"]["set"] == ("historical_hired", 1)
assert _RP["RP084"]["row_mutation"]["set"][0] == "reference_merit_score"
assert _RP["RP085"].get("atomic")


def apply_row_mutation(row: dict, spec: dict):
    """Apply one catalogue mutation to a copy of a row. Returns the new row,
    or the replacement value for replace_row."""
    if "replace_row" in spec:
        return copy.deepcopy(spec["replace_row"])
    out = copy.deepcopy(row)
    if "delete" in spec:
        out.pop(spec["delete"], None)
    if "set" in spec:
        key, value = spec["set"]
        out[key] = value
    if "multi" in spec:
        for key, value in spec["multi"]:
            out[key] = value
    return out


def training_input_for(case: dict) -> tuple[list | object, int]:
    """(records, random_state) for one RT case, built from MINIMAL_TRAIN."""
    rows = minimal_train()
    random_state = 42
    if "records" in case:
        return copy.deepcopy(case["records"]), random_state
    if "random_state" in case:
        return rows, case["random_state"]
    if "row_mutation" in case:
        rows[0] = apply_row_mutation(rows[0], case["row_mutation"])
        return rows, random_state
    if case.get("only_first"):
        return rows[:1], random_state
    if "all_labels" in case:
        for r in rows:
            r["historical_hired"] = case["all_labels"]
        return rows, random_state
    if case.get("all_ineligible"):
        for r in rows:
            r["has_valid_registration"] = False
        return rows, random_state
    if case.get("label1_ineligible"):
        for r in rows:
            if r["historical_hired"] == 1:
                r["has_valid_registration"] = False
        return rows, random_state
    raise AssertionError(f"unhandled catalogue entry {case['id']}")


def prediction_input_for(case: dict):
    """The candidate_records argument for one RP case."""
    if "records" in case:
        return copy.deepcopy(case["records"])
    if case.get("atomic"):
        return [base_b(), base_b(candidate_id="BAD", gender="Unknown")]
    mutated = apply_row_mutation(base_b(), case["row_mutation"])
    return [mutated]
