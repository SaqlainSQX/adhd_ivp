"""Independent Q noise replay, scalar-form estimates and exhaustive binary intervals."""

import hashlib
import json
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd
from run_query_noise_v2 import load_dataset
from validate_uco_transfer import exhaustive_interval

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/query-noise-q-v2"


def main():
    result = json.loads((OUT / "result.json").read_text())
    data = pd.read_csv(OUT / "draw-results.csv")
    maximum_point, maximum_var, checked = 0.0, 0.0, 0
    z = NormalDist().inv_cdf(0.975)
    for name, code in [("ChildPlay", 1), ("UCO", 2)]:
        q, y, budget, designs, _ = load_dataset(name)
        u = np.array(
            [
                np.random.default_rng(np.random.SeedSequence([800000 + d, 1, code, 91])).random(
                    len(y)
                )
                for d in range(1000)
            ]
        )
        if hashlib.sha256(u.tobytes()).hexdigest() != result["noise_uniform_sha256"][name]:
            raise ValueError("Noise uniform replay differs")
        for eta in [0, 0.01, 0.02, 0.05]:
            for method, d in designs.items():
                weight = 0.5 if method == "power-score" else 1.0
                phi = q * weight
                selection = d["selections"]
                sizes = np.array(list(map(len, d["populations"])))
                counts = d["counts"]
                noisy = np.bitwise_xor(
                    y[selection].astype(np.int8),
                    (u[np.arange(1000)[:, None], selection] < eta).astype(np.int8),
                )
                saved = data[
                    (data.dataset == name) & (data.method == method) & (data.eta == eta)
                ].sort_values("draw")
                estimate = np.full(1000, np.sum(phi) / len(y))
                variance = np.zeros(1000)
                totals = np.zeros((1000, 2), int)
                offset = 0
                noncensus = int(sum(counts < sizes))
                analytical_var = 0.0
                for size, n, pop in zip(sizes, counts, d["populations"], strict=True):
                    residual = (
                        noisy[:, offset : offset + n] - phi[selection[:, offset : offset + n]]
                    )
                    sum_r = residual.sum(axis=1)
                    estimate += size / len(y) * sum_r / n
                    factor = (size / len(y)) ** 2 * (1 - n / size) / n
                    if n < size:
                        variance += factor * ((residual**2).sum(axis=1) - sum_r**2 / n) / (n - 1)
                        clean_r = (1 - 2 * eta) * y[pop] - phi[pop]
                        centered = clean_r - clean_r.mean()
                        analytical_var += factor * np.dot(centered, centered) / (size - 1)
                    analytical_var += eta * (1 - eta) * (size / len(y)) ** 2 / n
                    successes = noisy[:, offset : offset + n].sum(axis=1)
                    totals += np.array(
                        [
                            exhaustive_interval(
                                int(k), int(n), int(size), 0.05 / noncensus if noncensus else 0.05
                            )
                            for k in successes
                        ]
                    )
                    offset += n
                maximum_point = max(maximum_point, float(np.max(abs(estimate - saved.point))))
                maximum_var = max(maximum_var, float(np.max(abs(variance - saved.variance))))
                if not np.allclose(
                    saved.normal_low, estimate - z * np.sqrt(variance), rtol=0, atol=1e-12
                ):
                    raise ValueError("Noisy normal lower endpoint differs")
                if not np.allclose(
                    saved.normal_high, estimate + z * np.sqrt(variance), rtol=0, atol=1e-12
                ):
                    raise ValueError("Noisy normal upper endpoint differs")
                if not np.array_equal(saved.binary_low_total, totals[:, 0]) or not np.array_equal(
                    saved.binary_high_total, totals[:, 1]
                ):
                    raise ValueError("Exhaustive noisy integer interval differs")
                flips = (u[np.arange(1000)[:, None], selection] < eta).sum(axis=1)
                if not np.array_equal(flips, saved.flipped_labels):
                    raise ValueError("Noisy queried-label count differs")
                summary = next(
                    r
                    for r in result["rows"]
                    if r["dataset"] == name and r["method"] == method and r["eta"] == eta
                )
                error = estimate - y.mean()
                if (
                    abs(summary["bias_pp"] - error.mean() * 100) > 1e-10
                    or abs(summary["rmse_pp"] - np.sqrt(np.mean(error**2)) * 100) > 1e-10
                ):
                    raise ValueError("Noisy summary differs")
                if abs(summary["analytical"]["variance"] - analytical_var) > 1e-14:
                    raise ValueError("Analytical noisy variance differs")
                expected_bias = eta * (1 - 2 * y.mean())
                if abs(expected_bias - summary["analytical"]["bias"]) > 1e-14:
                    raise ValueError("Analytical noisy bias differs")
                normal_cov = np.mean(
                    (saved.normal_low <= y.mean()) & (y.mean() <= saved.normal_high)
                )
                exact_cov = np.mean((totals[:, 0] <= y.sum()) & (y.sum() <= totals[:, 1]))
                if (
                    normal_cov != summary["normal_coverage"]
                    or exact_cov != summary["naive_binary_clean_target_coverage"]
                ):
                    raise ValueError("Noisy coverage summary differs")
                checked += 1000
    if checked != 24000 or maximum_point > 1e-12 or maximum_var > 1e-12:
        raise ValueError("Q independent replay failed")
    proof = {
        "complete": True,
        "method_rate_draws_checked": checked,
        "max_point_difference": maximum_point,
        "max_variance_difference": maximum_var,
        "noise_uniform_hashes_reproduced": True,
        "label_flip_counts_reproduced": True,
        "exact_integer_interval_cases": exhaustive_interval.cache_info().currsize,
        "integer_interval_method": (
            "exhaustive feasible totals; independent of primary binary search"
        ),
        "analytic_bias_variance_and_all_coverage_cells_checked": True,
        "saved_reference_tables_changed": False,
    }
    (OUT / "independent-validation.json").write_text(json.dumps(proof, indent=2) + "\n")
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    main()
