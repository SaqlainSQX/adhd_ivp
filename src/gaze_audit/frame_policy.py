"""Source-group cross-fitted signed-error stratification for the frame experiment."""

from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import RandomForestRegressor


@dataclass
class FrameRiskPolicy:
    model: RandomForestRegressor
    feature_columns: tuple[str, ...]
    cut_points: np.ndarray
    residual_sd: np.ndarray

    def scores(self, features):
        return self.model.predict(features[list(self.feature_columns)].to_numpy(float))

    def strata(self, features):
        return np.searchsorted(self.cut_points, self.scores(features), side="left")

    def contextual_surrogate(self, features):
        return np.clip(features.f_q.to_numpy(float) + self.scores(features), 0, 1)


def fit_frame_policy(features, labels, folds, *, seed=42):
    """Historical train references only; validation/test never enter this function."""
    columns = tuple(column for column in features if column.startswith("f_"))
    x = features[list(columns)].to_numpy(float)
    labels, folds = np.asarray(labels), np.asarray(folds)
    if (
        x.ndim != 2
        or len(x) < 2
        or not columns
        or not np.isfinite(x).all()
        or labels.shape != (len(x),)
        or not np.isin(labels, [0, 1]).all()
        or folds.shape != (len(x),)
        or set(folds) != set(range(5))
    ):
        raise ValueError("Require finite features, binary labels and all five frozen source folds")
    source_folds = {}
    for source, fold in zip(features.source_id, folds, strict=True):
        if source in source_folds and source_folds[source] != fold:
            raise ValueError("An original source crosses training folds")
        source_folds[source] = fold
    residual = labels.astype(float) - features.f_q.to_numpy(float)

    def fresh():
        return RandomForestRegressor(
            n_estimators=64, max_depth=4, min_samples_leaf=100, random_state=seed, n_jobs=1
        )

    oof = np.empty(len(x), dtype=float)
    fold_summary = []
    for fold in range(5):
        held = folds == fold
        model = fresh().fit(x[~held], residual[~held])
        oof[held] = model.predict(x[held])
        fold_summary.append(
            {"fold": fold, "training_rows": int((~held).sum()), "held_rows": int(held.sum())}
        )
    cuts = np.unique(np.quantile(oof, [0.25, 0.5, 0.75]))
    cuts = cuts[cuts < oof.max()]  # Remove a trailing cut that would create an empty bin.
    groups = np.searchsorted(cuts, oof, side="left")
    global_variance = float(np.var(residual, ddof=1))
    sd, strata_summary = [], []
    for h in range(len(cuts) + 1):
        values = residual[groups == h]
        count = len(values)
        within = float(np.var(values, ddof=1)) if count > 1 else 0.0
        shrunk = (max(count - 1, 0) * within + 20 * global_variance) / (max(count - 1, 0) + 20)
        sd.append(max(float(np.sqrt(shrunk)), 1e-6))
        strata_summary.append(
            {
                "stratum": h,
                "oof_rows": count,
                "centered_residual_variance": within,
                "shrunk_sd": sd[-1],
            }
        )
    policy = FrameRiskPolicy(fresh().fit(x, residual), columns, cuts, np.asarray(sd))
    return (
        policy,
        {
            "target": "signed residual y-q",
            "folds": fold_summary,
            "cut_points": cuts.tolist(),
            "strata": strata_summary,
            "global_centered_residual_variance": global_variance,
        },
        oof,
    )
