"""Independently recompute every saved audit from frozen queries and reference values."""

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from gaze_audit.frame_study import file_hash, load_feature_population, make_design, read_references


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--processed", type=Path, default=Path("data/processed/vsgaze-17357752-v1"))
    args = parser.parse_args()
    root, output = args.run, args.run / "independent-validation.json"
    if output.exists():
        parser.error(
            "Preserve existing validation evidence; use a separately copied run for rechecks"
        )
    evaluation, development = root / "evaluation", root / "development"
    report = json.loads((evaluation / "result.json").read_text())
    lock = json.loads((development / "policy-lock.json").read_text())
    tables, hashes = load_feature_population(root / "features")
    if (
        not report["complete"]
        or report["feature_hashes"] != hashes
        or lock["feature_hashes"] != hashes
    ):
        raise ValueError("Frozen input/result hashes disagree")
    if file_hash(development / "policy-lock.json") != report["policy_lock_sha256"]:
        raise ValueError("Policy lock changed after evaluation")
    if file_hash(args.processed / "oracle/oracle_labels.csv") != report["oracle_file_sha256"]:
        raise ValueError("Oracle version changed after evaluation")
    mask = tables["static"].split.eq("test").to_numpy()
    test = {name: table.loc[mask].reset_index(drop=True) for name, table in tables.items()}
    ids = tuple(test["static"].record_id)
    if tuple(pd.read_csv(evaluation / "population_index.csv").record_id) != ids:
        raise ValueError("Saved test population row order changed")
    labels = read_references(args.processed, ids)
    y = np.array([labels[key] for key in ids], dtype=float)
    q = test["static"].f_q.to_numpy(float)
    policies = {}
    for method, key in [("M3", "selected_static"), ("M4", "selected_temporal")]:
        name = lock[key]["feature_set"]
        path = development / f"{name}-policy.joblib"
        if file_hash(path) != lock["model_hashes"][name]:
            raise ValueError("Frozen policy model changed")
        policies[method] = joblib.load(path)
    contextual = policies["M4"].contextual_surrogate(test[lock["selected_temporal"]["feature_set"]])
    surrogate = {"M1": np.zeros(len(ids)), "M2": q, "M3": q, "M4": q, "M5": contextual}
    data = pd.read_csv(evaluation / "draw-results.csv")
    expected_rows = 5 * 4 * report["draws_per_method_budget"]
    if len(data) != expected_rows or data.duplicated(["method", "budget", "draw"]).any():
        raise ValueError("Incomplete or duplicate method/budget/draw grid")
    manifest = json.loads((evaluation / "query-manifest.json").read_text())
    comparisons = []
    max_point_difference, max_variance_difference = 0.0, 0.0
    for entry in manifest:
        path = evaluation / entry["file"]
        if file_hash(path) != entry["sha256"]:
            raise ValueError("Saved query file changed")
        saved = np.load(path)
        selected, counts = saved["selected"], saved["counts"]
        design = entry["design"]
        if selected.shape != (report["draws_per_method_budget"], entry["budget"]):
            raise ValueError("Incorrect realized budget")
        if (selected < 0).any() or (selected >= len(ids)).any():
            raise ValueError("Out-of-population query")
        if (np.diff(np.sort(selected, axis=1), axis=1) == 0).any():
            raise ValueError("Sampling was not without replacement")
        if design == "uniform":
            populations, expected_counts = (tuple(range(len(ids))),), np.array([entry["budget"]])
            methods, stream = ["M1", "M2", "M5"], 1
        else:
            field = "selected_static" if design == "M3" else "selected_temporal"
            chosen = lock[field]
            populations, expected_counts = make_design(
                policies[design].strata(test[chosen["feature_set"]]),
                policies[design].residual_sd,
                entry["budget"],
                chosen["alpha"],
            )
            methods, stream = [design], 3 if design == "M3" else 4
        if (
            not np.array_equal(counts, expected_counts)
            or list(map(len, populations)) != entry["stratum_sizes"]
        ):
            raise ValueError("Saved allocation differs from frozen policy")
        # Every draw is reproduced, not merely the demonstration draw.
        budget_index = [0.05, 0.1, 0.2, 0.4].index(entry["fraction"])
        for draw, saved_row in enumerate(selected):
            rng = np.random.default_rng(
                np.random.SeedSequence([200000 + draw, budget_index, stream])
            )
            regenerated = np.concatenate(
                [
                    rng.choice(pop, size=int(n), replace=False)
                    for pop, n in zip(populations, counts, strict=True)
                ]
            )
            if not np.array_equal(regenerated, saved_row):
                raise ValueError("Query RNG replay failed")
        edges = np.r_[0, np.cumsum(counts)]
        for method in methods:
            prediction = surrogate[method]
            point = np.full(len(selected), prediction.mean())
            variance = np.zeros(len(selected))
            for h, population in enumerate(populations):
                positions = selected[:, edges[h] : edges[h + 1]]
                residuals = y[positions] - prediction[positions]
                weight, nh, n = len(population) / len(ids), len(population), counts[h]
                point += weight * residuals.mean(axis=1)
                if n < nh:
                    variance += weight**2 * (1 - n / nh) * residuals.var(axis=1, ddof=1) / n
            subset = data[(data.method == method) & (data.budget == entry["budget"])].sort_values(
                "draw"
            )
            if len(subset) != len(selected) or not subset.labels_revealed.eq(entry["budget"]).all():
                raise ValueError("Wrong draw count or charged label budget")
            point_difference = float(np.max(np.abs(point - subset.prevalence.to_numpy())))
            variance_difference = float(np.max(np.abs(variance - subset.variance.to_numpy())))
            max_point_difference = max(max_point_difference, point_difference)
            max_variance_difference = max(max_variance_difference, variance_difference)
            if point_difference > 1e-12 or variance_difference > 1e-12:
                raise ValueError("Independent difference-estimator recomputation disagrees")
            summary = report["results"][f"{method}-b{entry['budget']}"]
            rmse = float(np.sqrt(np.mean((point - y.mean()) ** 2)) * 100)
            if abs(rmse - summary["rmse_pp"]) > 1e-10:
                raise ValueError("Reported RMSE does not match independent recomputation")
            comparisons.append(
                {
                    "method": method,
                    "budget": entry["budget"],
                    "draws_recomputed": len(selected),
                    "rmse_pp": rmse,
                }
            )
    evidence = {
        "status": "passed",
        "complete": True,
        "sampled_audits_recomputed": len(data),
        "query_streams_replayed": len(manifest),
        "max_point_difference": max_point_difference,
        "max_variance_difference": max_variance_difference,
        "population_size": len(ids),
        "reference_prevalence": float(y.mean()),
        "checks": [
            "input and policy hashes",
            "exact common population and row order",
            "all query RNG streams",
            "without-replacement exact budgets",
            "frozen allocation",
            "independent point and finite-population variance formulas",
            "all RMSE summaries",
        ],
        "method_budget_checks": comparisons,
        "evaluation_result_sha256": file_hash(evaluation / "result.json"),
    }
    output.write_text(json.dumps(evidence, indent=2) + "\n")
    print(f"Independently verified all {len(data):,} sampled audits: {output}")


if __name__ == "__main__":
    main()
