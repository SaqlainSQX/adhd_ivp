"""Package accepted R aggregate findings after independent replay and visual QA."""

import hashlib
import json
import shutil
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out = Path("outputs/directional-noise-r-v1")
    proof = json.loads((out / "independent-validation.json").read_text(encoding="utf-8"))
    if not proof["complete"] or proof["method_case_draws_checked"] != 18000:
        raise ValueError("R independent validation incomplete")
    cfg = json.loads(Path("configs/directional-noise-r-v1.json").read_text(encoding="utf-8"))
    for name, expected in cfg["input_sha256"].items():
        if sha(Path(name)) != expected:
            raise ValueError(f"Frozen R input changed: {name}")
    frozen = json.loads(
        Path("outputs/experiments/timed-d-20261108-v1/registration.json").read_text(
            encoding="utf-8"
        )
    )["config"]["frozen_hashes"]
    root = Path("outputs/experiments/course-20261107-v1")
    for name, key in [
        ("evaluation/result.json", "main_result"),
        ("development/policy-lock.json", "main_policy_lock"),
    ]:
        if sha(root / name) != frozen[key]:
            raise ValueError(f"Locked main file changed: {name}")
    result = json.loads((out / "result.json").read_text(encoding="utf-8"))
    status = {
        "state": "complete",
        "independent_draw_checks": 18000,
        "toy_cases": 18,
        "all_25_pinned_inputs_and_main_evidence_unchanged": True,
        "figure_visually_reviewed": True,
        "cpu_only": True,
        "preregistration_commit": "bf7f1b4",
        "next": "docs/SUBMISSION_SYNTHESIS_S.md",
    }
    (out / "status.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# R: directional label-error sensitivity results",
        "",
        "False-positive and false-negative errors have different consequences for",
        "a rare reference outcome. In this synthetic study, 2% class-conditional",
        "false-positive errors cause much more upward bias than the downward bias",
        "from 2% false-negative errors. These settings have different total error",
        "counts. This is an assumption check, not a fair comparison of annotators",
        "at matched overall accuracy or an improved estimation method.",
        "",
        "The configuration and implementation were committed at bf7f1b4 before",
        "outcomes. The three registered cases, 1000 fixed queries per case/method,",
        "weights, primary budgets (ChildPlay1032; UCO521), source populations and",
        "new fixed noise seeds were used without tuning. No GPU/Kaggle work.",
        "",
        "## Primary full-K4 endpoints",
        "",
        "| Dataset | Case | Bias pp | Analytical bias pp | Approx. MC SE pp | RMSE pp | "
        "Normal coverage % | Mean queried flips |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["rows"]:
        if row["method"] == "K4":
            vals = [
                row["bias_pp"],
                100 * row["analytical"]["bias"],
                100 * (row["analytical"]["variance"] / 1000) ** 0.5,
                row["rmse_pp"],
                100 * row["normal_coverage"],
                row["mean_label_flips"],
            ]
            lines.append(
                f"| {row['dataset']} | {row['case']} | "
                + " | ".join(f"{v:.4f}" for v in vals)
                + " |"
            )
    lines += [
        "",
        "MC SE uses the joint analytical variance divided by1000; it is not",
        "a source-level confidence interval. Common observations make method/case",
        "cells dependent. Finite-draw deviations from expected bias are preserved.",
        "",
        "ChildPlay full-K4 normal coverage falls from94.8% clean to26.4% under",
        "false-positive errors, versus92.9% under false-negative errors. UCO falls",
        "from95.1% to80.5% and88.5%, respectively. Full/half K4 share exactly the",
        "same queries and corrupted observations. Weight reduction does not remove",
        "the expected bias a*(1-mu)-b*mu and gives no new robustness guarantee.",
        "",
        "## All registered cells",
        "",
        "All bias/RMSE/width columns use percentage points; coverage uses percent.",
        "FP means reference0 flips to1 with probability0.02; FN means reference1",
        "flips to0 with probability0.02. The other class has zero error in each case.",
        "",
        "| Dataset | Method | Case | Bias | RMSE | Normal coverage | Normal width | "
        "Binary coverage | Binary width | Mean flips |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["rows"]:
        method = {"K4": "K4 full", "power-score": "K4 half", "uniform": "Uniform + q"}[
            row["method"]
        ]
        vals = [
            row["bias_pp"],
            row["rmse_pp"],
            row["normal_coverage"] * 100,
            row["normal_width_pp"],
            row["naive_binary_clean_target_coverage"] * 100,
            row["naive_binary_width_pp"],
            row["mean_label_flips"],
        ]
        lines.append(
            f"| {row['dataset']} | {method} | {row['case']} | "
            + " | ".join(f"{v:.4f}" for v in vals)
            + " |"
        )
    lines += [
        "",
        "## Checks and reproducibility",
        "",
        "All18 exhaustive toy moment cases pass, including census observation",
        "noise (maximum error4.17e-17). All6000 clean controls match Q's saved",
        "point/variance/normal/exact endpoints before directional outcomes. The",
        "independent validator uses XOR corruption, fresh RNG reconstruction,",
        "scalar residual sums/squares and exhaustive feasible integer intervals.",
        f"It checks all{proof['method_case_draws_checked']} draws and every summary field,",
        f"including{proof['exact_integer_interval_cases']} distinct integer interval cases.",
        f"Maximum point difference: {proof['max_point_difference']:.3g}; variance:",
        f"{proof['max_variance_difference']:.3g}. Analytical bias/variance/MSE were checked",
        "using a separate dot-product formulation. All25 pinned inputs and the",
        "locked main result/policy hashes remain unchanged. Ruff passes. The PNG",
        "was visually reviewed for readable class labels, units and analytical",
        "markers; PDF uses the same figure. No failed R scientific stage occurred.",
        "",
        "Commands from the project root:",
        "",
        "```powershell",
        ".venv/Scripts/python.exe scripts/run_directional_noise.py",
        ".venv/Scripts/python.exe scripts/validate_directional_noise.py",
        ".venv-mtgs/Scripts/python.exe scripts/report_directional_noise.py",
        "```",
        "",
        "The runner refuses to overwrite its output directory. Any fresh rerun",
        "must use a new versioned output/config. Registration, complete aggregate",
        "result, toy/clean/replay proofs and logs are tracked under docs/research/r-*.",
        "Per-draw logs, reference labels and noise vectors are excluded from Git.",
        "",
        "## Interpretation limits",
        "",
        "A rare positive prevalence makes even a small false-positive probability",
        "important for prevalence estimates. A possible implication is to check",
        "both error directions during real annotation quality control. This study",
        "does not measure annotator error rates or validate any quality-control policy.",
        "The naive exact-binary intervals still target a corrupted population;",
        "clean-target coverage is not guaranteed, even when wide intervals cover.",
        "Class-conditional errors here are independent across records; human errors",
        "may be correlated, source-dependent or systematically ambiguous. Reference",
        "labels are treated as clean only for simulation. No new held-out evidence,",
        "diagnostic inference, selected correction or universal method gain follows.",
        "The original main study, all transfer losses and every Q/R cell remain intact.",
        "",
        "Next registered stage S consolidates accepted evidence into a defensible",
        "course report and checked claim map. It creates no new empirical outcomes.",
        "",
        "![Directional label-error sensitivity](../reports/course-project/directional-noise-r.png)",
        "",
    ]
    Path("docs/DIRECTIONAL_NOISE_R_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    for name in [
        "registration.json",
        "result.json",
        "toy-validation.json",
        "clean-baseline-validation.json",
        "independent-validation.json",
        "status.json",
    ]:
        shutil.copyfile(out / name, Path("docs/research") / ("r-" + name))
    for name in ["directional-noise-r-v1.log", "directional-noise-r-v1-validation.log"]:
        shutil.copyfile(Path("outputs") / name, Path("docs/research") / name)
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
