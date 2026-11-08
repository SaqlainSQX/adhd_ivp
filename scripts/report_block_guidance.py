"""Aggregate G2 results and registered uniform-block comparisons after verification."""

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

root = Path("outputs/experiments/block-guidance-g2-20261108-v1")
pilot = Path("outputs/experiments/block-g-20261108-v1")
out = Path("reports/course-project/block-guidance-g2")
out.mkdir(parents=True, exist_ok=True)
r = json.loads((root / "result.json").read_text())
check = json.loads((root / "independent-validation.json").read_text())
assert (
    check["status"] == "passed"
    and check["result_sha256"] == hashlib.sha256((root / "result.json").read_bytes()).hexdigest()
)
lock = json.loads((root / "policy-lock.json").read_text())
data = pd.read_csv(root / "draw-results.csv")
uniform = pd.read_csv(pilot / "draw-results.csv")
u = json.loads((pilot / "result.json").read_text())
truth = r["reference_prevalence"]
comparisons = {}
for length in [1, 2, 5, 10]:
    for budget in [516, 1032, 2063, 4126]:
        base = (
            uniform[(uniform.length == length) & (uniform.weight == 1) & (uniform.budget == budget)]
            .sort_values("draw")
            .prevalence.to_numpy()
            - truth
        )
        for name in ["Q", "S", "T"]:
            subset = data[
                (data.length == length) & (data.policy == name) & (data.budget == budget)
            ].sort_values("draw")
            err = subset.prevalence.to_numpy() - truth
            assert (
                abs(
                    subset.labels.mean()
                    - r["results"][f"L{length}-{name}-b{budget}"]["mean_labels"]
                )
                < 1e-10
            )
            index = np.random.default_rng(400008).integers(1000, size=(2000, 1000))
            ratios = np.sqrt((err[index] ** 2).mean(axis=1) / (base[index] ** 2).mean(axis=1))
            comparisons[f"L{length}-{name}-b{budget}/uniform"] = dict(
                rmse_ratio=float(np.sqrt(np.mean(err**2) / np.mean(base**2))),
                draw_bootstrap_95pct=np.quantile(ratios, [0.025, 0.975]).tolist(),
                seed=400008,
                resamples=2000,
                scope="Aligned draw IDs with different registered streams; "
                "fixed corpus, not source resampling",
            )
extra = dict(
    complete=True,
    comparisons=comparisons,
    pilot_result_sha256=hashlib.sha256((pilot / "result.json").read_bytes()).hexdigest(),
    result_sha256=hashlib.sha256((root / "result.json").read_bytes()).hexdigest(),
)
dest = root / "uniform-comparisons.json"
if dest.exists():
    assert json.loads(dest.read_text()) == extra
else:
    dest.write_text(json.dumps(extra, indent=2) + "\n")
fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), layout="constrained")
lengths = [1, 2, 5, 10]
for name, color in [("Q", "#d05e28"), ("S", "#184e77"), ("T", "#397f5b")]:
    values = [r["results"][f"L{length}-{name}-b1032"] for length in lengths]
    axes[0].plot(lengths, [v["rmse_pp"] for v in values], "-o", color=color, label=name)
    axes[1].plot(lengths, [v["normal_coverage"] for v in values], "-o", color=color)
    axes[2].plot(
        [5, 10, 20, 40],
        [r["results"][f"L10-{name}-b{b}"]["normal_coverage"] for b in [516, 1032, 2063, 4126]],
        "-o",
        color=color,
    )
axes[0].plot(
    lengths,
    [u["results"][f"L{length}-w1-b1032"]["rmse_pp"] for length in lengths],
    "--o",
    color="#777777",
    label="G1 uniform",
)
axes[0].set(
    title="Point accuracy at expected B1,032",
    ylabel="RMSE (percentage points)",
    xlabel="Block length",
    xticks=lengths,
)
axes[1].set(
    title="Normal coverage at expected B1,032",
    ylabel="Empirical coverage",
    xlabel="Block length",
    xticks=lengths,
    ylim=(0, 1.025),
)
axes[2].set(
    title="Length10: normal coverage across budgets",
    ylabel="Empirical coverage",
    xlabel="Expected unique-label budget (%)",
    xticks=[5, 10, 20, 40],
    ylim=(0, 1.025),
)
for ax in axes[1:]:
    ax.axhline(0.95, color="black", ls="--", lw=1)
for ax in axes:
    ax.grid(alpha=0.2)
fig.suptitle(
    "Frozen block guidance | Q native score, S static error, T temporal error |1,000 draws"
)
fig.legend(*axes[0].get_legend_handles_labels(), loc="outside lower center", ncol=4, frameon=False)
for ext in ["png", "svg"]:
    fig.savefig(out / f"guidance-accuracy-coverage.{ext}", dpi=160, bbox_inches="tight")
plt.close(fig)
primary = r["primary"]
lines = [
    "# G2: frozen-score block guidance",
    "",
    f"Primary T/S RMSE ratio at L5/B1032: {primary['rmse_ratio']:.6f} "
    f"({(primary['rmse_ratio'] - 1) * 100:.2f}% higher error), Monte Carlo95% range "
    f"{primary['draw_bootstrap_95pct']}. The registered descriptive10% gain threshold "
    "is not met. No temporal improvement is claimed. All point estimates use lambda1.",
    "",
    "Q uses native q block sums; S/T use sums of frozen static/temporal signed-error "
    "scores, with source-OOF scores for training cuts. No new model was fitted. "
    "All lengths and policies were fixed before outcomes; alpha was selected on "
    "validation only. The repeatedly inspected test corpus remains exploratory.",
    "",
    "| Length/policy | Validation-selected alpha |",
    "| --- | ---: |",
]
for key, c in lock["selected"].items():
    lines.append(f"| {key} | {c['alpha']} |")
lines += [
    "",
    "| L | Policy | Expected B | RMSE pp | Bias pp | Mean labels | Label5–95% | "
    "Mean blocks | Normal coverage | Bounded coverage | Bounded width pp |",
    "| ---: | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |",
]
for length in lengths:
    for name in ["Q", "S", "T"]:
        for budget in [516, 1032, 2063, 4126]:
            s = r["results"][f"L{length}-{name}-b{budget}"]
            q = s["label_quantiles"]
            lines.append(
                f"| {length} | {name} | {budget} | {s['rmse_pp']:.4f} | {s['bias_pp']:.4f} "
                f"| {s['mean_labels']:.2f} | [{q[1]:.0f},{q[3]:.0f}] | {s['mean_blocks']:.2f} "
                f"| {s['normal_coverage']:.3f} | {s['bounded_coverage']:.3f} | "
                f"{s['bounded_width_pp']:.3f} |"
            )
lines += [
    "",
    "## Same-length uniform comparison at primary expected budget",
    "",
    "| L | Policy | RMSE ratio to G1 uniform | Draw-bootstrap95% range |",
    "| ---: | --- | ---: | --- |",
]
for length in lengths:
    for name in ["Q", "S", "T"]:
        c = comparisons[f"L{length}-{name}-b1032/uniform"]
        lines.append(
            f"| {length} | {name} | {c['rmse_ratio']:.4f} | "
            f"{[round(x, 4) for x in c['draw_bootstrap_95pct']]} |"
        )
lines += [
    "",
    "![Accuracy and coverage](guidance-accuracy-coverage.png)",
    "",
    "Guidance improves on uniform contiguous-block sampling at the primary budget, "
    "but that does not establish an advantage for long blocks over frame queries. "
    "Compare each L>1 with its corresponding G2 L1 control using the retained "
    "aggregate ratios. Native q remains an essential control against attributing "
    "its stratification benefit to a temporal error learner.",
    "",
    "Budgets match expected unique-frame labels; random block counts and partial "
    "blocks cause actual costs to vary. Minimum2 blocks per noncensus stratum is "
    "shared across G2 lengths. G2 L1 differs from the original main exact-budget "
    "frame design with minimum20; it does not replace or re-evaluate that main study.",
    "",
    "Normal coverage fails severely at some high-budget settings (including L10). "
    "The separately reported Hoeffding residual-total reference remains conservative "
    "and broad. It is not a binary hypergeometric interval, and neither interval "
    "family changes the retained point estimate. No measured annotation-time or "
    "unseen-source/clinical generalization claim follows from query-task counts.",
    "",
    f"All{r['method_draws']:,} test evaluations and3,600 validation candidate draws "
    "passed separate replay/recomputation, including public geometry, frozen "
    "OOF/fitted scores, training moments, alpha selection, FPC variances, bounded "
    "endpoints, costs, summaries and112 stored bootstrap comparisons. Additional "
    "registered same-length uniform comparisons use the saved G1 draws.",
    "",
    "Protocol: docs/X01_BLOCK_GUIDANCE_G2.md. CPU commands: "
    "scripts/run_block_guidance.py and scripts/validate_block_guidance.py; plotting "
    "environment: scripts/report_block_guidance.py. Existing numerical/verification "
    "roots refuse overwrite; reproduction needs a new versioned config/output.",
]
(out / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
for name in [
    "result.json",
    "registration.json",
    "training-policies.json",
    "policy-lock.json",
    "independent-validation.json",
    "uniform-comparisons.json",
]:
    Path(f"docs/research/g2-{name}").write_text((root / name).read_text(), encoding="utf-8")
print(f"G2 report complete; primary T/S ratio{primary['rmse_ratio']:.6f}.")
