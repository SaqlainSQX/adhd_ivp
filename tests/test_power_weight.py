"""Finite-population identity checks for the power-weight extension."""

from itertools import combinations, product

import numpy as np

from gaze_audit.frames import FrameStratum, estimate_frames
from gaze_audit.timed_research import choose


def test_fixed_power_weights_are_design_unbiased_with_fpc_variance():
    ids = tuple("abcdef")
    q = np.array([0.05, 0.2, 0.8, 0.1, 0.7, 0.9])
    y = dict(zip(ids, [0, 0, 1, 1, 0, 1], strict=True))
    populations = [(0, 1, 2), (3, 4, 5)]
    for weight in [0, 0.25, 0.5, 0.75, 1]:
        results = []
        for selections in product(*(list(combinations(p, 2)) for p in populations)):
            plan = tuple(
                FrameStratum(tuple(p), tuple(s))
                for p, s in zip(populations, selections, strict=True)
            )
            queried = {ids[i]: y[ids[i]] for s in selections for i in s}
            results.append(estimate_frames(ids, q * weight, plan, queried))
        points = np.array([r.prevalence for r in results])
        assert np.isclose(points.mean(), 0.5, atol=1e-14)
        assert np.isclose(points.var(), np.mean([r.variance for r in results]), atol=1e-14)


def test_weight_tie_keeps_original_correction_and_rejects_clear_loss():
    candidates = [dict(weight=0, validation_mse=1.0), dict(weight=1, validation_mse=1.005)]
    assert choose(candidates, "weight", True)["weight"] == 1
    candidates[1]["validation_mse"] = 1.1
    assert choose(candidates, "weight", True)["weight"] == 0
