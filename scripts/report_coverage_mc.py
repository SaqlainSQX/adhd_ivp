"""Render T's full registered coverage family from saved aggregate results."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


def main():
    rows = json.loads(Path("outputs/coverage-mc-t-v1/result.json").read_text(encoding="utf-8"))[
        "rows"
    ]
    fig, axes = plt.subplots(2, 2, figsize=(15, 12), constrained_layout=True)
    for ax, group in zip(axes.flat, ["Main", "UCO", "Q", "R"], strict=True):
        cells = [r for r in rows if r["group"] == group]
        for i, row in enumerate(cells):
            y = len(cells) - i - 1
            ax.plot([100 * v for v in row["family_interval"]], [y, y], color="#aab5bf", lw=4)
            ax.plot([100 * v for v in row["individual_interval"]], [y, y], color="#2463ad", lw=1.5)
            ax.plot(
                100 * row["coverage"],
                y,
                "D" if row["primary"] else "o",
                color="#673688" if row["primary"] else "#193a55",
                ms=4,
            )
        ax.set_yticks(range(len(cells)), [r["id"] for r in cells][::-1], fontsize=7)
        ax.axvline(95, color="#ae3d30", linestyle="--", lw=1)
        ax.set_xlim((85, 100) if group == "Main" else ((90, 100) if group == "UCO" else (-1, 101)))
        ax.set_title(group + ": coverage over fixed-corpus audit draws")
        ax.set_xlabel("Coverage probability (%)")
        ax.grid(axis="x", alpha=0.2)
    fig.suptitle(
        "Monte Carlo uncertainty in normal-interval coverage\n"
        "1000 draws/cell; exact binomial intervals. Panel x-axis ranges differ.",
        fontsize=13,
    )
    fig.legend(
        handles=[
            Line2D([0], [0], color="#2463ad", label="Individual 95%"),
            Line2D([0], [0], color="#aab5bf", lw=4, label="Bonferroni family 95% (74 cells)"),
            Line2D([0], [0], color="#ae3d30", ls="--", label="Nominal target 95%"),
        ],
        loc="outside lower center",
        ncol=3,
        fontsize=9,
    )
    target = Path("reports/course-project/coverage-mc-t")
    fig.savefig(target.with_suffix(".png"), dpi=150)
    fig.savefig(target.with_suffix(".pdf"))
    plt.close(fig)


if __name__ == "__main__":
    main()
