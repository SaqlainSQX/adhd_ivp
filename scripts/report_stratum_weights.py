"""Plot all fixed U coefficient methods from saved outcomes."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    rows = json.loads(Path("outputs/stratum-weights-u-v1/result.json").read_text(encoding="utf-8"))[
        "rows"
    ]
    methods = [
        ("full", "Full", "#2463ad"),
        ("half", "Half", "#b65424"),
        ("global", "Training global", "#458340"),
        ("stratum", "Training per-stratum", "#793ea6"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    for i, dataset in enumerate(["ChildPlay", "UCO"]):
        for method, label, color in methods:
            cells = sorted(
                [r for r in rows if r["dataset"] == dataset and r["method"] == method],
                key=lambda r: r["budget"],
            )
            x = [r["budget"] for r in cells]
            axes[i, 0].plot(x, [r["rmse_pp"] for r in cells], "o-", color=color, label=label)
            axes[i, 1].plot(x, [r["normal_coverage"] * 100 for r in cells], "o-", color=color)
        axes[i, 0].set_title(dataset + ": RMSE (percentage points)")
        axes[i, 1].set_title(dataset + ": normal95% coverage (%)")
        axes[i, 1].axhline(95, color="gray", linestyle="--", lw=1)
        axes[i, 1].set_ylim(0, 102)
        for ax in axes[i]:
            ax.set_xlabel("Queried reference labels")
            ax.set_xticks(x)
            ax.grid(alpha=0.2)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=4, fontsize=9)
    fig.suptitle(
        "Training-only coefficient extension: all registered methods/budgets\n"
        "Same K4 queries within each comparison; no test-selected coefficients.",
        fontsize=12,
    )
    target = Path("reports/course-project/stratum-weights-u")
    fig.savefig(target.with_suffix(".png"), dpi=160)
    fig.savefig(target.with_suffix(".pdf"))
    plt.close(fig)


if __name__ == "__main__":
    main()
