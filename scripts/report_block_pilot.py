"""Check saved G1 results and plot statistical cost/precision tradeoffs."""

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

root = Path("outputs/experiments/block-g-20261108-v1")
out = Path("reports/course-project/block-g")
out.mkdir(parents=True, exist_ok=True)
r = json.loads((root / "result.json").read_text())
reg = json.loads((root / "registration.json").read_text())
assert (
    r["complete"]
    and reg["implementation_sha256"]
    == hashlib.sha256(Path("src/gaze_audit/block_pilot.py").read_bytes()).hexdigest()
)
inventory = json.loads((root / "public-block-inventory.json").read_text())["inventory"]
data = pd.read_csv(root / "draw-results.csv")
assert len(data) == 32000 == r["method_draws"]
checks = []
for (length, weight, budget), part in data.groupby(["length", "weight", "budget"]):
    key = f"L{length}-w{weight:g}-b{budget}"
    s = r["results"][key]
    assert np.array_equal(part.draw, np.arange(1000))
    err = part.prevalence.to_numpy() - r["reference_prevalence"]
    assert abs(s["rmse_pp"] - np.sqrt(np.mean(err**2)) * 100) < 1e-10
    assert abs(s["bias_pp"] - err.mean() * 100) < 1e-10
    assert abs(s["mae_pp"] - np.abs(err).mean() * 100) < 1e-10
    assert np.isfinite(part.variance).all() and (part.variance >= 0).all()
    half = 1.959963984540054 * np.sqrt(part.variance.to_numpy())
    assert abs(s["normal_width_pp"] - 2 * half.mean() * 100) < 1e-10
    assert s["normal_coverage"] == float(np.mean(np.abs(err) <= half))
    assert abs(s["mean_labels"] - part.labels.mean()) < 1e-10
    assert abs(s["expected_labels"] - budget) < 1e-10
    assert np.allclose(
        s["realized_label_quantiles"], np.quantile(part.labels, [0, 0.05, 0.5, 0.95, 1])
    )
    assert s["excess_nominal_budget_rate"] == float(np.mean(part.labels > budget))
    assert abs(s["mean_queried_blocks"] - part.blocks.mean()) < 1e-10
    assert (part.labels >= part.blocks).all() and (part.labels <= part.blocks * length).all()
    checks.append(dict(setting=key, draws=1000, status="passed"))
for entry in json.loads((root / "query-lock.json").read_text())["plans"]:
    assert hashlib.sha256((root / entry["file"]).read_bytes()).hexdigest() == entry["sha256"]
    saved = np.load(root / entry["file"])
    costs = np.load(root / f"partition-L{entry['length']}.npz")["costs"]
    realized = np.array(
        [costs[s[:n]].sum() for s, n in zip(saved["selected"], saved["counts"], strict=True)]
    )
    for weight in [1, 0.5]:
        part = data[
            (data.length == entry["length"])
            & (data.budget == entry["budget"])
            & (data.weight == weight)
        ]
        assert np.array_equal(part.labels, realized)
        assert np.array_equal(part.blocks, saved["counts"])
base = (
    data[(data.length == 1) & (data.weight == 1) & (data.budget == 1032)].prevalence.to_numpy()
    - r["reference_prevalence"]
)
block = (
    data[(data.length == 5) & (data.weight == 1) & (data.budget == 1032)].prevalence.to_numpy()
    - r["reference_prevalence"]
)
idx = np.random.default_rng(400007).integers(1000, size=(2000, 1000))
ratio = np.sqrt((block[idx] ** 2).mean(axis=1) / (base[idx] ** 2).mean(axis=1))
assert np.allclose(
    np.quantile(ratio, [0.025, 0.975]), r["primary"]["draw_bootstrap_95pct"], rtol=0, atol=1e-10
)
fig, axes = plt.subplots(1, 3, figsize=(14, 4.4), layout="constrained")
colors = ["#184e77", "#ad7d25", "#d05e28", "#397f5b"]
for length, color in zip([1, 2, 5, 10], colors, strict=True):
    values = [r["results"][f"L{length}-w1-b{b}"] for b in [516, 1032, 2063, 4126]]
    axes[0].plot(
        [5, 10, 20, 40], [s["rmse_pp"] for s in values], "-o", label=f"L{length}", color=color
    )
    axes[1].plot([5, 10, 20, 40], [s["mean_queried_blocks"] for s in values], "-o", color=color)
    s = r["results"][f"L{length}-w1-b1032"]
    q = s["realized_label_quantiles"]
    axes[2].errorbar(
        length, q[2], yerr=[[q[2] - q[1]], [q[3] - q[2]]], fmt="o", color=color, capsize=4
    )
axes[0].set(ylabel="RMSE (percentage points)", title="Accuracy at lambda1")
axes[1].set(ylabel="Mean queried blocks", title="Query tasks, not measured time")
for ax in axes[:2]:
    ax.set(xlabel="Expected unique-label budget (%)", xticks=[5, 10, 20, 40])
axes[2].axhline(1032, color="black", ls="--", lw=1)
axes[2].set(
    xlabel="Requested block length",
    xticks=[1, 2, 5, 10],
    ylabel="Realized labels",
    title="B1,032: median and5–95% range",
)
for ax in axes:
    ax.grid(alpha=0.2)
fig.suptitle("Uniform contiguous-block pilot | matched expected labels |1,000 draws per setting")
fig.legend(*axes[0].get_legend_handles_labels(), loc="outside lower center", ncol=4, frameon=False)
for ext in ["png", "svg"]:
    fig.savefig(out / f"block-cost-accuracy.{ext}", dpi=160, bbox_inches="tight")
plt.close(fig)
lines = [
    "# Contiguous-block pilot G1",
    "",
    f"The primary L5/L1 RMSE ratio at B1032 and lambda1 is {r['primary']['rmse_ratio']:.4f}, "
    f"with fixed-corpus draw-bootstrap range{r['primary']['draw_bootstrap_95pct']}. "
    "All outcomes use equal expected unique-label cost; realized cost varies. "
    "This is a uniform-block pilot, not the queued static-versus-temporal guidance comparison.",
    "",
    "| Split | L | Eligible frames | Blocks | Mean size | Partial-block rate |",
    "| --- | ---: | ---: | ---: | ---: | ---: |",
]
for split in ["train", "validation", "test"]:
    for length in [1, 2, 5, 10]:
        s = inventory[f"{split}-L{length}"]
        lines.append(
            f"| {split} | {length} | {s['frames']} | {s['blocks']} | "
            f"{s['mean_block_size']:.3f} | {s['partial_block_rate']:.3f} |"
        )
lines += [
    "",
    "| L | Weight | Expected B | RMSE pp | Exact design RMSE pp | Normal coverage | "
    "Mean labels | Label5–95% | Over B rate | Mean blocks |",
    "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |",
]
for length in [1, 2, 5, 10]:
    for weight in [1, 0.5]:
        for budget in [516, 1032, 2063, 4126]:
            s = r["results"][f"L{length}-w{weight:g}-b{budget}"]
            q = s["realized_label_quantiles"]
            lines.append(
                f"| {length} | {weight} | {budget} | {s['rmse_pp']:.4f} | "
                f"{s['exact_design_rmse_pp']:.4f} | {s['normal_coverage']:.3f} | "
                f"{s['mean_labels']:.2f} | [{q[1]:.0f},{q[3]:.0f}] | "
                f"{s['excess_nominal_budget_rate']:.3f} | {s['mean_queried_blocks']:.2f} |"
            )
lines += [
    "",
    "![Block cost and accuracy](block-cost-accuracy.png)",
    "",
    "Longer contiguous queries reduce the number of query tasks but can increase "
    "residual correlation and estimation error. Query-task count is not measured "
    "human effort or speed. These results do not justify a time-saving claim. "
    "The variance estimator is conditional on the randomized block count; averaging "
    "its unbiased conditional variance is appropriate because each conditional "
    "point estimator has the same population expectation.",
    "",
    "The transferred weight0.5 uses the earlier uniform validation choice and is "
    "not retuned for blocks. Every setting and cost tail is retained. Length1 "
    "lambda1 reproduces the original M2 queries/estimates exactly. No new GPU "
    "inference or risk-model fitting was used. No valid exact binary interval is "
    "claimed for nonbinary block residual totals.",
    "",
    "All32,000 method-draw estimates passed independent RNG/point/variance checks "
    "in the runner, and saved-output summaries/costs and the primary bootstrap "
    "were checked separately. Next is G2 registration using frozen per-frame "
    "static/temporal OOF score aggregates; G1 does not select its length on test.",
    "",
    "Protocol: docs/X01_BLOCK_PILOT_G.md. Run scripts/run_block_pilot.py in the CPU "
    "environment and scripts/report_block_pilot.py in the plotting environment. "
    "Existing numerical roots refuse overwrite; reruns need a versioned config/output.",
]
(out / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
dest = root / "saved-output-validation.json"
if not dest.exists():
    dest.write_text(
        json.dumps(
            dict(
                status="passed",
                method_draws=len(data),
                checks=checks,
                primary_bootstrap="reproduced",
                result_sha256=hashlib.sha256((root / "result.json").read_bytes()).hexdigest(),
            ),
            indent=2,
        )
        + "\n"
    )
for name in [
    "result.json",
    "registration.json",
    "public-block-inventory.json",
    "saved-output-validation.json",
]:
    Path(f"docs/research/block-g-{name}").write_text((root / name).read_text(), encoding="utf-8")
print(f"G1 report complete; primary L5/L1 RMSE ratio{r['primary']['rmse_ratio']:.4f}.")
