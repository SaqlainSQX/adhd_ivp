"""Independent L recomputation with exhaustive integer hypergeometric endpoints."""

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd
from scipy.stats import hypergeom

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/experiments/uco-transfer-l-v1"


@lru_cache(maxsize=None)
def exhaustive_interval(k, n, size, alpha):
    if n == size:
        return k, k
    totals = np.arange(k, size - n + k + 1)
    accepted = (hypergeom.sf(k - 1, size, totals, n) >= alpha / 2) & (
        hypergeom.cdf(k, size, totals, n) >= alpha / 2
    )
    assert accepted.any()
    return int(totals[accepted][0]), int(totals[accepted][-1])


def main():
    cfg = json.loads((ROOT / "configs/uco-transfer-l-v1.json").read_text())
    plans = json.loads((OUT / "query-manifest.json").read_text())
    result = json.loads((OUT / "result.json").read_text())
    scores = pd.read_csv(OUT / "scores-population-order.csv")
    oracle = pd.read_csv(ROOT / "data/processed/uco-eligible-k4-v2/oracle.csv").set_index(
        "record_id"
    )
    y = oracle.loc[scores.record_id].label.to_numpy(float)
    q = scores.q.to_numpy(float)
    data = pd.read_csv(OUT / "draw-results.csv")
    assert len(y) == 5219 and len(data) == 12000
    checked, max_point, max_var, ratio_checks = 0, 0.0, 0.0, 0
    z = NormalDist().inv_cdf(0.975)
    for entry in plans:
        path = OUT / entry["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]
        selections = np.load(path)["selected"]
        pops = [np.asarray(p) for p in entry["populations"]]
        counts = np.array(entry["counts"])
        sizes = np.array(list(map(len, pops)))
        assert sum(counts) == entry["budget"]
        assert sum(sizes) == len(y) and np.all(counts >= np.minimum(sizes, 20))
        for draw in range(1000):
            rng = np.random.default_rng(
                np.random.SeedSequence([200000 + draw, entry["budget_index"], entry["stream"]])
            )
            expected = np.concatenate(
                [
                    rng.choice(p, size=int(n), replace=False)
                    for p, n in zip(pops, counts, strict=True)
                ]
            )
            assert np.array_equal(selections[draw], expected)
            assert len(np.unique(expected)) == entry["budget"]
        edges = np.r_[0, np.cumsum(counts)]
        intervals = np.zeros((1000, 2), dtype=int)
        noncensus = int(sum(counts < sizes))
        for h, (pop, n, size) in enumerate(zip(pops, counts, sizes, strict=True)):
            selected = selections[:, edges[h] : edges[h + 1]]
            assert np.isin(selected, pop).all()
            successes = y[selected].sum(axis=1).astype(int)
            intervals += np.array(
                [
                    exhaustive_interval(
                        int(k), int(n), int(size), 0.05 / noncensus if noncensus else 0.05
                    )
                    for k in successes
                ]
            )
        methods = ["K4", "power-score"] if entry["design"] == "K4" else ["uniform"]
        for method in methods:
            weight = cfg["methods"][method]["weight"]
            saved = data[(data.method == method) & (data.budget == entry["budget"])].sort_values(
                "draw"
            )
            point, variance = np.full(1000, np.mean(q * weight)), np.zeros(1000)
            design_var = 0.0
            for h, (pop, n, size) in enumerate(zip(pops, counts, sizes, strict=True)):
                selected = selections[:, edges[h] : edges[h + 1]]
                residual = y[selected] - weight * q[selected]
                point += size / len(y) * residual.mean(axis=1)
                factor = (size / len(y)) ** 2 * (1 - n / size) / n
                if n < size:
                    variance += factor * np.var(residual, axis=1, ddof=1)
                    design_var += factor * np.var(y[pop] - weight * q[pop], ddof=1)
            max_point = max(max_point, float(np.max(np.abs(point - saved.prevalence))))
            max_var = max(max_var, float(np.max(np.abs(variance - saved.variance))))
            assert np.allclose(saved.normal_low, point - z * np.sqrt(variance), rtol=0, atol=1e-12)
            assert np.allclose(saved.normal_high, point + z * np.sqrt(variance), rtol=0, atol=1e-12)
            assert np.array_equal(intervals[:, 0], saved.exact_lower_total)
            assert np.array_equal(intervals[:, 1], saved.exact_upper_total)
            summary = result["results"][f"{method}-b{entry['budget']}"]
            assert abs(summary["rmse_pp"] - np.sqrt(np.mean((point - y.mean()) ** 2)) * 100) < 1e-10
            assert abs(summary["exact_design_variance"] - design_var) < 1e-14
            coverage = np.mean((intervals[:, 0] <= y.sum()) & (y.sum() <= intervals[:, 1]))
            assert coverage == summary["intervals"]["exact_binary_reference"]["coverage"]
            checked += 1000
    assert max_point < 1e-12 and max_var < 1e-12 and checked == 12000
    for bi, budget in enumerate(cfg["budgets"]):
        errors = {
            m: data[(data.method == m) & (data.budget == budget)]
            .sort_values("draw")
            .prevalence.to_numpy()
            - y.mean()
            for m in cfg["methods"]
        }
        for top, bottom in [("power-score", "K4"), ("K4", "uniform"), ("power-score", "uniform")]:
            comparison = result["comparisons"][f"{top}/{bottom}-b{budget}"]
            assert (
                abs(
                    comparison["rmse_ratio"]
                    - np.linalg.norm(errors[top]) / np.linalg.norm(errors[bottom])
                )
                < 1e-12
            )
            ix = np.random.default_rng(500000 + bi).integers(1000, size=(2000, 1000))
            bootstrap = np.sqrt(
                np.mean(errors[top][ix] ** 2, axis=1) / np.mean(errors[bottom][ix] ** 2, axis=1)
            )
            assert np.allclose(
                np.quantile(bootstrap, [0.025, 0.975]),
                comparison["draw_bootstrap_95pct"],
                rtol=0,
                atol=1e-12,
            )
            ratio_checks += 1
    proof = {
        "complete": True,
        "method_draws_independently_checked": checked,
        "integer_reference_interval_method": "exhaustive feasible totals using scipy sf/cdf",
        "integer_interval_cache_entries": exhaustive_interval.cache_info().currsize,
        "max_point_difference": max_point,
        "max_variance_difference": max_var,
        "paired_bootstrap_comparisons_checked": ratio_checks,
        "normal_bounds_and_exact_design_variances_checked": True,
        "all_query_RNGs_and_unique_costs_reproduced": True,
    }
    (OUT / "independent-validation-exhaustive.json").write_text(json.dumps(proof, indent=2) + "\n")
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    main()
