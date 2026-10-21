"""T13B-RT001..RT102 (training), RP001..RP085 (prediction), RM01..RM02.

189 cases, each its own test id. Every one requires ValueError: never a normal
result, a silent coercion, a raw TypeError, or a partial output. The catalogue
lives in task13b/fixtures.py and is asserted against the spec's totals at
import time.
"""
import copy

import pytest

from task13b import fixtures

pytestmark = pytest.mark.robustness


@pytest.mark.parametrize("case", fixtures.RT_CASES, ids=[c["id"] for c in fixtures.RT_CASES])
def test_RT_training(api, expect_value_error, case):
    records, random_state = fixtures.training_input_for(case)
    expect_value_error(lambda: api.train(records, random_state),
                       note=f" for {case['id']} ({case['scenario']}: {case['label']})")


@pytest.mark.parametrize("case", fixtures.RP_CASES, ids=[c["id"] for c in fixtures.RP_CASES])
def test_RP_prediction(api, minimal_bundle, expect_value_error, case):
    records = fixtures.prediction_input_for(case)
    expect_value_error(lambda: api.score(minimal_bundle, records),
                       note=f" for {case['id']} ({case['scenario']}: {case['label']})")


def test_RM01_none_bundle(api, expect_value_error):
    expect_value_error(lambda: api.score(None, [fixtures.base_b()]))


def test_RM02_unfitted_estimator(api, expect_value_error):
    from sklearn.linear_model import LogisticRegression
    expect_value_error(lambda: api.score(LogisticRegression(), [fixtures.base_b()]))
