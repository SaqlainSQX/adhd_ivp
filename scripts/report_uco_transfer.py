"""Standalone aggregate-only L plots; never loads source data or model objects."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]


def main():
    result = json.loads((ROOT / "outputs/experiments/uco-transfer-l-v1/result.json").read_text())
    budgets = [260, 521, 1043, 2087]
    styles = {
        "K4": ("Frozen score strata, weight 1", "#2468a2"),
        "power-score": ("Same queries, weight 0.5", "#d97720"),
        "uniform": ("Uniform, weight 1", "#646b73"),
    }
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for method, (label, color) in styles.items():
        values = [result["results"][f"{method}-b{b}"] for b in budgets]
        axes[0, 0].plot(budgets, [v["rmse_pp"] for v in values], "o-", color=color, label=label)
        axes[0, 1].plot(
            budgets,
            [v["intervals"]["normal"]["coverage"] for v in values],
            "o-",
            color=color,
            label=label + " normal",
        )
        axes[1, 0].plot(budgets, [v["bias_pp"] for v in values], "o-", color=color, label=label)
        if method != "power-score":
            shared = "Shared stratified" if method == "K4" else "Uniform"
            axes[0, 1].plot(
                budgets,
                [v["intervals"]["exact_binary_reference"]["coverage"] for v in values],
                "s--",
                color=color,
                label=shared + " exact",
            )
            axes[1, 1].plot(
                budgets,
                [v["intervals"]["exact_binary_reference"]["mean_width_pp"] for v in values],
                "s--",
                color=color,
                label=shared + " exact",
            )
    axes[0, 0].set_title("Estimation error: lower is better")
    axes[0, 0].set_ylabel("RMSE (percentage points)")
    axes[0, 0].legend(fontsize=8)
    axes[0, 1].set_title("Coverage over 1,000 audit draws")
    axes[0, 1].axhline(0.95, color="black", linewidth=0.8, linestyle=":")
    axes[0, 1].set_ylim(0.925, 1.003)
    axes[0, 1].legend(fontsize=7, ncol=2)
    axes[1, 0].set_title("Signed bias: Monte Carlo variation on fixed corpus")
    axes[1, 0].axhline(0, color="black", linewidth=0.8)
    axes[1, 0].set_ylabel("Bias (percentage points)")
    axes[1, 1].set_title("Exact binary reference intervals remain wide")
    axes[1, 1].set_ylabel("Mean width (percentage points)")
    axes[1, 1].legend(fontsize=8)
    for ax in axes.flat:
        ax.set_xticks(budgets, labels=[str(b) for b in budgets])
        ax.set_xlabel("Exact queried pair-frame labels")
        ax.grid(alpha=0.2)
    primary = result["comparisons"]["power-score/K4-b521"]
    lo, hi = primary["draw_bootstrap_95pct"]
    fig.suptitle(
        "UCO transfer: half-weight correction loses on this population\n"
        f"Primary RMSE ratio = {primary['rmse_ratio']:.3f} "
        f"[draw-bootstrap 95%: {lo:.3f}, {hi:.3f}]",
        fontsize=14,
    )
    fig.text(
        0.5,
        0.015,
        "5,219 eligible pairs / 15 clips; frozen ChildPlay allocation. "
        "Same K4 queries at both weights.\nVSGaze backbone-family exposure; "
        "UCO retains raw border boxes; upstream ChildPlay boxes were clipped.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.065, 1, 0.91))
    target = ROOT / "reports/course-project/uco-transfer-l.png"
    fig.savefig(target, dpi=160)
    fig.savefig(target.with_suffix(".pdf"))
    print(target)


if __name__ == "__main__":
    main()
