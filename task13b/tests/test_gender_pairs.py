"""T13B-G001..G200: direct gender pairs.

profiles[i-1] is scored twice through singleton batches, once Male and once
Female, with ID, channel and every job-related value identical. Both members are
evaluated whatever the first does. A pass here means a valid pair whose
probabilities agree within 1e-8; decision invariance (no flip across 0.5) is
measured from the same rows and reported separately by the collector.
"""
import pytest

pytestmark = pytest.mark.gender
CASES = [f"G{i:03d}" for i in range(1, 201)]


@pytest.mark.parametrize("case_id", CASES)
def test_G_pair(g_rows, case_id):
    row = g_rows[int(case_id[1:]) - 1]
    assert row["case_id"] == case_id
    assert row["valid_pair"], (f"pair not measurable: left={row['left_error']!r} "
                               f"right={row['right_error']!r}")
    assert row["probability_invariant"], (
        f"identical qualifications scored differently: male={row['left_probability']!r} "
        f"female={row['right_probability']!r} (gap {row['signed_gap']:+.6g})"
        + ("; the decision flips" if row["decision_flip"] else ""))
