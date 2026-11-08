"""Registered M: explain frozen weight1/.5 comparisons, without selecting a weight."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/variance-explanation-m-v1"


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    child = ROOT / "outputs/experiments/timed-d-20261108-v1"
    uco = ROOT / "outputs/experiments/uco-transfer-l-v1"
    source_paths = [
        child / "population_index.csv",
        child / "K4-training.json",
        child / "query-manifest.json",
        child / "result.json",
        child / "posthoc-exact-design-variance.json",
        uco / "scores-population-order.csv",
        uco / "query-manifest.json",
        uco / "result.json",
        ROOT / "data/processed/uco-eligible-k4-v2/oracle.csv",
        ROOT / "data/processed/vsgaze-17357752-v1/oracle/oracle_labels.csv",
        ROOT / "outputs/experiments/course-20261107-v1/features/features-static.csv",
    ]
    registration = {
        "stage": "M-post-hoc-descriptive-no-weight-selection",
        "protocol_sha256": sha(ROOT / "docs/VARIANCE_DECOMPOSITION_M.md"),
        "implementation_sha256": sha(Path(__file__)),
        "input_sha256": {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in source_paths},
    }
    (OUT / "registration.json").write_text(json.dumps(registration, indent=2) + "\n")
    order = pd.read_csv(child / "population_index.csv").record_id
    features = pd.read_csv(source_paths[-1], usecols=["record_id", "f_q"]).set_index("record_id")
    child_q = features.loc[order].f_q.to_numpy(float)
    labels = pd.read_csv(source_paths[-2]).set_index("record_id")
    child_y = labels.loc[order].label.to_numpy(float)
    score = pd.read_csv(uco / "scores-population-order.csv")
    uco_y = (
        pd.read_csv(source_paths[-3])
        .set_index("record_id")
        .loc[score.record_id]
        .label.to_numpy(float)
    )
    training = json.loads((child / "K4-training.json").read_text())
    rows, max_difference = [], 0.0
    for name, base, q, y in [
        ("ChildPlay", child, child_q, child_y),
        ("UCO", uco, score.q.to_numpy(float), uco_y),
    ]:
        plans = json.loads((base / "query-manifest.json").read_text())
        plans = [p for p in plans if p.get("policy", p.get("design")) == "K4"]
        saved = json.loads((base / "result.json").read_text())
        old_exact = (
            {
                (v["policy"], v["budget"]): (v["exact_design_rmse_pp"] / 100) ** 2
                for v in json.loads((child / "posthoc-exact-design-variance.json").read_text())[
                    "rows"
                ]
            }
            if name == "ChildPlay"
            else None
        )
        groups = np.searchsorted(training["cuts"], q, side="left")
        present = np.unique(groups)
        for plan in plans:
            budget = plan["budget"]
            sizes = plan.get("sizes", list(map(len, plan.get("populations", []))))
            assert list(np.bincount(groups)[present]) == sizes
            strata = []
            for h, n, size in zip(present, plan["counts"], sizes, strict=True):
                pos = np.flatnonzero(groups == h)
                factor = (size / len(q)) ** 2 * (1 - n / size) / n
                vy = float(np.var(y[pos], ddof=1)) if size > 1 else 0.0
                vq = float(np.var(q[pos], ddof=1)) if size > 1 else 0.0
                covariance = float(np.cov(y[pos], q[pos], ddof=1)[0, 1]) if size > 1 else 0.0
                strata.append(
                    {
                        "stratum": int(h),
                        "size": size,
                        "labels": n,
                        "A": factor * vy,
                        "B": factor * covariance,
                        "C": factor * vq,
                    }
                )
            a, b, c = [sum(s[key] for s in strata) for key in ("A", "B", "C")]
            variances = {}
            for method, weight in [("K4", 1.0), ("power-score", 0.5)]:
                algebra = a - 2 * weight * b + weight**2 * c
                direct = sum(
                    (size / len(q)) ** 2
                    * (1 - n / size)
                    / n
                    * np.var(y[groups == h] - weight * q[groups == h], ddof=1)
                    if n < size
                    else 0.0
                    for h, n, size in zip(present, plan["counts"], sizes, strict=True)
                )
                reference = (
                    old_exact[method, budget]
                    if old_exact is not None
                    else saved["results"][f"{method}-b{budget}"]["exact_design_variance"]
                )
                difference = max(abs(algebra - direct), abs(algebra - reference))
                max_difference = max(max_difference, difference)
                assert difference < 1e-14
                variances[method] = algebra
            delta = variances["power-score"] - variances["K4"]
            assert abs(delta - (b - 0.75 * c)) < 1e-15
            full = saved["results"][f"K4-b{budget}"]["rmse_pp"]
            half = saved["results"][f"power-score-b{budget}"]["rmse_pp"]
            rows.append(
                {
                    "dataset": name,
                    "budget": budget,
                    "population_size": len(q),
                    "strata": strata,
                    "A": a,
                    "B": b,
                    "C": c,
                    "half_minus_full_variance": delta,
                    "B_minus_three_quarters_C": b - 0.75 * c,
                    "fixed_weight_variances": variances,
                    "exact_RMSE_ratio_half_over_full": float(
                        np.sqrt(variances["power-score"] / variances["K4"])
                    ),
                    "exact_MSE_ratio_half_over_full": variances["power-score"] / variances["K4"],
                    "MC_RMSE_ratio_half_over_full": half / full,
                    "MC_MSE_ratio_half_over_full": (half / full) ** 2,
                }
            )
    result = {
        "complete": True,
        "designation": "post-hoc finite-population explanation",
        "no_new_weight_selected_or_evaluated": True,
        "no_new_queries_or_inference": True,
        "budgets_explained": len(rows),
        "fixed_weight_checks": 2 * len(rows),
        "max_saved_vs_algebra_variance_difference": max_difference,
        "rows": rows,
    }
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=2))
    for row in rows:
        print(
            row["dataset"],
            row["budget"],
            "delta",
            row["half_minus_full_variance"],
            "exact RMSE ratio",
            row["exact_RMSE_ratio_half_over_full"],
        )


if __name__ == "__main__":
    main()
