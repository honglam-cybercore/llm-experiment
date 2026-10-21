"""T13B-J001..J200: combined sensitivity pairs.

Male+Channel_A against Female+Channel_B with everything else identical. These
are diagnostics: the difference cannot be attributed to gender alone, so they are
kept out of the direct gender pass rate. A pass here means only that the pair was
measurable; the gaps and flips live in the stored rows. The channel combination
is fixed in advance and never chosen to maximise an observed gap.
"""
import pytest

pytestmark = pytest.mark.combined
CASES = [f"J{i:03d}" for i in range(1, 201)]


@pytest.mark.parametrize("case_id", CASES)
def test_J_pair(j_rows, case_id):
    row = j_rows[int(case_id[1:]) - 1]
    assert row["case_id"] == case_id
    assert row["valid_pair"], (f"pair not measurable: left={row['left_error']!r} "
                               f"right={row['right_error']!r}")
