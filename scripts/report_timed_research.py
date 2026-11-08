"""Render an aggregate-only appendix after independent D verification."""

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


root = Path("outputs/experiments/timed-d-20261108-v1")
out = Path("reports/course-project/timed-d")
out.mkdir(parents=True, exist_ok=True)
r = json.loads((root / "result.json").read_text())
v = json.loads((root / "independent-validation.json").read_text())
lock = json.loads((root / "policy-lock.json").read_text())
assert v["status"] == "passed" and v["result_sha256"] == file_hash(root / "result.json")
comparison_check = json.loads((root / "comparison-validation.json").read_text())
assert comparison_check["status"] == "passed"
assert comparison_check["result_sha256"] == file_hash(root / "result.json")
names = ["K2", "K4", "K8", "K16", "power-score", "power-uniform"]
budgets = [516, 1032, 2063, 4126]
colors = ["#997a2f", "#184e77", "#397f5b", "#9467a3", "#d05e28", "#62676e"]
fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), layout="constrained")
for name, color in zip(names, colors, strict=True):
    values = [r["results"][f"{name}-b{b}"] for b in budgets]
    axes[0].plot([5, 10, 20, 40], [x["rmse_pp"] for x in values], "-o", label=name, color=color)
    axes[1].plot(
        [5, 10, 20, 40], [x["intervals"]["normal"]["coverage"] for x in values], "-o", color=color
    )
    axes[2].plot(
        [5, 10, 20, 40],
        [x["intervals"]["exact_binary_reference"]["mean_width_pp"] for x in values],
        "-o",
        color=color,
    )
axes[0].set(ylabel="RMSE (percentage points)", title="Point accuracy")
axes[1].axhline(0.95, color="black", ls="--", lw=1)
axes[1].set(ylabel="Empirical coverage", ylim=(0, 1.025), title="Normal interval (nominal 95%)")
axes[2].set(ylabel="Mean width (percentage points)", title="Exact binary reference interval")
for ax in axes:
    ax.set_xlabel("Test label budget (%)")
    ax.set_xticks([5, 10, 20, 40])
    ax.grid(alpha=0.2)
fig.suptitle(
    "Exploratory D round | 1,000 draws per setting | fixed 10,316 pair-frames", fontsize=13
)
fig.legend(*axes[0].get_legend_handles_labels(), loc="outside lower center", ncol=6, frameon=False)
for ext in ["png", "svg"]:
    fig.savefig(out / f"accuracy-coverage.{ext}", dpi=160, bbox_inches="tight")
plt.close(fig)
fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
for name in ["uniform", "K4"]:
    rows = [c for c in lock["lambda_candidates"] if c["policy"] == name]
    axes[0].plot(
        [c["weight"] for c in rows],
        [100 * np.sqrt(c["validation_mse"]) for c in rows],
        "-o",
        label=name,
    )
axes[0].set(
    xlabel="Prediction weight lambda", ylabel="Validation RMSE (pp)", title="D1 validation only"
)
axes[0].legend()
rows = list(lock["selected_alpha"].values())
axes[1].plot(
    [int(c["policy"][1:]) for c in rows], [100 * np.sqrt(c["validation_mse"]) for c in rows], "-o"
)
axes[1].set(
    xlabel="Requested score strata K",
    ylabel="Validation RMSE (pp)",
    title=f"D2 validation winner: {r['selected_k']}",
)
for ax in axes:
    ax.grid(alpha=0.2)
for ext in ["png", "svg"]:
    fig.savefig(out / f"development-selection.{ext}", dpi=160, bbox_inches="tight")
plt.close(fig)
lines = [
    "# Timed research D: results appendix",
    "",
    "Exploratory results after repeated inspection of the same test corpus. "
    "All settings were registered before these outcomes. The main submission remains frozen.",
    "",
    f"Completed {r['sampled_method_runs']:,} test method-draw evaluations, independently replayed "
    f"and recomputed; CPU run {r['elapsed_seconds']:.1f} seconds, no new GPU inference.",
    "",
    f"Validation selected weights: {r['selected_lambdas']}; D2 selected {r['selected_k']}. "
    "All four K variants are retained below. Each uses 191,956 training and "
    "25,139 reused validation labels; "
    "this excludes historical backbone supervision.",
    "",
    "| Policy | B | Bias pp | MAE pp | RMSE pp | Normal coverage | Normal width pp | "
    "Exact coverage | Exact width pp |",
    "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
]
for name in names:
    for b in budgets:
        s = r["results"][f"{name}-b{b}"]
        normal = s["intervals"]["normal"]
        exact = s["intervals"]["exact_binary_reference"]
        lines.append(
            f"| {name} | {b} | {s['bias_pp']:.4f} | {s['mae_pp']:.4f} | {s['rmse_pp']:.4f} "
            f"| {normal['coverage']:.3f} | {normal['mean_width_pp']:.4f} | "
            f"{exact['coverage']:.3f} | {exact['mean_width_pp']:.4f} |"
        )
lines += [
    "",
    "## Registered primary comparisons",
    "",
    "| Comparison at B1032 | RMSE ratio | Draw-bootstrap 95% range | "
    "Meets registered practical threshold |",
    "| --- | ---: | --- | --- |",
]
decisions = []
for name in ["power-score", r["selected_k"]]:
    c = r["comparisons"][f"{name}-b1032/K4"]
    lo, hi = c["draw_bootstrap_95pct"]
    passed = c["rmse_ratio"] <= 0.9 and hi < 1
    decisions.append(
        dict(
            c,
            policy=name,
            meets_threshold=passed,
            scope="Fixed-corpus draw-bootstrap uncertainty; shared queries for power-score/K4, "
            "common seeds with different designs for K8/K4. Not source-generalization uncertainty.",
        )
    )
    lines.append(f"| {name} / K4 | {c['rmse_ratio']:.4f} | [{lo:.4f}, {hi:.4f}] | {passed} |")
c = r["comparisons"]["power-uniform-b1032/M2"]
lo, hi = c["draw_bootstrap_95pct"]
lines += [
    f"| power-uniform / original M2 | {c['rmse_ratio']:.4f} | [{lo:.4f}, {hi:.4f}] | Secondary |",
    "",
    "The bootstrap describes simulation error on this fixed corpus, not generalization "
    "to new children/videos. Validation-selected K is the D2 endpoint even if another K "
    "looks better on test. No combined lambda/K policy was tested.",
    "D1 score/K4 and uniform/M2 use identical queried records. Across K, stream21 "
    "aligns random seeds but the designs differ. The inherited generic raw-JSON "
    "scope text saying streams differ is imprecise; the saved arrays were checked.",
    "",
    "The exact binary reference is a conservative, separately centered interval for "
    "the same finite population. It does not validate the residual-centered normal "
    "interval and may exclude the residual point estimate. Normal undercoverage, "
    "all high-budget behavior and all failed comparisons remain in the tables and aggregate JSON.",
    "",
    "A primary threshold pass is an exploratory engineering improvement, not a new "
    "statistical method or an independent replication. The original temporal-versus-static "
    "finding is unchanged. These results estimate benchmark-defined mutual looking, "
    "not ADHD diagnosis.",
    "The prior B1 score-control run reported 0.2079 pp at B1032 on stream7. "
    "This round's unweighted control is 0.2199 pp on stream21; the registered "
    "10.5% gain compares identical stream21 queries. Relative to the old simulation "
    "number, the weighted 0.1967 pp is about 5.4% lower. This is not a new dataset.",
    "A post-hoc evaluation-only calculation using full test references gives exact "
    "design RMSE 0.2160 pp for K4 and 0.1920 pp for power-score at B1032 "
    "(about 11.1% lower). This explains the fixed-population variance reduction; "
    "it does not select a new policy or establish transfer to unseen sources.",
    "",
    "![Accuracy and coverage](accuracy-coverage.png)",
    "",
    "![Development-only selection](development-selection.png)",
    "",
    "## Reproduction",
    "",
    "```powershell",
    ".venv/Scripts/python.exe scripts/run_timed_research.py",
    ".venv/Scripts/python.exe scripts/validate_timed_research.py",
    ".venv/Scripts/python.exe scripts/check_timed_comparisons.py",
    ".venv-mtgs/Scripts/python.exe scripts/report_timed_research.py",
    "```",
    "",
    "Reruns require a new versioned config/output path; existing evidence is never overwritten. "
    "Protocol: docs/TIMED_RESEARCH_D.md. Research links: docs/research/timed-d-literature.md.",
]
(out / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
tracked = Path("docs/research")
for name in [
    "result.json",
    "policy-lock.json",
    "independent-validation.json",
    "registration.json",
    "comparison-validation.json",
    "posthoc-exact-design-variance.json",
]:
    (tracked / f"timed-d-{name}").write_text((root / name).read_text(), encoding="utf-8")
(tracked / "timed-d-primary-decision.json").write_text(json.dumps(decisions, indent=2) + "\n")
evidence = {str(p).replace("\\", "/"): file_hash(p) for p in sorted(root.rglob("*")) if p.is_file()}
(tracked / "timed-d-evidence-manifest.json").write_text(json.dumps(evidence, indent=2) + "\n")
print(json.dumps(dict(primary_decisions=decisions, uniform_vs_M2=c), indent=2))
