import numpy as np
import pandas as pd
import pytest

from gaze_audit.frame_policy import fit_frame_policy


def test_policy_learns_signed_residual_and_constant_scores_collapse():
    features = pd.DataFrame(
        {
            "source_id": np.repeat(["a", "b", "c", "d", "e"], 40),
            "f_q": np.full(200, 0.9),
            "f_geometry": np.ones(200),
        }
    )
    labels = np.zeros(200)
    folds = np.repeat(np.arange(5), 40)
    policy, report, oof = fit_frame_policy(features, labels, folds)
    assert np.all(oof < -0.89)  # Squared error, used by the old scaffold, would be positive.
    assert policy.scores(features) == pytest.approx(np.full(200, -0.9))
    assert len(policy.cut_points) == 0
    assert len(policy.residual_sd) == 1
    assert report["target"] == "signed residual y-q"
    assert np.all(policy.strata(features) == 0)
    assert np.allclose(policy.contextual_surrogate(features), 0)
    with pytest.raises(ValueError, match="five"):
        fit_frame_policy(features, labels, np.zeros(200))
