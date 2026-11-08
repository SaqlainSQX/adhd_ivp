"""Aggregate-only figure for the registered descriptive variance decomposition."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]


def main():
    result = json.loads((ROOT / "outputs/variance-explanation-m-v1/result.json").read_text())
    fig, axes = plt.subplots(1, 3, figsize=(13, 5.3))
    for ax, name, budget in zip(axes[:2], ["ChildPlay", "UCO"], [1032, 521], strict=True):
        row = next(r for r in result["rows"] if r["dataset"] == name and r["budget"] == budget)
        values = [row["B"] * 10000, 0.75 * row["C"] * 10000]
        bars = ax.bar(["B", "0.75 C"], values, color=["#326b9c", "#dc8b33"], width=0.6)
        ax.bar_label(bars, fmt="%.4f", padding=4, fontsize=10)
        ax.set_ylim(0, max(values) * 1.25)
        ax.set_ylabel("Variance contribution (pp²)", fontsize=10)
        ax.set_title(
            f"{name}: primary budget {budget}\n"
            f"Half minus full variance = {row['half_minus_full_variance'] * 10000:+.4f}"
        )
        ax.grid(axis="y", alpha=0.2)
    for name, color in [("ChildPlay", "#326b9c"), ("UCO", "#dc8b33")]:
        rows = [r for r in result["rows"] if r["dataset"] == name]
        axes[2].plot(
            [5, 10, 20, 40],
            [r["exact_RMSE_ratio_half_over_full"] for r in rows],
            "o-",
            color=color,
            label=name,
        )
    axes[2].axhline(1, color="black", linewidth=1, linestyle=":")
    axes[2].set_xticks([5, 10, 20, 40])
    axes[2].set_xlabel("Nominal label budget (%)")
    axes[2].set_ylabel("Half/full exact design RMSE ratio")
    axes[2].set_title("Two fixed weights; no search")
    axes[2].legend()
    axes[2].grid(alpha=0.2)
    fig.suptitle(
        "Why the fixed half-weight comparison reverses\nV(0.5) - V(1) = B - 0.75 C", fontsize=15
    )
    fig.text(
        0.5,
        0.025,
        "Post-hoc description of locked allocations and finite populations. "
        "No new query, model fit or weight search.\nDifferent datasets, backbone-family exposure "
        "and upstream geometry preparation prevent a causal dataset/prevalence claim.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.12, 1, 0.86))
    path = ROOT / "reports/course-project/variance-explanation-m.png"
    fig.savefig(path, dpi=160)
    fig.savefig(path.with_suffix(".pdf"))
    print(path)


if __name__ == "__main__":
    main()
