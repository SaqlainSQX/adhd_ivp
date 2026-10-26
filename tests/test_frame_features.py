import numpy as np
import pandas as pd
import pytest

from gaze_audit.frame_features import build_temporal


def test_temporal_context_does_not_cross_gaps_clips_or_pairs():
    rows = []
    for clip, person, positions, values in [
        ("c1", 2, [1, 2, 4, 5], [0.1, 0.2, 0.8, 0.9]),
        ("c1", 3, [1], [0.3]),
        ("c2", 2, [1], [0.4]),
    ]:
        for position, q in zip(positions, values, strict=True):
            rows.append(
                {
                    "record_id": f"{clip}-{person}-{position}",
                    "clip_id": clip,
                    "person_a": 1,
                    "person_b": person,
                    "clip_frame_index_1based": position,
                    "f_q": q,
                    "f_direction_signed_difference": 0,
                    "f_head_a_area": 0.1,
                    "f_head_b_area": 0.2,
                    "f_pair_center_distance": 0.5,
                }
            )
    actual = build_temporal(pd.DataFrame(rows).sample(frac=1, random_state=42), 5).set_index(
        "record_id"
    )
    assert actual.loc["c1-2-1", "f_t_q_mean"] == pytest.approx(0.15)
    assert actual.loc["c1-2-4", "f_t_q_mean"] == pytest.approx(0.85)
    assert actual.loc["c1-2-4", "f_t_previous_context_missing"] == 1
    assert actual.loc["c1-2-1", "f_t_q_adjacent_change_mean"] == pytest.approx(0.1)
    assert actual.loc["c1-3-1", "f_t_available_context_count"] == 1
    assert actual.loc["c1-3-1", "f_t_q_adjacent_change_mean"] == 0
    assert actual.loc["c2-2-1", "f_t_q_mean"] == 0.4
    assert np.isfinite(actual.filter(regex="^f_").to_numpy()).all()
    with pytest.raises(ValueError, match="Reference"):
        build_temporal(pd.DataFrame(rows).assign(label=0), 5)
