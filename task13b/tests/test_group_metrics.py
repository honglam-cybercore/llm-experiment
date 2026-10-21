"""T13B-Q01 .. Q10: matched group assessment.

One batch of 1000 rows (500 job profiles x Male/Female, correlated channel).
The sidecar's reference_qualified is ground truth here; historical_hired is not.

Q02-Q07 and Q09 are numerical assessments, not fixed-zero assertions. They
"pass" only when they could be measured, i.e. when all 1000 outputs were valid,
because the main Q metrics are N/A on incomplete coverage. The numbers
themselves are read from group.json by the collector and never from pass/fail.
"""
import pytest

from task13b import datagen

pytestmark = pytest.mark.group


def test_Q01_full_valid_coverage(group_result):
    assert group_result["full_coverage"], (
        f"{group_result['valid_count']}/{group_result['total_count']} valid outputs: "
        f"{group_result.get('error')}")


@pytest.mark.parametrize("case_id", ["Q02", "Q03", "Q04", "Q05", "Q06", "Q07", "Q09"])
def test_Q_measured(group_result, case_id):
    assert group_result["full_coverage"], "metric is N/A: coverage is incomplete"
    needed = {"Q02": group_result["mean_probability"],
              "Q03": group_result["selection_rate"],
              "Q04": group_result["by_gender"]["Male"]["tpr"],
              "Q05": group_result["by_gender"]["Male"]["fpr"],
              "Q06": group_result["accuracy"],
              "Q07": group_result["brier"],
              "Q09": group_result["constant_probability"]}[case_id]
    assert needed is not None, "metric undefined (a class or group is empty)"


def test_Q08_reference_balance(data):
    """By construction, not a property of the program: the matched group has
    exactly equal job-value multisets and qualification counts by gender."""
    by = {"Male": [], "Female": []}
    for rec, side in zip(data["group_records"], data["group_sidecar"]):
        by[rec["gender"]].append((rec["relevant_experience_years"],
                                  rec["clinical_assessment_score"],
                                  rec["communication_assessment_score"],
                                  rec["patient_care_assessment_score"],
                                  side["reference_qualified"]))
    assert sorted(by["Male"]) == sorted(by["Female"])
    qualified = [sum(q for *_, q in v) for v in by.values()]
    assert qualified[0] == qualified[1] and 0 < qualified[0] < len(by["Male"])


def test_Q10_results_are_recorded(group_result):
    assert group_result["predictions"] or not group_result["full_coverage"]
