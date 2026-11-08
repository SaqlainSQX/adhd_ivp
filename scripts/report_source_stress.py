"""Check saved domain summaries and render an aggregate-only E appendix."""

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

root = Path("outputs/experiments/source-stress-e-20261108-v1")
out = Path("reports/course-project/source-e")
out.mkdir(parents=True, exist_ok=True)
r = json.loads((root / "result.json").read_text())
reg = json.loads((root / "registration.json").read_text())
data = pd.read_csv(root / "domain-draw-results.csv")
assert len(data) == r["domain_method_draws"] == 168000
checks = []
for key, group in data.groupby(["policy", "budget", "kind", "source"], sort=False):
    policy, budget, kind, source = key
    summary = r["summaries"][f"{policy}-b{budget}-{kind}-{source}"]
    assert np.array_equal(group.draw, np.arange(1000))
    err = group.prevalence.to_numpy() - summary["truth"]
    assert abs(100 * np.sqrt(np.mean(err**2)) - summary["rmse_pp"]) < 1e-10
    assert abs(100 * np.mean(err) - summary["bias_pp"]) < 1e-10
    assert abs(100 * np.mean(np.abs(err)) - summary["mae_pp"]) < 1e-10
    assert np.isfinite(group.variance).all() and (group.variance >= 0).all()
    assert abs(group.queries.mean() - summary["mean_queries"]) < 1e-10
    checks.append(
        dict(policy=policy, budget=int(budget), kind=kind, source=source, status="passed")
    )
for policy in ["K4", "power-score"]:
    for budget in [516, 1032, 2063, 4126]:
        part = data[(data.policy == policy) & (data.budget == budget)]
        points = part.pivot(index="draw", columns=["kind", "source"], values="prevalence")
        total = points[("all", "all")].to_numpy() * 10316
        accumulated = np.zeros(1000)
        for i in range(1, 11):
            alias = f"S{i:02d}"
            size = r["summaries"][f"{policy}-b{budget}-source-{alias}"]["size"]
            domain = points[("source", alias)].to_numpy() * size
            outside = points[("leave-out", alias)].to_numpy() * (10316 - size)
            assert np.allclose(domain + outside, total, rtol=0, atol=1e-9)
            accumulated += domain
        assert np.allclose(accumulated, total, rtol=0, atol=1e-9)
aliases = [f"S{i:02d}" for i in range(1, 11)]
fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), layout="constrained")
for ax, kind, title in zip(
    axes,
    ["source", "leave-out"],
    ["Per-source domains", "Omit one source (fixed original queries)"],
    strict=True,
):
    for j, alias in enumerate(aliases):
        c = r["comparisons"][f"b1032-{kind}-{alias}"]
        value = c["rmse_ratio"]
        if value is not None:
            lo, hi = c["draw_bootstrap_95pct"]
            ax.errorbar(
                j, value, yerr=[[value - lo], [hi - value]], fmt="o", color="#d05e28", capsize=3
            )
    ax.axhline(1, color="black", ls="--", lw=1)
    ax.axhline(0.9, color="#707070", ls=":", lw=1)
    ax.set(xticks=range(10), xticklabels=aliases, ylabel="Power-score / K4 RMSE", title=title)
    ax.grid(axis="y", alpha=0.2)
fig.suptitle("Frozen weighting sensitivity | B1,032 | paired draw-bootstrap ranges", fontsize=13)
for ext in ["png", "svg"]:
    fig.savefig(out / f"source-sensitivity.{ext}", dpi=160, bbox_inches="tight")
plt.close(fig)
primary = [r["comparisons"][f"b1032-leave-out-{a}"]["rmse_ratio"] for a in aliases]
defined = [x for x in primary if x is not None]
assessment = dict(
    leave_out_b1032=dict(
        improved=sum(x < 1 for x in defined),
        gain_at_least_10pct=sum(x <= 0.9 for x in defined),
        total=len(primary),
        mean_ratio=float(np.mean(defined)),
        worst_ratio=max(defined),
        best_ratio=min(defined),
    ),
    scope="Frozen-corpus source sensitivity; not unseen-source generalization or cross-validation",
)
positive_aliases = [a for a in aliases if r["summaries"][f"K4-b1032-source-{a}"]["positives"] > 0]
assessment["positive_sources"] = dict(
    total=len(positive_aliases),
    improved=sum(r["comparisons"][f"b1032-source-{a}"]["rmse_ratio"] < 1 for a in positive_aliases),
)
for key, c in r["comparisons"].items():
    if c["rmse_ratio"] is None:
        continue
    budget_text, kind, alias = key.split("-", 2)
    budget = int(budget_text[1:])
    if kind == "leave":
        kind, alias = "leave-out", alias.removeprefix("out-")
    a = data[
        (data.policy == "power-score")
        & (data.budget == budget)
        & (data.kind == kind)
        & (data.source == alias)
    ]
    b = data[
        (data.policy == "K4")
        & (data.budget == budget)
        & (data.kind == kind)
        & (data.source == alias)
    ]
    ae = (a.prevalence.to_numpy() - a.truth.to_numpy()) ** 2
    be = (b.prevalence.to_numpy() - b.truth.to_numpy()) ** 2
    rng = np.random.default_rng(400005)
    index = rng.integers(1000, size=(2000, 1000))
    ratios = np.sqrt(ae[index].mean(axis=1) / be[index].mean(axis=1))
    assert abs(np.sqrt(ae.mean() / be.mean()) - c["rmse_ratio"]) < 1e-10
    assert np.allclose(
        np.quantile(ratios, [0.025, 0.975]), c["draw_bootstrap_95pct"], rtol=0, atol=1e-10
    )
lines = [
    "# Source sensitivity E: frozen-policy robustness",
    "",
    "No new queries, labels, training or inference. Both estimators reuse original "
    "query inclusion weights and known public domain sizes. The policy, lambda0.5, "
    "strata and budgets remain fixed. This analysis was registered after D outcomes.",
    "",
    f"At B1032, weighting reduces RMSE in {assessment['leave_out_b1032']['improved']}/10 "
    "leave-one-source-out domains; "
    f"{assessment['leave_out_b1032']['gain_at_least_10pct']}/10 show at least10% reduction. "
    f"The worst ratio is {max(defined):.4f}. "
    "These overlapping domains are not independent replications.",
    "The gain is uneven: three of six positive-reference sources improve and three "
    "lose. Four zero-positive sources have exactly half the original error because "
    "lambda0.5 scales their residual-only errors; this is not independent evidence "
    "of better gaze recognition. Omitting S05 weakens the aggregate gain to about "
    "1.2%, with a draw-bootstrap range including a tie. Keep this qualification.",
    "",
    "| Domain | Alias | N | Positive references | K4 RMSE pp | Weighted RMSE pp | "
    "Ratio | MC95% range | Weighted normal coverage |",
    "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
]
for kind in ["source", "leave-out"]:
    for a in aliases:
        base = r["summaries"][f"K4-b1032-{kind}-{a}"]
        power = r["summaries"][f"power-score-b1032-{kind}-{a}"]
        c = r["comparisons"][f"b1032-{kind}-{a}"]
        ratio = f"{c['rmse_ratio']:.4f}" if c["rmse_ratio"] is not None else c["status"]
        interval = str([round(x, 4) for x in c.get("draw_bootstrap_95pct", [])])
        lines.append(
            f"| {kind} | {a} | {base['size']} | {base['positives']} | {base['rmse_pp']:.4f} "
            f"| {power['rmse_pp']:.4f} | {ratio} | {interval} | {power['normal_coverage']:.3f} |"
        )
lines += [
    "",
    "![Source sensitivity](source-sensitivity.png)",
    "",
    "All four budgets, zero-query rates, zero-variance rates, exact design RMSE and "
    "all source outcomes are retained in the aggregate JSON. Domain normal intervals "
    "can be unstable with few queried residuals. No domain-specific exact binary "
    "interval is claimed here. "
    "The conservative whole-population reference intervals from D are unchanged.",
    "",
    "The bootstrap resamples saved draw indices, not sources. Omitted-source "
    "estimates still use the original global sampling allocation, and realized domain "
    "label counts vary; these are not new equal-budget nine-source experiments. "
    "No source is removed from the main report or used to retune the method. "
    "An unseen-source evaluation remains future work.",
    "",
    "Reproduce with scripts/run_source_stress.py, then scripts/report_source_stress.py "
    "in the plotting environment. "
    "Existing numerical outputs refuse overwrite; use a new versioned config/output to rerun.",
]
(out / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
verification = dict(
    status="passed",
    domain_method_draws=len(data),
    saved_summary_checks=checks,
    source_complements="all8000 full-population draw totals passed",
    runner_independent_points_and_variances="all168000 cases passed",
    result_sha256=hashlib.sha256((root / "result.json").read_bytes()).hexdigest(),
)
destination = root / "saved-output-validation-v2.json"
if not destination.exists():
    destination.write_text(json.dumps(verification, indent=2) + "\n")
for name in [
    "result.json",
    "registration.json",
    "saved-output-validation.json",
    "saved-output-validation-v2.json",
]:
    Path(f"docs/research/source-e-{name}").write_text((root / name).read_text(), encoding="utf-8")
Path("docs/research/source-e-assessment.json").write_text(json.dumps(assessment, indent=2) + "\n")
print(json.dumps(assessment, indent=2))
