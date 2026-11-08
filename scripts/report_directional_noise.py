"""Render saved R aggregates without refitting or selecting settings."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    rows = json.loads(
        Path("outputs/directional-noise-r-v1/result.json").read_text(encoding="utf-8")
    )["rows"]
    cases = ["clean", "false-positive", "false-negative"]
    fig, axes = plt.subplots(2, 3, figsize=(13, 7), constrained_layout=True)
    methods = [
        ("K4", "K4 full", "#2463ad"),
        ("power-score", "K4 half", "#b65424"),
        ("uniform", "Uniform + q", "#458340"),
    ]
    for i, dataset in enumerate(["ChildPlay", "UCO"]):
        for offset, (method, label, color) in enumerate(methods):
            cells = [
                next(
                    r
                    for r in rows
                    if r["dataset"] == dataset and r["method"] == method and r["case"] == case
                )
                for case in cases
            ]
            for j, key in enumerate(["bias_pp", "rmse_pp", "normal_coverage"]):
                axes[i, j].bar(
                    np.arange(3) + (offset - 1) * 0.24,
                    [r[key] * (100 if j == 2 else 1) for r in cells],
                    width=0.23,
                    color=color,
                    label=label,
                )
        full = [
            next(
                r
                for r in rows
                if r["dataset"] == dataset and r["method"] == "K4" and r["case"] == case
            )
            for case in cases
        ]
        axes[i, 0].plot(
            np.arange(3),
            [100 * r["analytical"]["bias"] for r in full],
            "kx",
            markersize=9,
            label="Analytical bias",
        )
        axes[i, 0].axhline(0, color="gray", linewidth=0.8)
        axes[i, 2].axhline(95, color="gray", linestyle="--", linewidth=1)
        axes[i, 2].set_ylim(0, 103)
        for j, title in enumerate(["Signed bias (pp)", "RMSE (pp)", "Normal coverage (%)"]):
            axes[i, j].set_title(f"{dataset}: {title}")
            axes[i, j].set_xticks(np.arange(3), ["Clean", "FP 2%", "FN 2%"])
            axes[i, j].grid(axis="y", alpha=0.2)
            axes[i, j].set_axisbelow(True)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=4, fontsize=9)
    fig.suptitle(
        "Synthetic directional label errors: frozen queries and label budgets\n"
        "FP/FN rates are conditional on the reference class; total corruptions differ. "
        "1000 draws/cell.",
        fontsize=12,
    )
    target = Path("reports/course-project/directional-noise-r")
    fig.savefig(target.with_suffix(".png"), dpi=160)
    fig.savefig(target.with_suffix(".pdf"))
    plt.close(fig)


if __name__ == "__main__":
    main()
