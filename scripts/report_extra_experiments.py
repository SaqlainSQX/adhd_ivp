"""Render the complete, independently checked round-C appendix without replacing main results."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--config", type=Path, default=Path("configs/extra-experiments-c-v1.json"))
parser.add_argument("--output", type=Path, default=Path("reports/course-project/extra-c"))
args = parser.parse_args()
config = json.loads(args.config.read_text())
root = Path(config["output"])
verification = json.loads((root / "independent-validation.json").read_text())
if verification["status"] != "passed" or verification["test_evaluations_recomputed"] != 32000:
    raise ValueError("Require independent validation of the whole registered queue")
stages = {
    stage: json.loads((root / stage / "result.json").read_text())
    for stage in ["C1-ridge", "C2-label-cost", "C3-squared-rf"]
}
main = json.loads((Path(config["main_run"]) / "evaluation/result.json").read_text())
simple = json.loads((Path(config["simple_run"]) / "result.json").read_text())
if not all(s["complete"] and s["frozen_baseline_inputs_unchanged"] for s in stages.values()):
    raise ValueError("Require all completed stages and unchanged accepted baselines")
args.output.mkdir(parents=True, exist_ok=True)
budgets = [516, 1032, 2063, 4126]
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


def save(fig, name):
    for ext in ["png", "svg"]:
        path = args.output / f"{name}.{ext}"
        fig.savefig(path, dpi=220, bbox_inches="tight")
        if ext == "svg":
            path.write_text(
                "\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n"
            )
    plt.close(fig)


fig, axes = plt.subplots(2, 2, figsize=(12, 8), layout="constrained")
for row, (stage, prefix, title) in enumerate(
    [
        ("C1-ridge", "ridge", "C1: signed-residual Ridge"),
        ("C3-squared-rf", "squared-rf", "C3: squared-residual RF"),
    ]
):
    source = stages[stage]
    entries = [
        (main, "M3", "Main static", "#285f86"),
        (main, "M4", "Main temporal", "#ce7950"),
        (simple, "q-quartiles", "Score control", "#8d9696"),
        (source, f"{prefix}-static", "New static", "#2c8175"),
        (source, f"{prefix}-temporal-w11", "New temporal", "#929454"),
    ]
    values = [s["results"][f"{key}-b1032"]["rmse_pp"] for s, key, _, _ in entries]
    bars = axes[row, 0].bar(range(5), values, color=[e[3] for e in entries])
    axes[row, 0].bar_label(bars, fmt="%.4f", padding=4, fontsize=8)
    axes[row, 0].set_xticks(range(5), [e[2].replace(" ", "\n", 1) for e in entries], fontsize=8)
    axes[row, 0].set_ylim(0, max(values) * 1.2)
    axes[row, 0].set_title(f"{title}; primary B=1,032")
    axes[row, 0].set_ylabel("RMSE (percentage points)")
    for source, key, label, color in entries:
        axes[row, 1].plot(
            budgets,
            [source["results"][f"{key}-b{b}"]["rmse_pp"] for b in budgets],
            "o-",
            color=color,
            label=label,
        )
    axes[row, 1].set_yscale("log")
    axes[row, 1].set_ylabel("RMSE (pp; log scale)")
    axes[row, 1].set_xlabel("Revealed test labels per audit")
    axes[row, 1].set_title("The same frozen policy at every budget")
    axes[row, 1].legend(fontsize=8, loc="lower left")
for ax in axes.flat:
    ax.grid(axis="y", alpha=0.18)
    ax.set_axisbelow(True)
fig.suptitle(
    "Alternative learners and score targets\n"
    "Exploratory after inspected outcomes; all losses and budgets retained"
)
save(fig, "alternative-learners")

cost = stages["C2-label-cost"]
names = [f"score-labels-{fraction:g}" for fraction in config["training_label_fractions"]]
counts = [cost["training_labels"][name] for name in names]
fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), layout="constrained")
for budget, color in zip(budgets, ["#8b969d", "#285f86", "#ce7950", "#2c8175"], strict=True):
    axes[0].plot(
        counts,
        [cost["results"][f"{name}-b{budget}"]["rmse_pp"] for name in names],
        "o-",
        color=color,
        label=f"{budget:,} test labels",
    )
axes[0].set_yscale("log")
axes[0].set_xscale("log")
axes[0].set_ylabel("RMSE (pp; log scale)")
axes[0].set_title("Training-label moment calibration")
axes[0].legend(fontsize=8)
ratios = [cost["comparisons"][f"{name}-b1032/full-labels"] for name in names]
values = np.array([r["rmse_ratio"] for r in ratios])
ci = np.array([r["draw_bootstrap_95pct"] for r in ratios])
axes[1].errorbar(
    counts,
    values,
    yerr=np.stack([values - ci[:, 0], ci[:, 1] - values]),
    fmt="o-",
    color="#285f86",
    capsize=4,
)
axes[1].axhline(1, color="#777", linestyle="--", linewidth=1, label="Full-label reference")
axes[1].axhline(1.1, color="#ce7950", linestyle=":", label="Registered 10% loss margin")
axes[1].set_xscale("log")
axes[1].set_ylabel("Primary RMSE / full-label RMSE")
axes[1].set_title("B=1,032; draw-bootstrap MC intervals")
axes[1].legend(fontsize=8)
for ax in axes:
    ax.set_xticks(
        counts,
        [
            f"{n:,}\n{int(f * 100)}%"
            for n, f in zip(counts, config["training_label_fractions"], strict=True)
        ],
        fontsize=8,
    )
    ax.set_xlabel("Training labels used for residual moments")
    ax.grid(alpha=0.18)
fig.suptitle(
    "Can score guidance use fewer development labels?\n"
    "25,139 validation labels still reused; public training scores remain available"
)
save(fig, "training-label-cost")

entries = []
for stage in stages:
    for name in stages[stage]["training_labels"]:
        entries.append((name, stages[stage]["results"][f"{name}-b1032"]))
fig, axes = plt.subplots(1, 2, figsize=(12, 5.5), layout="constrained")
ypos = np.arange(len(entries))
for ax, field, label in [
    (axes[0], "coverage", "Coverage (%)"),
    (axes[1], "mean_width_pp", "Mean width (pp; log scale)"),
]:
    for shift, kind, color, title in [
        (-0.18, "normal", "#285f86", "Original normal"),
        (0.18, "exact_binary_reference", "#2c8175", "Exact binary reference"),
    ]:
        values = [
            r["intervals"][kind][field] * (100 if field == "coverage" else 1) for _, r in entries
        ]
        ax.barh(ypos + shift, values, height=0.36, color=color, label=title)
    ax.set_yticks(
        ypos, [name.replace("score-labels-", "score fraction ") for name, _ in entries], fontsize=8
    )
    ax.invert_yaxis()
    ax.set_xlabel(label)
    ax.grid(axis="x", alpha=0.18)
    ax.set_axisbelow(True)
axes[0].axvline(95, color="#777", linestyle="--", linewidth=1)
axes[0].set_xlim(0, 105)
axes[0].legend(fontsize=8, loc="lower left")
axes[1].set_xscale("log")
fig.suptitle(
    "Primary-budget uncertainty: report width alongside coverage\n"
    "Exact binary references can have a different center from the residual estimate"
)
save(fig, "primary-coverage-width")

text = """# Additional exploratory results: round C

Registered after the completed course study and strengthening round. This is
an appendix on an already inspected fixed test corpus, not independent
confirmation or a replacement for the locked main comparison. All registered
variants, budgets, losses and uncertainty limitations are retained.

## Recommended use in the course project

Keep the accepted main comparison and add the calibration-label cost curve as
an exploratory result. Five percent of training labels (9,599) gives primary
RMSE 0.2120 pp versus 0.2148 with all 191,956 labels; the ratio is 0.9867
[0.9422,1.0347] on this fixed corpus. The full 25,139 validation labels and
pretrained backbone remain in use. This meets the registered practical cost
signal, but does not prove transfer or real annotation-time savings.

None of the new learned variants meets the registered 10% primary RMSE gain
versus the frozen score control. Ridge-static is approximately tied with it;
the squared-residual RF has worse primary point error. Keep these alternatives
in the appendix rather than recasting a secondary-budget gain as a primary win.

## Alternative learners and score targets

Every method shares frozen MTGS predictions, the eligible population, estimator
and exact annotation budgets. Ridge uses training-fold-only StandardScaler and
fixed alpha=1 regularization. The squared-residual RF changes its score-learning
target; allocation moments remain centered signed-residual SDs. Models use the
original five source folds, validation-only allocation selection and fixed
settings across test budgets.

RMSE (percentage points):

| Method | 516 labels | 1,032 labels | 2,063 labels | 4,126 labels |
| --- | ---: | ---: | ---: | ---: |
"""
all_methods = [
    (main, "M3", "Main learned static"),
    (main, "M4", "Main learned temporal"),
    (simple, "q-quartiles", "Frozen score control"),
]
all_methods += [
    (source, name, name)
    for stage, source in stages.items()
    if stage != "C2-label-cost"
    for name in source["training_labels"]
]
for source, name, label in all_methods:
    text += (
        "| "
        + label
        + " | "
        + " | ".join(f"{source['results'][f'{name}-b{b}']['rmse_pp']:.4f}" for b in budgets)
        + " |\n"
    )
text += (
    "\n![Alternative learners](alternative-learners.png)\n\n"
    "Primary ratios against the frozen score control "
    "(Monte Carlo 95% draw-bootstrap intervals):\n\n"
)
for stage, source in stages.items():
    if stage == "C2-label-cost":
        continue
    for name in source["training_labels"]:
        ratio = source["comparisons"][f"{name}-b1032/q-quartiles"]
        low, high = ratio["draw_bootstrap_95pct"]
        text += (
            f"- {name}: {ratio['rmse_ratio']:.4f} [{low:.4f}, {high:.4f}]. "
            f"Registered 10% point-improvement threshold met: {ratio['rmse_ratio'] <= 0.9}.\n"
        )
text += """

These are descriptive exploratory comparisons without multiplicity-adjusted
discovery claims. A favorable secondary budget is not a new primary endpoint.

## Development-label calibration cost

Public score cut points remain frozen. Training labels were sampled within
source under a deterministic nested permutation before their values were read.
Only the sampled labels estimate residual moments. All variants reuse 25,139
validation labels; this is masking of existing labels, not a real annotation
purchase or a cold-start study. The 100% moments reproduce the B1 policy; a
different registered query stream means its Monte Carlo result need not match B1.
These costs cover downstream audit calibration only: the frozen pretrained
MTGS backbone and its historical supervision remain unchanged and are not
included in the training-plus-validation totals below.

| Fraction | Train labels | Train + validation | RMSE (pp) | Ratio/full and MC interval |
| --- | ---: | ---: | ---: | --- |
"""
for name, fraction in zip(names, config["training_label_fractions"], strict=True):
    ratio = cost["comparisons"][f"{name}-b1032/full-labels"]
    low, high = ratio["draw_bootstrap_95pct"]
    count = cost["training_labels"][name]
    text += (
        f"| {fraction * 100:g}% | {count:,} | {count + cost['validation_labels_reused']:,} | "
        f"{cost['results'][f'{name}-b1032']['rmse_pp']:.4f} | "
        f"{ratio['rmse_ratio']:.4f} [{low:.4f}, {high:.4f}] |\n"
    )
text += "\n![Training-label cost](training-label-cost.png)\n\n"
text += (
    "Non-monotonic results can reflect moment shrinkage, source shift and Monte Carlo "
    "variation; fewer labels are not intrinsically more informative. "
    "Validation costs must remain in any cost claim.\n\n## Coverage and width\n\n"
)
text += (
    "| Policy | Normal coverage, 10% | Binary coverage, 10% | Mean widths (pp) | Normal, 40% |\n"
    "| --- | ---: | ---: | --- | ---: |\n"
)
for _stage, source in stages.items():
    for name in source["training_labels"]:
        r = source["results"][f"{name}-b1032"]
        normal, exact = r["intervals"]["normal"], r["intervals"]["exact_binary_reference"]
        c40 = source["results"][f"{name}-b4126"]["intervals"]["normal"]["coverage"]
        text += (
            f"| {name} | {100 * normal['coverage']:.1f}% | {100 * exact['coverage']:.1f}% | "
            f"{normal['mean_width_pp']:.4f} / {exact['mean_width_pp']:.4f} | {100 * c40:.1f}% |\n"
        )
text += """

![Coverage and width](primary-coverage-width.png)

The exact binary reference uses only sampled binary successes and fixed stratum
sizes, with Bonferroni-adjusted hypergeometric inversions. It ignores q, can be
wide and is not generally centered on the retained residual point estimate.
Point-outside-reference rates and all bounded interval metrics are retained in
the aggregate JSON. Normal-interval failures are not hidden by reporting only
point-error improvements or primary-budget coverage.

Some secondary-budget failures are severe: squared-RF-static normal coverage
is 79.9% at 20% labels, Ridge-temporal is 74.2% at 40%, and the score cost-curve
variants are around 44-48% at 40%. Low point error does not remove these limits.

There is a secondary width tradeoff: squared-RF-static has a 2.586 pp primary
exact-reference width versus 8.706 pp for the full-label C2 score policy, but
worse point RMSE (0.2619 versus 0.2148 pp). This interval-width observation is
not the registered primary efficacy endpoint or a reason to replace its result.

## Verification, costs and interpretation

All 32,000 new test evaluations and 2,400 validation candidate evaluations were
independently replayed and recomputed, including selection, exact budgets,
finite-population variances, intervals and RMSEs. Source-nested training subsets
were independently reconstructed. Original main/B1 results, policies, source
folds and prediction caches remain unchanged. No further GPU inference or new
human annotation was used.

"""
for stage, source in stages.items():
    text += (
        f"- {stage}: {source['sampled_method_runs']:,} test evaluations, "
        f"{source['elapsed_seconds']:.1f} seconds including fitting, selection and evaluation.\n"
    )
text += """

The existing course submission remains valid whether or not these variants
improve it. Practical signals were registered before this round's outcomes:
10% primary RMSE improvement versus the score control, or a reduced-training-
label calibration within 10% of its own full-label reference. Report uncertainty
and all tradeoffs rather than turning either threshold into a claim of general
superiority. The same inspected corpus, three validation sources, historical
backbone exposure and repeated exploratory comparisons limit inference.

Stop after this registered queue. No additional learner/window search was
launched to rescue a negative outcome. The contribution remains a reproducible
audit-method comparison and cost/uncertainty analysis, not a new gaze backbone,
clinical screening system or new statistical theorem.

Protocol: [round C](../../../docs/EXTRA_EXPERIMENTS_C.md). Numerical source
artifacts and validation: see the
[evidence manifest](../../../docs/research/extra-c-evidence-manifest.json)
and the ignored run root.
"""
(args.output / "results.md").write_text(text, encoding="utf-8", newline="\n")
print(args.output / "results.md")
