"""Reproduce planning arithmetic; these are not MTGS performance experiments."""

import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import hypergeom


def checks(inventory):
    test = inventory["splits"]["test"]
    n_population = test["eligible_binary_pairs"]
    positives = test["positive"]
    p = positives / n_population
    budgets = []
    for fraction in [0.05, 0.1, 0.2, 0.4]:
        n = round(fraction * n_population)
        se = math.sqrt((1 - n / n_population) * p * (1 - p) / n * n_population / (n_population - 1))
        budgets.append(
            {
                "fraction": fraction,
                "frame_labels": n,
                "expected_positive_frames": n * p,
                "human_srs_normal_half_width_pp": 100 * 1.96 * se,
                "human_srs_probability_zero_positives": float(
                    hypergeom.pmf(0, n_population, positives, n)
                ),
            }
        )
    development = sum(inventory["splits"][s]["eligible_binary_pairs"] for s in ["train", "val"])
    baseline_budget = round(0.1 * n_population)
    assumed_rmse_ratio = 0.9
    savings = baseline_budget * (1 - assumed_rmse_ratio**2)
    # Exact finite-population design variances for an invented example.
    # Constant q=.5 cancels from residual variance, so no model claim is involved.
    toy = {}
    for name, labels in {
        "persistent": np.repeat([0.0, 1.0, 0.0, 1.0], 5),
        "alternating": np.tile([0.0, 1.0], 10),
    }.items():
        residual = labels - 0.5
        block_residual = residual.reshape(-1, 5).sum(axis=1)
        toy[name] = float(np.var(block_residual, ddof=1) / (5 * np.var(residual, ddof=1)))
    result = {
        "description": "Planning arithmetic and labeled toy examples, not proposed-method results",
        "source_inventory_sha256": inventory["archive_sha256"],
        "eligible_prevalence": p,
        "unknown_fraction_of_real_pair_records": test["unknown"] / (n_population + test["unknown"]),
        "hypothetical_full_population_binary_bounds": [
            positives / (n_population + test["unknown"]),
            (positives + test["unknown"]) / (n_population + test["unknown"]),
        ],
        "uniform_frame_sampling_reference": budgets,
        "development_label_cost": development,
        "cost_scenario": {
            "baseline_audit_labels": baseline_budget,
            "assumed_rmse_ratio": assumed_rmse_ratio,
            "approximate_saving_per_corpus_ignoring_fpc": savings,
            "break_even_corpora_ignoring_fpc": math.floor(development / savings) + 1,
            "optimistic_lower_bound_corpora_if_all_baseline_labels_saved": (
                math.floor(development / baseline_budget) + 1
            ),
            "note": "Illustrative scaling scenario, not an observed saving; ignores compute/time",
        },
        "invented_exact_block_to_frame_variance_ratios": toy,
        "exchangeable_cost_scenarios": [
            {
                "block_length": k,
                "residual_correlation": rho,
                "setup_to_per_label_cost_ratio": overhead,
                "design_effect": 1 + (k - 1) * rho,
                "approx_variance_ratio_at_equal_time": (
                    (1 + (k - 1) * rho) * (overhead / k + 1) / (overhead + 1)
                ),
            }
            for k, rho, overhead in [(5, 0.8, 0), (5, 0.8, 10), (5, 0.8, 100)]
        ],
    }
    return result


if __name__ == "__main__":
    source = Path("outputs/research/vsgaze-inventory.json")
    result = checks(json.loads(source.read_text(encoding="utf-8")))
    output = Path("outputs/research/feasibility-checks.json")
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
