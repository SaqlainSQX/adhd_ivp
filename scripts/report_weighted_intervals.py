"""Plot and summarize all registered interval recipes after independent checks."""

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = Path("outputs/experiments/weighted-f-20261108-v2")
out = Path("reports/course-project/weighted-f")
out.mkdir(parents=True, exist_ok=True)
r = json.loads((root / "result.json").read_text())
v = json.loads((root / "independent-validation.json").read_text())
assert v["status"] == "passed"
assert v["result_sha256"] == hashlib.sha256((root / "result.json").read_bytes()).hexdigest()
recipes = ["equal", "inverse-fraction", "inverse-sqrt-count"]
colors = ["#66717e", "#d05e28", "#347b62"]
fig, axes = plt.subplots(1, 3, figsize=(14, 4.3), layout="constrained")
for ax, name in zip(axes, ["M3", "M4", "K4"], strict=True):
    for recipe, color in zip(recipes, colors, strict=True):
        values = [
            r["results"][f"{name}-b{b}-{recipe}"]["mean_width_pp"] for b in [516, 1032, 2063, 4126]
        ]
        ax.plot([5, 10, 20, 40], values, "-o", label=recipe, color=color)
    ax.set(
        title=name,
        xlabel="Original test label budget (%)",
        ylabel="Mean reference width (pp)",
        xticks=[5, 10, 20, 40],
    )
    ax.grid(alpha=0.2)
fig.suptitle("Conservative binary reference | public error weights | same frozen queries")
fig.legend(*axes[0].get_legend_handles_labels(), loc="outside lower center", ncol=3, frameon=False)
for ext in ["png", "svg"]:
    fig.savefig(out / f"weighted-reference-width.{ext}", dpi=160, bbox_inches="tight")
plt.close(fig)
ratio = r["primary"]["mean_width_ratio"]
lines = [
    "# Public-weight exact reference intervals F",
    "",
    f"The primary interval-width ratio is {ratio:.6f}: a {(1 - ratio) * 100:.2f}% reduction, "
    "below the registered descriptive10% target. No point-estimate improvement is claimed. "
    "The original normal interval failures and equal-error references stay intact.",
    "",
    "Weighted Bonferroni error allowances are fixed from public stratum sizes/query counts. "
    "Exact hypergeometric stratum intervals plus the union bound give at least95% "
    "finite-population coverage under the stated SRS design. This is a standard "
    "construction, not a new theorem or an unseen-source validation.",
    "",
    "| Design | B | Recipe | Coverage | Mean width pp | Residual point outside rate |",
    "| --- | ---: | --- | ---: | ---: | ---: |",
]
for name in ["M3", "M4", "K4", "power-uniform"]:
    for b in [516, 1032, 2063, 4126]:
        for recipe in recipes:
            s = r["results"][f"{name}-b{b}-{recipe}"]
            lines.append(
                f"| {name} | {b} | {recipe} | {s['coverage']:.3f} | "
                f"{s['mean_width_pp']:.4f} | {s['point_outside_rate']:.3f} |"
            )
lines += [
    "",
    "![Interval widths](weighted-reference-width.png)",
    "",
    "The primary same-draw width-ratio Monte Carlo95% range is "
    f"{r['primary']['draw_bootstrap_95pct']}. The range describes simulation variability "
    "on the fixed corpus, not uncertainty about performance on new videos.",
    "",
    "At B1032 the primary score design remains broad (over8 pp). The temporal M4 "
    "inverse-fraction interval has about11% less width than its equal-error reference, "
    "but remains over9 pp wide; this is secondary and does not rescue temporal point accuracy. "
    "Uniform sampling has one stratum, so all recipes are identical as required.",
    "",
    "These binary intervals estimate the same prevalence but are not centered on the "
    "residual-correction point. They can exclude that point; no clipping or intersection "
    "with normal/equal intervals is used. Choosing a recipe after observing labels is "
    "not covered by this fixed-weight construction.",
    "",
    f"All{r['interval_cases']:,} saved integer endpoint cases passed independent allocation, "
    "endpoint/tail and saved-summary checks. Equal recipes reproduce prior exact intervals. "
    "The exhaustive synthetic tests cover all binary population totals for a small "
    "two-stratum design. No new queried labels or GPU inference were used.",
    "",
    "Protocol: docs/WEIGHTED_INTERVALS_F.md. Run scripts/run_weighted_intervals.py "
    "--config configs/weighted-intervals-f-v2.json, then scripts/validate_weighted_intervals.py "
    "in the CPU environment and scripts/report_weighted_intervals.py in the plotting environment. "
    "Existing numerical/verification outputs refuse overwrite.",
    "",
    "The failed v1 output-row container bug is retained with its log. Accepted v2 fixes "
    "only that container and adds a configuration argument; recipes/endpoints are unchanged.",
]
(out / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
for name in [
    "result.json",
    "registration.json",
    "public-allocation-lock.json",
    "independent-validation.json",
]:
    Path(f"docs/research/weighted-f-{name}").write_text((root / name).read_text(), encoding="utf-8")
print(f"F report complete; primary width reduction {(1 - ratio) * 100:.2f}%.")
