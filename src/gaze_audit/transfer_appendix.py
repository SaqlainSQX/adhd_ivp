"""Small projection of immutable aggregate evidence; no raw-data dependencies."""

import hashlib
import json
from pathlib import Path

SOURCES = {
    "demo/research/data.json": "docs/research/h-evidence-manifest.json",
    "docs/research/l-transfer-result.json": "docs/research/l-transfer-evidence-manifest.json",
    "docs/research/m-variance-result.json": "docs/research/m-evidence-manifest.json",
}


def build_summary(root):
    root = Path(root)
    loaded, provenance = {}, {}
    for name, manifest in SOURCES.items():
        content = (root / name).read_bytes().replace(b"\r\n", b"\n")
        digest = hashlib.sha256(content).hexdigest()
        assert digest == json.loads((root / manifest).read_text())["files"][name]
        loaded[name] = json.loads(content)
        provenance[name] = {"sha256": digest, "manifest": manifest}
    history = loaded["demo/research/data.json"]
    uco = loaded["docs/research/l-transfer-result.json"]
    variance = loaded["docs/research/m-variance-result.json"]
    rows = []
    for budget in [260, 521, 1043, 2087]:
        for method in ["uniform", "K4", "power-score"]:
            value = uco["results"][f"{method}-b{budget}"]
            rows.append(
                {
                    "budget": budget,
                    "method": method,
                    **{k: value[k] for k in ["rmse_pp", "bias_pp", "mae_pp"]},
                    "normal": value["intervals"]["normal"],
                    "exact": value["intervals"]["exact_binary_reference"],
                }
            )
    return {
        "version": 1,
        "scope": "aggregate course appendix; no raw labels or queries",
        "population": {
            "eligible_pairs": uco["population_size"],
            "test_clips": 15,
            "TV_shows": 4,
            "draws_per_method_budget": 1000,
            "total_validated_method_draws": 12000,
        },
        "primary_budget": 521,
        "budgets": [260, 521, 1043, 2087],
        "uco": {
            "rows": rows,
            "comparisons": uco["comparisons"],
            "reference_prevalence": uco["reference_prevalence"],
        },
        "childplay": {
            "primary_half_full_MC": history["frame"]["primary"],
            "primary_budget": 1032,
            "reference_prevalence": history["main"]["truth"],
            "main_temporal_rmse_pp": history["main"]["results"]["M4-b1032"]["rmse_pp"],
            "main_static_rmse_pp": history["main"]["results"]["M3-b1032"]["rmse_pp"],
            "block_temporal_static_ratio": history["block_primary"]["rmse_ratio"],
        },
        "variance": [
            {
                k: value[k]
                for k in [
                    "dataset",
                    "budget",
                    "A",
                    "B",
                    "C",
                    "half_minus_full_variance",
                    "exact_RMSE_ratio_half_over_full",
                    "MC_RMSE_ratio_half_over_full",
                ]
            }
            for value in variance["rows"]
        ],
        "checks": {
            "validated_draws": 12000,
            "bootstrap_comparisons": 12,
            "exact_variance_checks": 16,
            "stratum_dot_product_checks": 96,
            "sampled_frames_visually_reviewed": 75,
        },
        "provenance": provenance,
    }
