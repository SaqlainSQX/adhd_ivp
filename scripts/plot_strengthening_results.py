"""Export aggregate control and interval figures from completed registered results."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--root", type=Path, default=Path("outputs/experiments/strengthening-20261107-v1")
)
parser.add_argument("--main", type=Path, default=Path("docs/research/main-course-results.json"))
parser.add_argument("--output", type=Path, default=Path("reports/course-project"))
args = parser.parse_args()
main = json.loads(args.main.read_text())
simple = json.loads((args.root / "B1-simple-controls/result.json").read_text())
coverage = json.loads((args.root / "B2-coverage/result.json").read_text())
if not simple["complete"] or not coverage["complete"]:
    raise ValueError("Only completed results may be plotted")
args.output.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
budgets = [516, 1032, 2063, 4126]
series = [
    ("M2", "Uniform residual", "#8b969d"),
    ("M3", "Learned static (main)", "#285f86"),
    ("M4", "Learned temporal (main)", "#ce7950"),
    ("q-quartiles", "Score quartiles (exploratory)", "#2c8175"),
    ("entropy-quartiles", "Entropy quartiles (exploratory)", "#919454"),
]


def save(fig, name):
    for extension in ["png", "svg"]:
        path = args.output / f"{name}.{extension}"
        fig.savefig(path, dpi=220, bbox_inches="tight")
        if extension == "svg":
            path.write_text("\n".join(s.rstrip() for s in path.read_text().splitlines()) + "\n")
    plt.close(fig)


fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), layout="constrained")
values, labels, colors = [], [], []
for key, label, color in series:
    source = main if key.startswith("M") else simple
    errors = [source["results"][f"{key}-b{b}"]["rmse_pp"] for b in budgets]
    values.append(errors[1])
    labels.append(label.replace(" (", "\n("))
    colors.append(color)
    axes[1].plot(budgets, errors, "o-", color=color, label=label, linewidth=1.8)
bars = axes[0].bar(range(len(values)), values, color=colors)
axes[0].bar_label(bars, fmt="%.4f", padding=4)
axes[0].set_xticks(range(len(values)), labels, rotation=25, ha="right", fontsize=8)
axes[0].set_ylim(0, max(values) * 1.15)
axes[0].set_title("Primary budget: 1,032 labels")
axes[0].set_ylabel("RMSE (percentage points)")
axes[1].set_yscale("log")
axes[1].set_title("Same frozen policy across budgets")
axes[1].set_xlabel("Revealed labels per audit")
axes[1].set_ylabel("RMSE (percentage points; log scale)")
axes[1].legend(fontsize=8)
for ax in axes:
    ax.grid(axis="y", alpha=0.2)
    ax.set_axisbelow(True)
fig.suptitle(
    "Simple controls challenge the need for learned guidance\n"
    "Exploratory extension; 1,000 draws; fixed available corpus"
)
save(fig, "simple-guidance-controls")

intervals = [
    ("normal", "Original normal", "#285f86", "-"),
    ("student_t", "Student-t (approx.)", "#ce7950", "--"),
    ("validation_calibrated", "Validation calibrated", "#2c8175", "-."),
    ("exact_variance_normal_DIAGNOSTIC_ONLY", "Exact variance: diagnostic only", "#8c78a6", ":"),
]
fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), layout="constrained")
for ax, method in zip(axes, ["M3", "M4"], strict=True):
    for key, label, color, style in intervals:
        values = [
            100 * coverage["results"][f"{method}-b{b}"]["intervals"][key]["coverage"]
            for b in budgets
        ]
        ax.plot(budgets, values, marker="o", linestyle=style, label=label, color=color)
    ax.axhline(95, color="#6f7270", linewidth=1, alpha=0.6)
    ax.set_ylim(88, 98)
    ax.set_title("Static guidance (M3)" if method == "M3" else "Temporal guidance (M4)")
    ax.set_xlabel("Revealed labels per audit")
    ax.set_ylabel("Coverage (%)")
    ax.grid(alpha=0.18)
axes[1].legend(fontsize=8, loc="lower right")
fig.suptitle(
    "Simple interval adjustments do not resolve undercoverage\n"
    "Original test queries retained; exact-variance intervals are diagnostic only"
)
save(fig, "interval-strengthening")

diagnostics = np.genfromtxt(
    args.root / "B2-coverage/diagnostic-draws.csv",
    delimiter=",",
    names=True,
    dtype=None,
    encoding="utf-8",
)
fig, axes = plt.subplots(1, 2, figsize=(11, 4.3), layout="constrained")
hist_population = diagnostics[np.isin(diagnostics["budget"], [1032, 2063])]
hist_upper = np.ceil(
    np.max(hist_population["estimated_variance"] / hist_population["exact_variance"]) * 2
) / 2
for ax, method in zip(axes, ["M3", "M4"], strict=True):
    for budget, color in [(1032, "#285f86"), (2063, "#ce7950")]:
        selected = diagnostics[
            (diagnostics["method"] == method) & (diagnostics["budget"] == budget)
        ]
        ratio = selected["estimated_variance"] / selected["exact_variance"]
        ax.hist(
            ratio,
            bins=np.linspace(0, hist_upper, 50),
            density=True,
            histtype="step",
            linewidth=1.8,
            color=color,
            label=f"{budget:,} labels",
        )
    ax.axvline(1, color="#555", linestyle="--", linewidth=1)
    ax.set_title("Static guidance (M3)" if method == "M3" else "Temporal guidance (M4)")
    ax.set_xlabel("Estimated variance / exact design variance")
    ax.set_ylabel("Density")
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.18)
fig.suptitle(
    "Variance is close to correct on average but variable between draws\n"
    "Exact variance uses full test references for diagnosis only"
)
save(fig, "variance-strengthening")
print("Saved three PNG/SVG evidence figures", flush=True)
