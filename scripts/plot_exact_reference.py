"""Show the coverage/width cost of the registered exact binary reference."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--input",
    type=Path,
    default=Path(
        "outputs/experiments/strengthening-20261107-v1/B2b-exact-reference-v2/result.json"
    ),
)
parser.add_argument("--output", type=Path, default=Path("reports/course-project"))
args = parser.parse_args()
result = json.loads(args.input.read_text())
if not result["complete"]:
    raise ValueError("Require a completed, checked exact reference run")
methods = ["M3", "M4", "q-quartiles", "entropy-quartiles"]
labels = ["Static\n(main)", "Temporal\n(main)", "Score\n(exploratory)", "Entropy\n(exploratory)"]
fig, axes = plt.subplots(2, 2, figsize=(11, 7), layout="constrained")
for row, budget in enumerate([1032, 4126]):
    summaries = [result["results"][f"{method}-b{budget}"] for method in methods]
    for col, field in enumerate(["coverage", "mean_width_pp"]):
        ax = axes[row, col]
        normal = [s["normal"][field] * (100 if col == 0 else 1) for s in summaries]
        exact = [s[field] * (100 if col == 0 else 1) for s in summaries]
        x = np.arange(len(methods))
        ax.bar(x - 0.18, normal, width=0.36, color="#285f86", label="Original normal")
        ax.bar(x + 0.18, exact, width=0.36, color="#2c8175", label="Exact binary reference")
        ax.set_xticks(x, labels, fontsize=9)
        ax.set_title(f"{budget:,} labels per audit")
        ax.set_ylabel("Coverage (%)" if col == 0 else "Mean width (pp; log scale)")
        if col == 0:
            ax.axhline(95, color="#777", linestyle="--", linewidth=1)
            ax.set_ylim(0, 105)
        else:
            ax.set_yscale("log")
        ax.grid(axis="y", alpha=0.18)
        ax.set_axisbelow(True)
axes[0, 0].legend(fontsize=8, loc="lower left")
fig.suptitle(
    "Exact binary references improve coverage at a substantial width cost\n"
    "Existing labels reused; reference intervals need not center on residual estimates"
)
args.output.mkdir(parents=True, exist_ok=True)
for ext in ["png", "svg"]:
    path = args.output / f"exact-reference-intervals.{ext}"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    if ext == "svg":
        path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
plt.close(fig)
print(args.output / "exact-reference-intervals.png")
