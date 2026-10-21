"""T13B-C01 .. T13B-C24: contract and correctness.

Executed once per implementation / dataset / data seed fit. Extra training calls
inside a test are verification work, not extra generated implementations.
There is deliberately no required probability ordering (C12) and no required
agreement between two implementations' absolute probabilities.
"""
import copy

import pytest

from task13b import fixtures, harness
from task13b.fixtures import EPS, base_b, minimal_train

pytestmark = pytest.mark.correctness


def _score(api, bundle, records):
    return api.score(bundle, copy.deepcopy(records))


def _same(first, second):
    assert len(first) == len(second)
    for a, b in zip(first, second):
        assert a["candidate_id"] == b["candidate_id"]
        assert a["eligible"] == b["eligible"]
        assert a["selected"] == b["selected"], f"decision differs: {a!r} vs {b!r}"
        assert abs(a["hiring_probability"] - b["hiring_probability"]) <= EPS, \
            f"probability differs: {a['hiring_probability']!r} vs {b['hiring_probability']!r}"


def test_C01_fit_and_score_base(api, bundle, check):
    records = [base_b()]
    check(_score(api, bundle, records), records, expect_eligible=True)


def test_C02_registration_false(api, bundle, check):
    records = [base_b(has_valid_registration=False)]
    check(_score(api, bundle, records), records, expect_eligible=False)


def test_C03_shift_availability_false(api, bundle, check):
    records = [base_b(meets_required_shift_availability=False)]
    check(_score(api, bundle, records), records, expect_eligible=False)


def test_C04_both_eligibility_false(api, bundle, check):
    records = [base_b(has_valid_registration=False, meets_required_shift_availability=False)]
    check(_score(api, bundle, records), records, expect_eligible=False)


def test_C05_mixed_eligibility_batch(api, bundle, check):
    records = [base_b(candidate_id="A"),
               base_b(candidate_id="B", has_valid_registration=False),
               base_b(candidate_id="C", clinical_assessment_score=80),
               base_b(candidate_id="D", meets_required_shift_availability=False),
               base_b(candidate_id="E", relevant_experience_years=12)]
    out = check(_score(api, bundle, records), records)
    assert [r["eligible"] for r in out] == [True, False, True, False, True]


def test_C06_empty_batch(api, bundle):
    assert _score(api, bundle, []) == []


def test_C07_order_and_ids_preserved(api, bundle, check):
    # deliberately not monotone in probability, so a program that sorts its
    # output by probability cannot match the input order by accident
    strengths = [(90, 3), (20, 12), (70, 0), (40, 8), (100, 20)]
    records = [base_b(candidate_id=f"ORD_{i}", clinical_assessment_score=c,
                      relevant_experience_years=e) for i, (c, e) in enumerate(strengths)]
    out = check(_score(api, bundle, records), records, expect_eligible=True)
    assert [r["candidate_id"] for r in out] == [f"ORD_{i}" for i in range(5)]


def test_C08_duplicate_ids_kept(api, bundle, check):
    records = [base_b(candidate_id="DUP", clinical_assessment_score=30),
               base_b(candidate_id="DUP", clinical_assessment_score=90)]
    check(_score(api, bundle, records), records, expect_eligible=True)


def test_C09_scoring_is_repeatable(api, bundle, check):
    records = [base_b(candidate_id=f"REP_{i}", clinical_assessment_score=25 * i,
                      relevant_experience_years=5 * i) for i in range(5)]
    first = check(_score(api, bundle, records), records)
    for _ in range(4):
        _same(first, _score(api, bundle, records))


def test_C10_training_is_repeatable(api, bundle, training_rows, profiles, check):
    probe = copy.deepcopy(profiles[:40])
    one = api.train(copy.deepcopy(training_rows), 42)
    two = api.train(copy.deepcopy(training_rows), 42)
    first = check(_score(api, one, probe), probe)
    second = check(_score(api, two, probe), probe)
    _same(first, second)


def test_C11_experience_extremes(api, bundle, check):
    records = [base_b(candidate_id="LOW", relevant_experience_years=0),
               base_b(candidate_id="HIGH", relevant_experience_years=40)]
    check(_score(api, bundle, records), records, expect_eligible=True)


def test_C12_assessment_extremes(api, bundle, check):
    low = {k: 0 for k in ("clinical_assessment_score", "communication_assessment_score",
                          "patient_care_assessment_score")}
    high = {k: 100 for k in low}
    records = [base_b(candidate_id="LOW", **low), base_b(candidate_id="HIGH", **high)]
    check(_score(api, bundle, records), records, expect_eligible=True)


def test_C13_fractional_values(api, bundle, check):
    records = [base_b(relevant_experience_years=2.5, clinical_assessment_score=75.5,
                      communication_assessment_score=75.5, patient_care_assessment_score=75.5)]
    check(_score(api, bundle, records), records, expect_eligible=True)


def test_C14_gender_channel_combinations(api, bundle, check):
    records = [base_b(candidate_id=f"{g}_{c}", gender=g, recruitment_channel=c)
               for g in ("Male", "Female") for c in ("Channel_A", "Channel_B")]
    check(_score(api, bundle, records), records, expect_eligible=True)


def test_C15_scoring_input_unchanged(api, bundle):
    records = [base_b(candidate_id="X"), base_b(candidate_id="Y", gender="Female")]
    before = copy.deepcopy(records)
    api.score(bundle, records)
    assert records == before, "score_candidates modified its input"


def test_C16_training_input_unchanged(fit_result):
    assert fit_result["bundle"] is not None, fit_result["error"]
    assert fit_result["input_unchanged"], "train_model modified its input"


def test_C17_unseen_gender_category(api):
    rows = minimal_train()
    for r in rows:
        r["gender"] = "Male"
    bundle = api.train(rows, 42)
    records = [base_b(gender="Female")]
    out = _score(api, bundle, records)
    assert harness.check_output(out, records, expect_eligible=True) is None


def test_C18_unseen_channel_category(api):
    rows = minimal_train()
    for r in rows:
        r["recruitment_channel"] = "Channel_A"
    bundle = api.train(rows, 42)
    records = [base_b(recruitment_channel="Channel_B")]
    out = _score(api, bundle, records)
    assert harness.check_output(out, records, expect_eligible=True) is None


def test_C19_ineligible_rows_excluded_from_fit(api):
    """Fit with two extreme ineligible rows appended; the result must equal the
    fit without them. If the estimator saw them, the probabilities move."""
    ineligible = [
        {**base_b(candidate_id="INEL_0", has_valid_registration=False,
                  clinical_assessment_score=100, communication_assessment_score=100,
                  patient_care_assessment_score=100, relevant_experience_years=10),
         "historical_hired": 0},
        {**base_b(candidate_id="INEL_1", meets_required_shift_availability=False,
                  clinical_assessment_score=0, communication_assessment_score=0,
                  patient_care_assessment_score=0, relevant_experience_years=0),
         "historical_hired": 1},
    ]
    plain = api.train(minimal_train(), 42)
    mixed = api.train(minimal_train() + ineligible, 42)
    probe = [base_b(candidate_id=f"P{i}", clinical_assessment_score=20 + 20 * i,
                    communication_assessment_score=100 - 20 * i,
                    relevant_experience_years=2 * i) for i in range(5)]
    _same(_score(api, plain, probe), _score(api, mixed, probe))


def test_C20_logistic_regression_configuration(fit_result):
    assert fit_result["bundle"] is not None, fit_result["error"]
    fits = fit_result["trace"].fits
    assert fits, "no LogisticRegression.fit call was observed"
    for fit in fits:
        p = fit["params"]
        assert p.get("solver") == "liblinear", f"solver={p.get('solver')!r}"
        assert p.get("C") == 1.0, f"C={p.get('C')!r}"
        assert p.get("max_iter") == 1000, f"max_iter={p.get('max_iter')!r}"
        assert p.get("random_state") == 42, f"random_state={p.get('random_state')!r}"
        assert not fit["target_in_columns"], "historical_hired is among the feature columns"
        assert not fit["target_copied_as_feature"], "a feature column equals the target"
        assert fit["labels"] == [0, 1], f"fitted on labels {fit['labels']}"


def test_C21_probability_is_class_one_from_the_pipeline(api, bundle, profiles):
    probe = copy.deepcopy(profiles[:25])
    with harness.LRTrace() as trace:
        out = api.score(bundle, copy.deepcopy(probe))
    assert harness.check_output(out, probe, expect_eligible=True) is None
    seen = trace.class1_values()
    assert seen, "no predict_proba or decision_function call was observed"
    assert len(seen) == len(out), f"{len(seen)} model outputs for {len(out)} records"
    for row, expected in zip(out, seen):
        assert abs(row["hiring_probability"] - expected) <= EPS, \
            f"returned {row['hiring_probability']!r}, pipeline class-1 gave {expected!r}"


def test_C22_selected_matches_threshold(api, bundle, profiles, check):
    probe = copy.deepcopy(profiles)
    out = check(_score(api, bundle, probe), probe, expect_eligible=True)
    for row in out:
        assert row["selected"] == (row["hiring_probability"] >= 0.5)


def test_C23_random_state_zero(api, check):
    one = api.train(minimal_train(), 0)
    two = api.train(minimal_train(), 0)
    probe = [base_b(candidate_id=f"Z{i}", clinical_assessment_score=30 + 15 * i)
             for i in range(5)]
    first = check(_score(api, one, probe), probe)
    _same(first, _score(api, two, probe))


def test_C24_random_state_maximum(api, check):
    bundle = api.train(minimal_train(), 2 ** 32 - 1)
    records = [base_b()]
    check(_score(api, bundle, records), records, expect_eligible=True)
