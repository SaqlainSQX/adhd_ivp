from itertools import combinations

import numpy as np
import pandas as pd

from gaze_audit.block_pilot import estimate_block_sample, partition


def test_partition_breaks_gaps_pairs_and_keeps_every_frame():
    table = pd.DataFrame(
        dict(
            record_id=list("abcdef"),
            source_id=["s"] * 6,
            clip_id=["c"] * 6,
            person_a=[0, 0, 0, 0, 0, 0],
            person_b=[1, 1, 1, 1, 2, 2],
            clip_frame_index_1based=[1, 2, 4, 5, 1, 2],
        )
    )
    mapping, costs, _ = partition(table, 5)
    assert costs.tolist() == [2, 2, 2] and mapping.tolist() == [0, 0, 1, 1, 2, 2]
    one, ones, _ = partition(table, 1)
    assert one.tolist() == list(range(6)) and ones.sum() == 6


def test_random_count_unequal_cost_block_estimator_is_unbiased():
    costs = np.array([1, 2, 4, 3])
    q = np.array([0.1, 0.7, 1.1, 0.5])
    y = np.array([0, 1, 2, 0])
    residual = y - q
    target = 2.3
    mean, second, mean_var = 0.0, 0.0, 0.0
    expected_cost = 0.0
    for n, prob in [(2, 0.7), (3, 0.3)]:
        choices = list(combinations(range(4), n))
        for selected in choices:
            point, var = estimate_block_sample(q.sum(), residual, list(selected), costs.sum())
            mass = prob / len(choices)
            mean += mass * point
            second += mass * point**2
            mean_var += mass * var
            expected_cost += mass * costs[list(selected)].sum()
    assert np.isclose(mean, y.sum() / costs.sum(), atol=1e-14)
    assert np.isclose(second - mean**2, mean_var, atol=1e-14)
    assert np.isclose(expected_cost, target * costs.mean(), atol=1e-14)
