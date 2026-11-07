import numpy as np
import pandas as pd
import pytest

from gaze_audit.frames import FrameOracle, FrameStratum, estimate_frames
from gaze_audit.strengthening import (
    Z95,
    calibration_multiplier,
    fit_feature_policy,
    replay_rng,
    sampled_components,
    satterthwaite_df,
    verify_estimates,
)


def test_feature_quartiles_preserve_ties_and_reproduce_centered_moments():
    table = pd.DataFrame({"f_q": [0.1, 0.1, 0.1, 0.1, 0.8, 0.8, 0.8, 0.8]})
    policy = fit_feature_policy(table, [0, 0, 0, 1, 0, 1, 1, 1], "f_q")
    assert len(policy.cut_points) == 2  # quantiles at 0.1 and 0.45; trailing 0.8 removed
    assert len(np.unique(policy.strata(table.iloc[:4]))) == 1
    assert len(np.unique(policy.strata(table.iloc[4:]))) == 1
    assert np.isfinite(policy.residual_sd).all()
    assert (policy.residual_sd > 0).all()
    before = policy.as_dict()
    policy.strata(pd.DataFrame({"f_q": [-100, 100]}))
    assert policy.as_dict() == before  # applying shifted target data cannot change the cuts


def test_welch_degrees_of_freedom_handles_single_component_and_census_zero():
    actual = satterthwaite_df([[2.0, 0.0], [1.0, 1.0]], [21, 11])
    assert actual[0] == pytest.approx(20)
    assert actual[1] == pytest.approx(4 / (1 / 20 + 1 / 10))
    assert np.isinf(satterthwaite_df([[0.0, 0.0]], [2, 2])[0])


def test_development_calibration_rank_floor_and_unbounded_cases():
    result = calibration_multiplier(np.arange(1000, dtype=float), np.ones(1000), 0)
    assert result["rank_one_based"] == 951
    assert result["multiplier"] == 950
    assert calibration_multiplier(np.zeros(10), np.zeros(10), 0)["multiplier"] == Z95
    missing = calibration_multiplier(np.ones(10), np.zeros(10), 0)
    assert missing["multiplier"] is None and missing["zero_se_nonzero_error_draws"] == 10


def test_independent_components_match_oracle_estimator_and_census():
    ids = tuple("abcdef")
    q = np.array([0.1, 0.2, 0.3, 0.8, 0.4, 0.7])
    y = np.array([0, 1, 0, 1, 0, 1])
    populations, counts = [(0, 1, 2, 3), (4, 5)], np.array([2, 2])
    samples = np.array([[0, 2, 4, 5], [1, 3, 4, 5]])
    oracle = FrameOracle(dict(zip(ids, y, strict=True)), ids)
    rows = []
    for sample in samples:
        plan = (
            FrameStratum(populations[0], tuple(sample[:2])),
            FrameStratum(populations[1], tuple(sample[2:])),
        )
        rows.append(
            estimate_frames(ids, q, plan, oracle.query(tuple(ids[i] for i in sample))).as_dict()
        )
    point, components, strata, _ = sampled_components(samples, populations, counts, q, y)
    assert verify_estimates(pd.DataFrame(rows), point, components)["status"] == "passed"
    assert np.all(components[:, 1] == 0) and strata[1]["census"]
    damaged = pd.DataFrame(rows)
    damaged.loc[0, "prevalence"] += 0.01
    with pytest.raises(ValueError, match="recomputation"):
        verify_estimates(damaged, point, components)


def test_registered_rng_replay_rejects_modified_saved_queries():
    populations, counts = [(0, 1, 2, 3), (4, 5, 6)], [2, 2]
    samples = []
    for draw in range(3):
        rng = np.random.default_rng(np.random.SeedSequence([200000 + draw, 1, 7]))
        samples.append(
            np.r_[
                rng.choice(populations[0], 2, replace=False),
                rng.choice(populations[1], 2, replace=False),
            ]
        )
    samples = np.asarray(samples)
    replay_rng(samples, populations, counts, 200000, 1, 7)
    samples[0, 0] = samples[0, 1]
    with pytest.raises(ValueError, match="budget or duplicate"):
        replay_rng(samples, populations, counts, 200000, 1, 7)
