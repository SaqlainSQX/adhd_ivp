"""Independent R replay with XOR errors, scalar sums and exhaustive intervals."""

import hashlib
import json
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd
from run_query_noise_v2 import load_dataset
from validate_uco_transfer import exhaustive_interval

OUT = Path("outputs/directional-noise-r-v1")


def main():
    result = json.loads((OUT / "result.json").read_text(encoding="utf-8"))
    cfg = json.loads(Path("configs/directional-noise-r-v1.json").read_text(encoding="utf-8"))
    data = pd.read_csv(OUT / "draw-results.csv")
    z = NormalDist().inv_cdf(0.975)
    checked, max_point, max_var = 0, 0.0, 0.0
    for name, code in cfg["datasets"].items():
        q, y, budget, designs, _ = load_dataset(name)
        uniforms = np.array(
            [
                np.random.default_rng(np.random.SeedSequence([810000 + d, 1, code, 92])).random(
                    len(y)
                )
                for d in range(1000)
            ]
        )
        if hashlib.sha256(uniforms.tobytes()).hexdigest() != result["noise_uniform_sha256"][name]:
            raise ValueError("R uniform hash differs")
        for case in cfg["cases"]:
            a, b = case["a"], case["b"]
            for method, design in designs.items():
                phi = q * cfg["weights"][method]
                selection = design["selections"]
                flip_rate = a * (1 - y[selection]) + b * y[selection]
                flips = uniforms[np.arange(1000)[:, None], selection] < flip_rate
                noisy = np.bitwise_xor(y[selection].astype(np.int8), flips.astype(np.int8))
                saved = data[
                    (data.dataset == name)
                    & (data.method == method)
                    & (data["case"] == case["name"])
                ].sort_values("draw")
                if len(saved) != 1000 or not (saved.budget == budget).all():
                    raise ValueError("R draw count or budget differs")
                point, variance, totals = (
                    np.full(1000, phi.sum() / len(y)),
                    np.zeros(1000),
                    np.zeros((1000, 2), int),
                )
                sizes, counts = list(map(len, design["populations"])), design["counts"]
                noncensus = sum(n < size for n, size in zip(counts, sizes, strict=True))
                analytical_var, start = 0.0, 0
                for pop, n, size in zip(design["populations"], counts, sizes, strict=True):
                    r = noisy[:, start : start + n] - phi[selection[:, start : start + n]]
                    sr = r.sum(axis=1)
                    w = size / len(y)
                    point += w * sr / n
                    if n < size:
                        factor = w * w * (1 - n / size) / n
                        variance += factor * ((r * r).sum(axis=1) - sr * sr / n) / (n - 1)
                        residual_mean = a + (1 - a - b) * y[pop] - phi[pop]
                        centered = residual_mean - residual_mean.mean()
                        analytical_var += factor * np.dot(centered, centered) / (size - 1)
                    v = (1 - y[pop]) * a * (1 - a) + y[pop] * b * (1 - b)
                    analytical_var += w * w * v.sum() / size / n
                    successes = noisy[:, start : start + n].sum(axis=1)
                    totals += np.array(
                        [
                            exhaustive_interval(
                                int(k), int(n), int(size), 0.05 / noncensus if noncensus else 0.05
                            )
                            for k in successes
                        ]
                    )
                    start += n
                lo, hi = point - z * np.sqrt(variance), point + z * np.sqrt(variance)
                max_point = max(max_point, float(np.max(abs(point - saved.point))))
                max_var = max(max_var, float(np.max(abs(variance - saved.variance))))
                for field, expected in [("normal_low", lo), ("normal_high", hi)]:
                    if not np.allclose(saved[field], expected, rtol=0, atol=1e-12):
                        raise ValueError(f"R {field} differs")
                for field, expected in [
                    ("binary_low_total", totals[:, 0]),
                    ("binary_high_total", totals[:, 1]),
                    ("flipped_labels", flips.sum(axis=1)),
                ]:
                    if not np.array_equal(saved[field], expected):
                        raise ValueError(f"R {field} differs")
                row = next(
                    r
                    for r in result["rows"]
                    if r["dataset"] == name and r["method"] == method and r["case"] == case["name"]
                )
                error = point - y.mean()
                expected_fields = {
                    "bias_pp": error.mean() * 100,
                    "rmse_pp": np.sqrt(np.mean(error**2)) * 100,
                    "normal_coverage": np.mean((lo <= y.mean()) & (y.mean() <= hi)),
                    "normal_width_pp": np.mean(hi - lo) * 100,
                    "naive_binary_clean_target_coverage": np.mean(
                        (totals[:, 0] <= y.sum()) & (y.sum() <= totals[:, 1])
                    ),
                    "naive_binary_width_pp": np.mean(totals[:, 1] - totals[:, 0]) / len(y) * 100,
                    "mean_label_flips": flips.sum(axis=1).mean(),
                }
                for field, expected in expected_fields.items():
                    if abs(row[field] - expected) > 1e-10:
                        raise ValueError(f"R aggregate {field} differs")
                bias = a * (1 - y.mean()) - b * y.mean()
                for field, expected in [
                    ("bias", bias),
                    ("variance", analytical_var),
                    ("MSE", analytical_var + bias * bias),
                ]:
                    if abs(row["analytical"][field] - expected) > 1e-13:
                        raise ValueError(f"R analytical {field} differs")
                checked += 1000
                print(f"Validated {name}/{method}/{case['name']}", flush=True)
    if checked != 18000 or max_point > 1e-12 or max_var > 1e-12:
        raise ValueError("R independent replay failed")
    proof = {
        "complete": True,
        "method_case_draws_checked": checked,
        "max_point_difference": max_point,
        "max_variance_difference": max_var,
        "rng_costs_flips_all_endpoints_and_summary_fields_checked": True,
        "exact_integer_interval_cases": exhaustive_interval.cache_info().currsize,
        "interval_method": "exhaustive feasible integer totals",
        "analytical_moments_independently_checked": True,
    }
    (OUT / "independent-validation.json").write_text(
        json.dumps(proof, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    main()
