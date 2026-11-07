import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from gaze_audit.extra_experiments import fit_extra_policy, nested_source_subset


def test_training_subsets_are_source_nested_and_stable_under_public_row_shuffle():
    table = pd.DataFrame(
        {"source_id": ["A"] * 20 + ["B"] * 35, "record_id": [f"id{i:03d}" for i in range(55)]}
    )
    previous = set()
    for fraction, expected_count in [(0.01, 2), (0.05, 3), (0.2, 11), (1.0, 55)]:
        positions, counts = nested_source_subset(table, fraction)
        chosen = set(table.iloc[positions].record_id)
        shuffled = table.sample(frac=1, random_state=41).reset_index(drop=True)
        changed_positions, _ = nested_source_subset(shuffled, fraction)
        assert chosen == set(shuffled.iloc[changed_positions].record_id)
        assert previous <= chosen and len(chosen) == expected_count
        assert sum(row["selected_labels"] for row in counts) == expected_count
        previous = chosen


def test_ridge_oof_scaling_and_fit_exclude_the_held_source():
    folds = np.repeat(np.arange(5), 12)
    table = pd.DataFrame(
        {
            "source_id": [f"source{f}" for f in folds],
            "f_q": np.linspace(0.01, 0.99, len(folds)),
            "f_geometry": folds * 8 + np.tile(np.arange(12), 5),
        }
    )
    y = np.tile([0, 1, 0], 20)
    policy, diagnostic, oof = fit_extra_policy(table, y, folds, "ridge")
    columns = list(policy.feature_columns)
    held = folds == 0
    expected = make_pipeline(
        StandardScaler(), Ridge(alpha=1.0, fit_intercept=True, solver="cholesky")
    )
    expected.fit(
        table.loc[~held, columns].to_numpy(), y[~held] - table.loc[~held, "f_q"].to_numpy()
    )
    assert np.allclose(oof[held], expected.predict(table.loc[held, columns].to_numpy()))
    assert np.allclose(policy.model["standardscaler"].mean_, table[columns].mean().to_numpy())
    assert diagnostic["scaling_inside_each_training_fold"]
    assert len(diagnostic["folds"]) == 5


def test_squared_score_retains_centered_signed_residual_allocation_moments():
    folds = np.repeat(np.arange(5), 240)
    table = pd.DataFrame(
        {"source_id": [f"source{f}" for f in folds], "f_q": np.full(len(folds), 0.2)}
    )
    y = np.tile([0, 1], len(folds) // 2)
    policy, diagnostic, oof = fit_extra_policy(table, y, folds, "squared-rf")
    assert np.all(oof >= 0) and np.allclose(oof, 0.34, atol=0.02)
    assert np.all((policy.residual_sd > 0.49) & (policy.residual_sd < 0.51))
    assert diagnostic["allocation_moments_use_centered_signed_residuals"]
    assert policy.target == "squared residual (y-q)^2"


def test_cross_source_fold_leakage_and_unregistered_learner_are_rejected():
    folds = np.tile(np.arange(5), 4)
    table = pd.DataFrame({"source_id": ["same-source"] * 20, "f_q": np.linspace(0, 1, 20)})
    with pytest.raises(ValueError, match="crosses"):
        fit_extra_policy(table, np.tile([0, 1], 10), folds, "ridge")
    with pytest.raises(ValueError, match="fraction"):
        nested_source_subset(table.assign(record_id=[str(i) for i in range(20)]), 0)
