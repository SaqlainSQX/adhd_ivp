"""Render only saved Q aggregates; no fitting or scientific recomputation."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    rows = json.loads(Path("outputs/query-noise-q-v2/result.json").read_text(encoding="utf-8"))[
        "rows"
    ]
    fig, axes = plt.subplots(2, 3, figsize=(13, 7), constrained_layout=True)
    methods = [
        ("K4", "K4 full", "#2463ad"),
        ("power-score", "K4 half", "#b65424"),
        ("uniform", "Uniform + q", "#458340"),
    ]
    for i, dataset in enumerate(["ChildPlay", "UCO"]):
        for method, label, color in methods:
            cells = [r for r in rows if r["dataset"] == dataset and r["method"] == method]
            x = [r["eta"] * 100 for r in cells]
            for j, key in enumerate(["bias_pp", "rmse_pp", "normal_coverage"]):
                axes[i, j].plot(
                    x,
                    [r[key] * (100 if j == 2 else 1) for r in cells],
                    "o-",
                    color=color,
                    label=label,
                )
        cells = [r for r in rows if r["dataset"] == dataset and r["method"] == "K4"]
        axes[i, 0].plot(
            [r["eta"] * 100 for r in cells],
            [100 * r["analytical"]["bias"] for r in cells],
            "k--",
            label="Analytical bias",
        )
        axes[i, 2].axhline(95, color="gray", linestyle="--", linewidth=1)
        for j, title in enumerate(
            [
                "Signed bias (percentage points)",
                "RMSE (percentage points)",
                "Normal interval coverage (%)",
            ]
        ):
            axes[i, j].set_title(f"{dataset}: {title}", fontsize=10)
            axes[i, j].set_xlabel("Synthetic independent flip rate (%)")
            axes[i, j].grid(alpha=0.2)
        axes[i, 2].set_ylim(-2, 102)
    axes[0, 0].legend(fontsize=8)
    fig.suptitle(
        "Synthetic query-label errors: fixed queries and primary label budgets\n"
        "ChildPlay n=1032; UCO n=521; 1000 draws per method/rate. Clean reference target.",
        fontsize=12,
    )
    out = Path("reports/course-project/query-noise-q")
    fig.savefig(out.with_suffix(".png"), dpi=160)
    fig.savefig(out.with_suffix(".pdf"))
    plt.close(fig)


if __name__ == "__main__":
    main()
