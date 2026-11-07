"""E06: produce transparent course tables and figures from locked results."""

import argparse
import csv
import hashlib
import json
import os
import subprocess
from pathlib import Path

import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--development", type=Path, required=True)
    parser.add_argument("--checks", type=Path, required=True)
    parser.add_argument("--population", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new report directory")
    result = json.loads((args.evaluation / "result.json").read_text())
    lock = json.loads((args.development / "policy-lock.json").read_text())
    checks = json.loads((args.checks / "result.json").read_text())
    population = json.loads((args.population / "population-manifest.json").read_text())
    if (
        not all(r["complete"] for r in [result, lock, checks])
        or result["test_population_size"]
        != population["retained_eligible_anchors_by_split"]["test"]
        or result["feature_hashes"] != lock["feature_hashes"]
        or result["feature_hashes"] != checks["feature_hashes"]
    ):
        raise ValueError("Incomplete or inconsistent report inputs")
    pipeline_path = args.output.parent / "pipeline-status.json"
    verification_path = args.output.parent / "independent-validation.json"
    if pipeline_path.exists() and not verification_path.exists():
        project = Path(__file__).resolve().parents[1]
        python = project / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run(
            [str(python), "scripts/validate_experiment_run.py", "--run", str(args.output.parent)],
            check=True,
            cwd=project,
        )
    if pipeline_path.exists():
        verification = json.loads(verification_path.read_text())
        if (
            verification["status"] != "passed"
            or verification["sampled_audits_recomputed"] != result["sampled_method_runs"]
            or verification["evaluation_result_sha256"]
            != hashlib.sha256((args.evaluation / "result.json").read_bytes()).hexdigest()
        ):
            raise ValueError("Independent full-run audit validation has not passed")
    args.output.mkdir(parents=True)
    os.environ["MPLCONFIGDIR"] = str((args.output / "matplotlib-cache").resolve())
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = {
        "M1": "Human uniform",
        "M2": "Uniform residual",
        "M3": "Static guided",
        "M4": "Temporal guided",
        "M5": "Contextual surrogate",
    }
    colors = {"M1": "#4063A2", "M2": "#767676", "M3": "#D08A22", "M4": "#23836A", "M5": "#8C5AA5"}
    fractions = [0.05, 0.1, 0.2, 0.4]
    budgets = [int(np.floor(f * result["test_population_size"] + 0.5)) for f in fractions]
    primary = next(
        c for c in result["comparisons"] if c["fraction"] == 0.1 and c["comparison"] == "M4/M3"
    )
    ratio = primary["rmse_ratio"]
    interval = primary["paired_draw_bootstrap_95pct"]
    if ratio is None:
        verdict = (
            "The primary ratio is undefined because the static baseline has zero observed RMSE."
        )
    elif ratio < 0.9 and interval[1] < 1:
        verdict = (
            "Temporal guidance met the planned 10% relative RMSE-reduction target on this "
            "fixed corpus."
        )
    elif ratio < 1 and interval[1] < 1:
        verdict = (
            "Temporal guidance reduced RMSE on this fixed corpus, "
            "below the planned 10% practical target."
        )
    elif ratio < 1:
        verdict = (
            "Temporal guidance had lower observed RMSE, with Monte Carlo uncertainty "
            "including a tie."
        )
    else:
        verdict = (
            "Temporal guidance did not improve the primary RMSE comparison against static guidance."
        )

    table_rows = []
    for method in names:
        for fraction, budget in zip(fractions, budgets, strict=True):
            value = result["results"][f"{method}-b{budget}"]
            table_rows.append(
                {
                    "method": method,
                    "name": names[method],
                    "fraction": fraction,
                    "budget": budget,
                    "bias_pp": value["bias_pp"],
                    "mae_pp": value["mae_pp"],
                    "rmse_pp": value["rmse_pp"],
                    "normal_coverage": value["intervals"]["normal"]["coverage"],
                    "normal_width_pp": value["intervals"]["normal"]["mean_width_pp"],
                    "bounded_coverage": value["intervals"]["bounded"]["coverage"],
                    "bounded_width_pp": value["intervals"]["bounded"]["mean_width_pp"],
                    "zero_positive_rate": value["zero_positive_rate"],
                    "failed_draw_rate": value["failed_draw_rate"],
                }
            )
    with (args.output / "results-table.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(table_rows[0]))
        writer.writeheader()
        writer.writerow(
            {
                "method": "M0",
                "name": "Model only (deterministic)",
                "fraction": 0,
                "budget": 0,
                "bias_pp": result["model_only_bias_pp"],
                "mae_pp": abs(result["model_only_bias_pp"]),
                "rmse_pp": abs(result["model_only_bias_pp"]),
            }
        )
        writer.writerows(table_rows)

    cost = {
        "development_labels": lock["development_unique_labels"],
        "test_labels_per_audit": dict(zip(map(str, fractions), budgets, strict=True)),
        "new_human_annotation_time_measured": False,
        "compute_stages": [],
        "inference_shards": [],
        "kaggle_gpu_hours_used": 0,
    }
    if pipeline_path.exists():
        pipeline = json.loads(pipeline_path.read_text())
        cost["compute_stages"] = [
            {"stage": row["name"], "seconds": row.get("elapsed_seconds"), "state": row["state"]}
            for row in pipeline["stages"]
        ]
        for shard in pipeline["shards"]:
            inference = json.loads((Path(shard) / "inference-provenance.json").read_text())
            cost["inference_shards"].append(
                {
                    "path": shard,
                    "seconds": inference["elapsed_seconds"],
                    "frames": inference["processed_frames"],
                    "gpu": inference["runtime"]["gpu"],
                    "peak_allocated_bytes": inference["peak_gpu_allocated_bytes"],
                }
            )
    (args.output / "cost-ledger.json").write_text(json.dumps(cost, indent=2) + "\n")

    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "svg.fonttype": "none",
            "savefig.bbox": "tight",
        }
    )
    fig, axis = plt.subplots(figsize=(8, 4.6), layout="constrained")
    for method in names:
        values = [result["results"][f"{method}-b{budget}"]["rmse_pp"] for budget in budgets]
        axis.plot(
            np.asarray(budgets) / result["test_population_size"] * 100,
            values,
            marker="o",
            color=colors[method],
            label=f"{method}: {names[method]}",
            linewidth=2.4 if method == "M4" else 1.5,
        )
    axis.axhline(
        abs(result["model_only_bias_pp"]),
        color="#B0413E",
        linestyle="--",
        linewidth=1.2,
        label="M0: model-only absolute error (zero audit labels)",
    )
    axis.set(
        xlabel="Reference labels queried (%)",
        ylabel="Prevalence RMSE (percentage points)",
        title="Estimation error on the verified ChildPlay subset",
        ylim=(0, None),
    )
    axis.grid(alpha=0.15)
    axis.legend(frameon=False, fontsize=8)
    fig.savefig(args.output / "rmse-budget.png", dpi=240)
    fig.savefig(args.output / "rmse-budget.svg")
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8), layout="constrained")
    for method in names:
        values = [result["results"][f"{method}-b{b}"] for b in budgets]
        x = np.asarray(budgets) / result["test_population_size"] * 100
        axes[0].plot(
            x, [v["bias_pp"] for v in values], marker="o", color=colors[method], label=method
        )
        axes[1].plot(
            x,
            [v["intervals"]["normal"]["coverage"] * 100 for v in values],
            marker="o",
            color=colors[method],
        )
        axes[2].plot(
            x,
            [v["intervals"]["normal"]["mean_width_pp"] for v in values],
            marker="o",
            color=colors[method],
        )
    axes[0].axhline(0, color="#333333", linestyle="--", linewidth=1)
    axes[1].axhline(95, color="#333333", linestyle="--", linewidth=1)
    axes[0].set(title="Bias", ylabel="Percentage points")
    axes[1].set(title="Normal interval coverage", ylabel="Coverage (%)", ylim=(0, 105))
    axes[2].set(title="Normal interval width", ylabel="Average width (percentage points)")
    for axis in axes:
        axis.set_xlabel("Reference labels queried (%)")
        axis.grid(alpha=0.15)
    axes[0].legend(frameon=False, ncols=2, fontsize=8)
    fig.savefig(args.output / "bias-coverage-width-budget.png", dpi=240)
    fig.savefig(args.output / "bias-coverage-width-budget.svg")
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(7, 4), layout="constrained")
    selected_methods = ["M2", "M3", "M4", "M5"]
    axis.bar(
        selected_methods,
        [result["results"][f"{m}-b{budgets[1]}"]["rmse_pp"] for m in selected_methods],
        color=[colors[m] for m in selected_methods],
    )
    axis.set(
        title="Allocation and surrogate controls at 10% budget",
        ylabel="Prevalence RMSE (percentage points)",
    )
    axis.grid(axis="y", alpha=0.15)
    fig.savefig(args.output / "primary-controls.png", dpi=240)
    fig.savefig(args.output / "primary-controls.svg")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), layout="constrained")
    positions = np.arange(5)
    for offset, interval_name, color in [
        (-0.18, "normal", "#4063A2"),
        (0.18, "bounded", "#D08A22"),
    ]:
        values = [
            result["results"][f"{method}-b{budgets[1]}"]["intervals"][interval_name]
            for method in names
        ]
        axes[0].bar(
            positions + offset,
            [v["mean_width_pp"] for v in values],
            width=0.35,
            color=color,
            label=interval_name.capitalize(),
        )
        axes[1].bar(
            positions + offset, [v["coverage"] * 100 for v in values], width=0.35, color=color
        )
    axes[0].set(ylabel="Average interval width (percentage points)", title="Width at 10% budget")
    axes[1].set(ylabel="Empirical coverage (%)", title="Coverage at 10% budget", ylim=(0, 105))
    axes[1].axhline(95, color="#333333", linestyle="--", linewidth=1)
    for axis in axes:
        axis.set_xticks(positions, list(names))
        axis.grid(axis="y", alpha=0.15)
    axes[0].legend(frameon=False)
    fig.savefig(args.output / "interval-width-coverage.png", dpi=240)
    fig.savefig(args.output / "interval-width-coverage.svg")
    plt.close(fig)

    sensitivity = result["primary_source_sensitivity"]
    fig, axis = plt.subplots(figsize=(8, max(3.5, len(sensitivity) * 0.35)), layout="constrained")
    valid = [r for r in sensitivity if r["leave_source_out_M4_over_M3"] is not None]
    axis.scatter(
        [r["leave_source_out_M4_over_M3"] for r in valid], np.arange(len(valid)), color=colors["M4"]
    )
    axis.set_yticks(np.arange(len(valid)), [r["source_id"] for r in valid])
    axis.axvline(1, color="#333333", linestyle="--", linewidth=1)
    axis.set(
        xlabel="RMSE ratio M4 / M3 after excluding each source domain",
        title="Primary-budget source sensitivity; original query design",
    )
    axis.grid(axis="x", alpha=0.15)
    fig.savefig(args.output / "source-sensitivity.png", dpi=240)
    fig.savefig(args.output / "source-sensitivity.svg")
    plt.close(fig)

    ratio_text = "undefined" if ratio is None else f"{ratio:.4f}"
    lines = [
        "# Temporal error-guided auditing: course experiment report",
        "",
        verdict,
        "",
        "This is an exploratory, fixed-corpus benchmark. A positive result would be an "
        "application result; "
        "generic stratification, residual correction and temporal context are established ideas.",
        "",
        "## Data and frozen protocol",
        "",
        f"All {population['original_sources_attempted']} original source videos were attempted. "
        f"The verified subset retains {population['retained_sources']} sources and "
        f"{result['test_population_size']:,} eligible test pair-frames from "
        f"{result['test_source_count']} sources. "
        "Unknown references are excluded. Failed/changed/challenged media are recorded in "
        "the population manifest. "
        "The results target this available subset and do not estimate the missing videos' "
        "prevalence.",
        "",
        "The frozen predictor is the released MTGS-DINO temporal model. Static M3 and "
        "temporal M4 share "
        "its native q and the same finite-population difference estimator. "
        "Training-source cross-fitting "
        "defines error strata; validation selects among nine prespecified "
        "allocation/window candidates. "
        "No predictor weights or policy parameters are fitted to test references.",
        "",
        f"Selected static alpha: {lock['selected_static']['alpha']}; temporal alpha: "
        f"{lock['selected_temporal']['alpha']}, window: "
        f"{lock['selected_temporal']['temporal_window']}. "
        f"Each method/budget has {result['draws_per_method_budget']:,} draws. Query plans "
        f"were saved before oracle access. "
        "M1/M2/M5 reuse the same uniform queries.",
        "",
        f"Test reference prevalence: {result['reference_prevalence'] * 100:.4f}%. "
        f"Uncorrected model mean: {result['model_only_mean'] * 100:.4f}% "
        f"(bias {result['model_only_bias_pp']:+.4f} percentage points).",
        "",
        "## Estimation results",
        "",
        "| Method | 5% RMSE | 10% RMSE | 20% RMSE | 40% RMSE |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for method in names:
        values = [result["results"][f"{method}-b{budget}"]["rmse_pp"] for budget in budgets]
        lines.append(
            f"| {method}: {names[method]} | " + " | ".join(f"{v:.4f}" for v in values) + " |"
        )
    lines.append(
        "| M0: Model only (zero labels) | "
        + " | ".join([f"{abs(result['model_only_bias_pp']):.4f}"] * 4)
        + " |"
    )
    lines += [
        "",
        "RMSE units are percentage points. Exact budgets: " + ", ".join(map(str, budgets)) + ".",
        "",
        "![RMSE versus budget](rmse-budget.png)",
        "",
        "![Bias, coverage and width by budget](bias-coverage-width-budget.png)",
        "",
        "![Primary allocation and surrogate controls](primary-controls.png)",
        "",
        f"Primary M4/M3 RMSE ratio: {ratio_text}, with paired-draw bootstrap interval "
        f"[{interval[0]:.4f}, {interval[1]:.4f}]. "
        "This interval reflects Monte Carlo uncertainty on the fixed corpus, not transfer "
        "to new sources.",
        "",
        "M5 uses the same temporal error model to adjust the surrogate, with uniform correction. "
        "Its comparison with M4 distinguishes the allocation benefit from a contextual "
        "surrogate benefit. "
        "All comparisons, including losses and ties, are retained in result.json.",
        "",
        "## Intervals and source sensitivity",
        "",
        "Normal 95% intervals are approximate. The bounded-residual reference can be much wider; "
        "coverage and width must be considered together. M1 additionally has an exact "
        "hypergeometric interval. "
        "The CSV records sparse-positive, zero-variance and failure rates.",
        "",
        f"M4 normal interval coverage at the primary budget was "
        f"{result['results'][f'M4-b{budgets[1]}']['intervals']['normal']['coverage'] * 100:.1f}%. "
        "An RMSE reduction alone does not establish useful confidence intervals.",
        "",
        "![Interval width and coverage](interval-width-coverage.png)",
        "",
        "![Source sensitivity](source-sensitivity.png)",
        "",
        result["source_sensitivity_scope"],
        "",
        "## Cost and interpretation limits",
        "",
        f"Historical development references reused: "
        f"{lock['development_unique_labels']['train']:,} training "
        f"and {lock['development_unique_labels']['validation']:,} validation labels. "
        "These costs are separate from each test audit's budget. No new annotators were timed; "
        "label-count efficiency is not a measured human-time saving.",
        "",
        "The official backbone was trained on VSGaze; this study reuses historical training "
        "annotations for the error model. It evaluates a frozen published predictor, rather than "
        "a cold-start system with a newly purchased development set.",
        "",
        "Compute and reference-label costs are itemized in `cost-ledger.json`. GPU preprocessing "
        "and inference are shared by all methods; repeated audits reuse the same frozen cache.",
        "",
        f"Only {checks['descriptive_diagnostics']['validation']['sources']} validation sources "
        "remain available, limiting selection stability. Test references "
        "had already been inspected in earlier feasibility work, so the experiment is "
        "exploratory. "
        "Benchmark labels and provided head tracks define the target; this study does not "
        "validate ADHD "
        "or autism diagnosis, direct eye contact, or fully automatic raw-video deployment.",
        "",
        "The contribution suitable for the course is a reproducible "
        "temporal-versus-static audit experiment "
        "with exact label budgets, query replay, reference isolation, source alignment "
        "checks and an explicit "
        "contextual-surrogate control. Scientific novelty or general superiority is not "
        "established by implementation alone.",
        "",
        "## Reproduction artifacts",
        "",
        "The estimator uses e_i=y_i-q_i and p_hat=mean_all(q)+sum_h(N_h/M)*mean_sample_h(e). "
        "Its estimated variance is sum_h (N_h/M)^2 (1-n_h/N_h) s_e,h^2/n_h. "
        "M1 uses q=0; M5 substitutes the frozen contextual surrogate. Fixed partitions and SRS "
        "without replacement preserve positive inclusion and exact label counts.",
        "",
        "```mermaid",
        "flowchart LR",
        '  A["Verified images and public head tracks"] --> B["Frozen temporal MTGS"]',
        '  B --> C["Native scores and label-free features"]',
        '  C --> D["Train error models; validate allocation"]',
        '  D --> E["Freeze policies and draw exact-budget queries"]',
        '  E --> F["Reveal selected references; correct prevalence"]',
        "```",
        "",
        f"- Evaluation: `{args.evaluation}`",
        f"- Frozen policy lock: `{args.development / 'policy-lock.json'}`",
        f"- Development diagnostics: `{args.checks / 'result.json'}`",
        f"- Media/population manifest: `{args.population / 'population-manifest.json'}`",
        "- Exported tables: `results-table.csv`; shareable figures: PNG and SVG files in "
        "this directory.",
        "",
        "## Sources and scope of contribution",
        "",
        "- [Official MTGS implementation and model description](https://github.com/idiap/MTGS)",
        "- [VSGaze annotation release](https://zenodo.org/records/17357752)",
        "- [Original ChildPlay release and extraction metadata](https://zenodo.org/records/8252535)",
        "- [Stratified prediction-powered inference](https://proceedings.neurips.cc/paper_files/"
        "paper/2024/file/c9fcd02e6445c7dfbad6986abee53d0d-Paper-Conference.pdf)",
        "",
        "The temporal predictor is an external pretrained component. The course contribution is "
        "the implemented auditing policy, controlled comparison, data-verification workflow and "
        "reproducible evidence. This report does not claim to introduce residual correction or "
        "stratified sampling as new statistical ideas.",
        "",
    ]
    (args.output / "course-report.md").write_text("\n".join(lines), encoding="utf-8")
    (args.output / "report-status.json").write_text(
        json.dumps(
            {
                "computation_complete": True,
                "visual_review": "pending agent inspection",
                "interpretation": verdict,
                "primary_rmse_ratio": ratio,
                "figure_files": [
                    "rmse-budget.png",
                    "interval-width-coverage.png",
                    "source-sensitivity.png",
                    "bias-coverage-width-budget.png",
                    "primary-controls.png",
                ],
                "report": "course-report.md",
                "independent_validation": str(verification_path)
                if pipeline_path.exists()
                else None,
            },
            indent=2,
        )
        + "\n"
    )
    print(args.output / "course-report.md")


if __name__ == "__main__":
    main()
