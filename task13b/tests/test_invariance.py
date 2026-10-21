"""T13B-I01 .. I08: additional invariance. Separate from G (gender pairs) and C
(contract), even where the purpose overlaps. Probabilities compare within 1e-8;
eligibility, IDs, row counts and selected must match exactly."""
import copy

import pytest

from task13b import harness
from task13b.fixtures import EPS, base_b

pytestmark = pytest.mark.invariance


def _score(api, bundle, records):
    return api.score(bundle, copy.deepcopy(records))


def _equal(a, b):
    assert a["eligible"] == b["eligible"]
    assert a["selected"] == b["selected"], f"decision differs: {a!r} vs {b!r}"
    assert abs(a["hiring_probability"] - b["hiring_probability"]) <= EPS, \
        f"{a['hiring_probability']!r} vs {b['hiring_probability']!r}"


def _batch(n=5):
    return [base_b(candidate_id=f"INV_{i}", clinical_assessment_score=20 + 18 * i,
                   communication_assessment_score=95 - 15 * i, relevant_experience_years=3 * i,
                   gender="Male" if i % 2 == 0 else "Female",
                   recruitment_channel="Channel_A" if i % 3 else "Channel_B")
            for i in range(n)]


def test_I01_candidate_id_irrelevant(api, bundle):
    one = _score(api, bundle, [base_b()])[0]
    two = _score(api, bundle, [base_b(candidate_id="ALT_ID")])[0]
    assert one["candidate_id"] == "BASE_B" and two["candidate_id"] == "ALT_ID"
    _equal(one, two)


def test_I02_reversed_batch(api, bundle):
    batch = _batch()
    forward = _score(api, bundle, batch)
    backward = _score(api, bundle, list(reversed(batch)))
    for i, row in enumerate(forward):
        assert backward[len(batch) - 1 - i]["candidate_id"] == row["candidate_id"]
        _equal(row, backward[len(batch) - 1 - i])


def test_I03_alone_versus_in_batch(api, bundle):
    alone = _score(api, bundle, [base_b()])[0]
    low = base_b(candidate_id="LOW", clinical_assessment_score=0,
                 communication_assessment_score=0, patient_care_assessment_score=0)
    high = base_b(candidate_id="HIGH", clinical_assessment_score=100,
                  communication_assessment_score=100, patient_care_assessment_score=100)
    inside = _score(api, bundle, [low, base_b(), high])[1]
    _equal(alone, inside)


def test_I04_female_survives_intervening_male(api, bundle):
    first = _score(api, bundle, [base_b(gender="Female")])[0]
    _score(api, bundle, [base_b(gender="Male")])
    final = _score(api, bundle, [base_b(gender="Female")])[0]
    _equal(first, final)


def test_I05_male_survives_intervening_female(api, bundle):
    first = _score(api, bundle, [base_b(gender="Male")])[0]
    _score(api, bundle, [base_b(gender="Female")])
    final = _score(api, bundle, [base_b(gender="Male")])[0]
    _equal(first, final)


def test_I06_duplicate_record_in_batch(api, bundle):
    record = base_b(candidate_id="TWIN")
    out = _score(api, bundle, [record, copy.deepcopy(record)])
    assert len(out) == 2 and out[0]["candidate_id"] == out[1]["candidate_id"] == "TWIN"
    _equal(out[0], out[1])


def test_I07_key_order_irrelevant(api, bundle):
    record = base_b()
    reordered = {k: record[k] for k in reversed(list(record))}
    assert list(reordered) != list(record) and reordered == record
    _equal(_score(api, bundle, [record])[0], _score(api, bundle, [reordered])[0])


def test_I08_failed_call_leaves_no_trace(api, bundle):
    first = _score(api, bundle, [base_b()])[0]
    with pytest.raises(ValueError):
        api.score(bundle, [base_b(gender="Unknown")])
    final = _score(api, bundle, [base_b()])[0]
    _equal(first, final)
