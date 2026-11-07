"""E01/E02: descriptive development diagnostics and uniform M1/M2 validation checks."""

import argparse
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from gaze_audit.frame_study import (
    load_feature_population,
    read_references,
    reconstruct_plan,
    save_queries,
    summarize_draws,
)
from gaze_audit.frames import FrameOracle, estimate_frames, hypergeometric_interval, integer_budget


def diagnostics(table, labels):
    y = np.array([labels[key] for key in table.record_id], dtype=float)
    q = table.f_q.to_numpy(float)
    residual = y - q
    variance_y = float(np.var(y, ddof=1))
    variance_e = float(np.var(residual, ddof=1))
    report = {
        "eligible_anchors": len(table),
        "sources": table.source_id.nunique(),
        "mean_y": float(y.mean()),
        "mean_q": float(q.mean()),
        "model_prevalence_bias_pp": float((q.mean() - y.mean()) * 100),
        "variance_y": variance_y,
        "variance_residual": variance_e,
        "variance_ratio_residual_over_human": variance_e / variance_y if variance_y else None,
        "covariance_y_q": float(np.cov(y, q, ddof=1)[0, 1]),
        "calibration_bins": [],
        "residual_lag_covariances": [],
    }
    bins = np.minimum((q * 10).astype(int), 9)
    for bucket in range(10):
        mask = bins == bucket
        if mask.any():
            report["calibration_bins"].append(
                {
                    "bin": bucket,
                    "rows": int(mask.sum()),
                    "mean_q": float(q[mask].mean()),
                    "mean_y": float(y[mask].mean()),
                    "positive_references": int(y[mask].sum()),
                }
            )
    augmented = table.assign(residual=residual)
    products, counts = np.zeros(10), np.zeros(10, dtype=int)
    center = residual.mean()
    for _, group in augmented.groupby(["clip_id", "person_a", "person_b"]):
        group = group.sort_values("clip_frame_index_1based")
        index = group.clip_frame_index_1based.to_numpy()
        values = group.residual.to_numpy() - center
        for lag in range(1, 11):
            positions = np.searchsorted(index, index + lag)
            left = np.flatnonzero(positions < len(index))
            left = left[index[positions[left]] == index[left] + lag]
            products[lag - 1] += (values[left] * values[positions[left]]).sum()
            counts[lag - 1] += len(left)
    for lag in range(1, 11):
        report["residual_lag_covariances"].append(
            {
                "lag": lag,
                "known_endpoint_pairs": int(counts[lag - 1]),
                "centered_covariance": float(products[lag - 1] / counts[lag - 1])
                if counts[lag - 1]
                else None,
            }
        )
    report["lag_scope"] = (
        "known endpoints at exact mapped lag, within clip and pair; descriptive only"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--processed", type=Path, default=Path("data/processed/vsgaze-17357752-v1"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--draws", type=int, default=100)
    args = parser.parse_args()
    if args.output.exists() or args.draws < 1:
        parser.error("Choose a new output directory and positive draw count")
    tables, hashes = load_feature_population(args.features)
    static = tables["static"]
    validation = static[static.split == "validation"].reset_index(drop=True)
    ids = tuple(validation.record_id)
    size = len(ids)
    if size < 40:
        raise ValueError("Validation population too small for the four declared budgets")
    args.output.mkdir(parents=True)
    whole = (tuple(range(size)),)
    plans = []
    for budget_index, fraction in enumerate([0.05, 0.1, 0.2, 0.4]):
        budget = integer_budget(fraction, size)
        path = args.output / f"uniform-queries-b{budget}.npz"
        sha = save_queries(path, whole, [budget], args.draws, 100000, budget_index, 1)
        plans.append({"budget": budget, "fraction": fraction, "file": path.name, "sha256": sha})
    # All reference-independent validation plans are saved before any reference lookup.
    train = static[static.split == "train"].reset_index(drop=True)
    train_labels = read_references(args.processed, tuple(train.record_id))
    labels = read_references(args.processed, ids)
    report = {
        "stages": ["E01", "E02"],
        "complete": False,
        "feature_hashes": hashes,
        "designation": "exploratory",
        "test_references_accessed": False,
        "descriptive_diagnostics": {
            "train": diagnostics(train, train_labels),
            "validation": diagnostics(validation, labels),
        },
        "uniform_validation_query_plans": plans,
        "results": {},
    }
    oracle = FrameOracle(labels, ids)
    truth = float(np.mean(list(labels.values())))
    y = np.array([labels[key] for key in ids])
    q = validation.f_q.to_numpy(float)
    exact = lru_cache(maxsize=None)(hypergeometric_interval)
    rows = []
    for plan in plans:
        budget = plan["budget"]
        indices = np.load(args.output / plan["file"])["selected"]
        for draw, selection in enumerate(indices):
            queried = oracle.query(tuple(ids[i] for i in selection))
            design = reconstruct_plan(whole, [budget], selection)
            for method, surrogate in [("M1", np.zeros(size)), ("M2", q)]:
                estimate = estimate_frames(ids, surrogate, design, queried)
                row = {"method": method, "budget": budget, "draw": draw, **estimate.as_dict()}
                if method == "M1":
                    low, high = exact(estimate.positives_revealed, budget, size)
                    row.update(hypergeometric_low=low, hypergeometric_high=high)
                rows.append(row)
    data = pd.DataFrame(rows)
    data.to_csv(args.output / "validation-draws.csv", index=False)
    for (method, budget), group in data.groupby(["method", "budget"]):
        population_values = y if method == "M1" else y - q
        summary = summarize_draws(group, truth)
        summary.update(
            {
                "empirical_sampling_variance": float(group.prevalence.var(ddof=1)),
                "mean_estimated_variance": float(group.variance.mean()),
                "known_design_variance": float(
                    (1 - budget / size) * np.var(population_values, ddof=1) / budget
                ),
            }
        )
        report["results"][f"{method}-b{budget}"] = summary
    report["complete"] = True
    (args.output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Completed {len(rows)} uniform development method-runs; no test references accessed")


if __name__ == "__main__":
    main()
