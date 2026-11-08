"""Save aggregate Q delivery, provenance and a readable complete-cell report."""

import hashlib
import json
import shutil
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out = Path("outputs/query-noise-q-v2")
    evidence = Path("docs/research")
    result = json.loads((out / "result.json").read_text(encoding="utf-8"))
    validation = json.loads((out / "independent-validation.json").read_text(encoding="utf-8"))
    if not validation["complete"] or validation["method_rate_draws_checked"] != 24000:
        raise ValueError("Independent replay incomplete")
    cfg = json.loads(Path("configs/query-noise-q-v2.json").read_text(encoding="utf-8"))
    for name, expected in cfg["input_sha256"].items():
        if sha(Path(name)) != expected:
            raise ValueError(f"Frozen input changed: {name}")
    frozen = json.loads(
        Path("outputs/experiments/timed-d-20261108-v1/registration.json").read_text(
            encoding="utf-8"
        )
    )["config"]["frozen_hashes"]
    main_root = Path("outputs/experiments/course-20261107-v1")
    for rel, key in [
        ("evaluation/result.json", "main_result"),
        ("development/policy-lock.json", "main_policy_lock"),
    ]:
        if sha(main_root / rel) != frozen[key]:
            raise ValueError(f"Main evidence changed: {rel}")
    status = {
        "state": "complete",
        "draws_independently_verified": 24000,
        "toy_moment_cases": 24,
        "frozen_inputs_and_main_result_lock_verified": True,
        "figure_visually_reviewed": True,
        "cpu_only": True,
        "next_protocol": "docs/ASYMMETRIC_NOISE_R.md",
    }
    (out / "status.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    copies = {}
    for filename in [
        "result.json",
        "registration.json",
        "toy-validation.json",
        "clean-baseline-validation.json",
        "independent-validation.json",
        "status.json",
    ]:
        copies[out / filename] = evidence / ("q-" + filename)
    failed = Path("outputs/query-noise-q-v1")
    for filename in [
        "failure.json",
        "registration.json",
        "baseline-interval-diagnosis.json",
        "repair-setup-failure.txt",
    ]:
        copies[failed / filename] = evidence / ("q-v1-" + filename)
    for filename in [
        "query-noise-q-v1.log",
        "query-noise-q-v2.log",
        "query-noise-q-v2-validation.log",
    ]:
        copies[Path("outputs") / filename] = evidence / filename
    for source, destination in copies.items():
        shutil.copyfile(source, destination)
    lines = [
        "# Q: synthetic label-error sensitivity results",
        "",
        "The audit depends on accurate queried labels. Synthetic symmetric errors",
        "substantially harm the clean-reference target; this stage shows a limitation,",
        "not a performance improvement. Frozen full/half K4 and uniform+q queries,",
        "budgets1032/521 and1000 draws were reused with no model fitting or rate selection.",
        "",
        "At the primary2% flip setting, full K4 signed bias is+1.7807 percentage",
        "points on ChildPlay (analytical+1.8592), versus+0.0048 with clean labels.",
        "UCO bias is+0.9788 (analytical+0.9048), versus+0.0194 clean. ChildPlay",
        "full-K4 RMSE increases0.2199 to1.9959 points and normal95% coverage falls",
        "94.8% to33.9%. UCO RMSE increases0.5923 to1.5334 and coverage95.1% to93.6%.",
        "",
        "All prespecified cells follow. Bias, RMSE and width use percentage points;",
        "coverage is percent. Half denotes0.5q on the same K4 queries. Uniform uses q.",
        "",
        "| Dataset | Method | Flip % | Bias | RMSE | Normal coverage | Normal width | "
        "Naive binary coverage | Binary width |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["rows"]:
        method = {"K4": "K4 full", "power-score": "K4 half", "uniform": "Uniform + q"}[
            row["method"]
        ]
        vals = [
            row["eta"] * 100,
            row["bias_pp"],
            row["rmse_pp"],
            row["normal_coverage"] * 100,
            row["normal_width_pp"],
            row["naive_binary_clean_target_coverage"] * 100,
            row["naive_binary_width_pp"],
        ]
        lines.append(
            f"| {row['dataset']} | {method} | " + " | ".join(f"{v:.4f}" for v in vals) + " |"
        )
    lines += [
        "",
        "## Analytical expectation versus finite simulation",
        "",
        "The formula describes the joint sampling/error expectation, not an exact",
        "match to a fixed1000-draw mean. Approximate Monte Carlo standard errors",
        "below use sqrt(analytical variance/1000); they are not source-level intervals.",
        "",
        "| Dataset | Full K4 flip % | Observed bias pp | Expected bias pp | MC SE pp |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in result["rows"]:
        if row["method"] == "K4":
            lines.append(
                f"| {row['dataset']} | {100 * row['eta']:.0f} | {row['bias_pp']:.4f} | "
                f"{100 * row['analytical']['bias']:.4f} | "
                f"{100 * (row['analytical']['variance'] / 1000) ** 0.5:.4f} |"
            )
    lines += [
        "",
        "## Verification and preserved failure",
        "",
        "All24 exhaustive toy moment cases pass (maximum error9.03e-17), including",
        "census cases with observation noise. All6000 clean controls match prior",
        "saved points, variances and intervals. Independent XOR/RNG/scalar-form",
        "replay checks all24000 cases; maximum point difference1.18e-16 and variance",
        "difference1.01e-16. Direct feasible-integer enumeration checks358 distinct",
        "hypergeometric interval cases. Aggregate bias/RMSE/coverage and analytical",
        "moments were independently checked. All17 pinned input files and the locked",
        "main result/policy hashes remain unchanged. Ruff passes. The six-panel",
        "PNG was visually inspected: titles, units, legend and coverage reference",
        "are readable. PDF is exported from the same Matplotlib figure.",
        "",
        "V1 stopped before noisy outcomes because M2 stored no binary interval",
        "endpoints. The registered v2 repair takes only those endpoints from M1",
        "after exact query-array/queried-positive equality checks, retaining M2's",
        "point/variance/normal comparison. Failure, diagnosis, repair setup failure",
        "and original run logs are retained. Formatting-only validator edits after",
        "its first pass were followed by another independent replay.",
        "",
        "## Interpretation and limits",
        "",
        "Rare positives make symmetric flips introduce upward bias. Half-weighting",
        "does not remove this bias; Q gives no new method win. At5% all ChildPlay",
        "normal intervals miss the clean target; UCO full K4 coverage is76.8%.",
        "The naive binary intervals target the corrupted binary population, and",
        "their clean-target coverage is not guaranteed. Large widths can hide this",
        "bias: UCO's99.1% full-K4 binary coverage at5% is not proof of robustness.",
        "",
        "Rates are artificial independent symmetric errors, not measured annotator",
        "accuracy. The reference labels are treated as clean only for simulation.",
        "Correlated, class-dependent and source-dependent errors may behave differently.",
        "These repeatedly inspected benchmark populations provide no fresh held-out",
        "confirmation, diagnostic evidence or universal real-world error bound.",
        "R preregisters a bounded directional-error decomposition; no main method",
        "or accepted result is changed. The10-minute standing program stays active.",
        "",
        "The fixed-draw primary bias differs from the analytical mean by about",
        "2.70 MC standard errors for ChildPlay and2.06 for UCO. These deviations",
        "are retained, not treated as exact agreement or resolved by choosing",
        "different seeds. Rates/methods share random observations, so cells are",
        "dependent; this stage does not make a multiple-comparison significance claim.",
        "",
        "Reproduce: `.venv/Scripts/python.exe scripts/run_query_noise_v2.py` in a new",
        "versioned output (existing outputs are intentionally protected), then",
        "`scripts/validate_query_noise.py`. Plot with the Matplotlib environment:",
        "`.venv-mtgs/Scripts/python.exe scripts/report_query_noise.py`.",
        "",
        "![Q sensitivity](../reports/course-project/query-noise-q.png)",
        "",
    ]
    Path("docs/QUERY_NOISE_Q_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
