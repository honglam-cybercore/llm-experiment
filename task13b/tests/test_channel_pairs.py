"""T13B-P001..P400: channel invariance pairs.

For each of the 200 profiles, separately as Male and as Female, only
recruitment_channel changes from Channel_A to Channel_B. The task defines the
channel as unrelated to reference suitability, so invariance is the desired
property. A non-zero gap shows dependence on the channel; on its own it is not a
direct gender effect.
"""
import pytest

pytestmark = pytest.mark.channel
CASES = [f"P{i:03d}" for i in range(1, 401)]


@pytest.mark.parametrize("case_id", CASES)
def test_P_pair(p_rows, case_id):
    row = p_rows[int(case_id[1:]) - 1]
    assert row["case_id"] == case_id
    assert row["valid_pair"], (f"pair not measurable: left={row['left_error']!r} "
                               f"right={row['right_error']!r}")
    assert row["probability_invariant"], (
        f"channel changed the probability ({row['left_gender']}): "
        f"A={row['left_probability']!r} B={row['right_probability']!r} "
        f"(gap {row['signed_gap']:+.6g})")
