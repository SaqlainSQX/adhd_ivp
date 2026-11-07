import pandas as pd
import pytest

from gaze_audit.followups import DROP_ORDERED, bootstrap_ratio, choose_alpha, summary_only


def test_validation_tie_prefers_smaller_alpha_within_one_percent():
    rows = [
        {"alpha": 0.0, "validation_mse": 1.005},
        {"alpha": 0.5, "validation_mse": 1.0},
        {"alpha": 1.0, "validation_mse": 1.02},
    ]
    assert choose_alpha(rows)["alpha"] == 0
    rows[0]["validation_mse"] = 1.02
    assert choose_alpha(rows)["alpha"] == 0.5
    with pytest.raises(ValueError, match="three"):
        choose_alpha(rows[:2])


def test_summary_ablation_drops_exactly_registered_columns_and_preserves_input():
    original = pd.DataFrame(
        {
            "record_id": ["a"],
            "f_q": [0.2],
            "f_t_q_mean": [0.3],
            **dict.fromkeys(DROP_ORDERED, [0.1]),
        }
    )
    reduced = summary_only(original)
    assert set(original) - set(reduced) == set(DROP_ORDERED)
    assert reduced.f_q.iloc[0] == 0.2 and reduced.f_t_q_mean.iloc[0] == 0.3
    assert set(DROP_ORDERED) <= set(original)
    with pytest.raises(ValueError, match="eight"):
        summary_only(reduced)


def test_paired_bootstrap_ratio_reproduces_identical_method_and_fixed_scaling():
    assert bootstrap_ratio([1.0, -2.0, 3.0], [1.0, -2.0, 3.0])["rmse_ratio"] == 1
    scaled = bootstrap_ratio([2.0, -4.0, 6.0], [1.0, -2.0, 3.0])
    assert scaled["rmse_ratio"] == 2
    assert scaled["paired_draw_bootstrap_95pct"] == pytest.approx([2, 2])
