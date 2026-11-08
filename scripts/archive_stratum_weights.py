"""Seal the final authorized U run and course-project handoff; no new queue."""

import hashlib
import json
import shutil
from pathlib import Path


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    out = Path("outputs/stratum-weights-u-v1")
    proof, result, fit = [
        read(out / name)
        for name in ["independent-validation.json", "result.json", "coefficient-lock.json"]
    ]
    if (
        not proof["complete"]
        or proof["draw_calculations_checked"] != 32000
        or proof["paired_bootstraps_checked"] != 24
    ):
        raise ValueError("Final U validation incomplete")
    cfg = read("configs/stratum-weights-u-v1.json")
    for name, expected in cfg["input_sha256"].items():
        if sha(Path(name).read_bytes()) != expected:
            raise ValueError(f"U input changed: {name}")
    main_root = Path("outputs/experiments/course-20261107-v1")
    frozen = read("docs/research/timed-d-registration.json")["config"]["frozen_hashes"]
    for rel, key in [
        ("evaluation/result.json", "main_result"),
        ("development/policy-lock.json", "main_policy_lock"),
    ]:
        if sha((main_root / rel).read_bytes()) != frozen[key]:
            raise ValueError("Final main evidence differs")
    prior = 0
    for path in Path("docs/research").glob("*evidence-manifest.json"):
        if path.name == "u-evidence-manifest.json":
            continue
        for name, expected in read(path).get("files", {}).items():
            raw = Path(name).read_bytes()
            if expected not in [sha(raw), sha(raw.replace(b"\r\n", b"\n"))]:
                raise ValueError(f"Final prior evidence differs: {name}")
            prior += 1
    lines = [
        "# U: final training-only coefficient experiment",
        "",
        "This was the user's last authorized experiment. The recurring research",
        "timer is PAUSED; no further experiment is queued. The full course handoff",
        "and recommendation are in [FINAL_PROJECT_HANDOFF.md](FINAL_PROJECT_HANDOFF.md).",
        "",
        "The training-only extension improves over full weight on ChildPlay but",
        "does not beat the earlier half-weight result at the primary budget.",
        "On UCO it improves over half weight but still loses to full weight.",
        "It therefore supplies a useful control, not a new best overall method.",
        "",
        "## Frozen recipe and training cost",
        "",
        "The config/kernel/runner were committed at1f4a9c8 before coefficient",
        "fitting or new test outcomes. Only191956 eligible training rows from40",
        "ChildPlay training sources were supplied to the coefficient fit. Their",
        "IDs and input files are hashed. Training coefficients were saved before",
        "evaluation-population access in this run. No validation, ChildPlay-test",
        "or UCO labels fit or select these coefficients. The source oracle file",
        "contains multiple splits, but only training-selected records enter fitting.",
        "",
        "For fixed phi_i=lambda_h*q_i, the audit uses mean(phi) plus weighted",
        "sample residual means. The coefficient is training Cov(y,q)/Var(q),",
        "clipped to[0,1], with the registered small-count/variance fallback to0.",
        "Strata, K4 allocations, exact query streams and label budgets are frozen.",
        "The global ablation fits the same coefficient on all training rows.",
        "This is an established control-variate idea applied to the course system,",
        "not a claim of a new theorem. Training labels are additional data costs,",
        "even though they reuse existing files; no annotation-free/cold-start",
        "cost advantage over a method without training labels is established.",
        "",
        f"Global fitted coefficient: {fit['global']['coefficient']:.12f}.",
        "",
        "| Stratum | Training rows | Fitted coefficient |",
        "|---|---:|---:|",
    ]
    for h, row in enumerate(fit["strata"]):
        lines.append(f"| {h} | {row['count']} | {row['coefficient']:.12f} |")
    lines += [
        "",
        "## Prespecified primary comparisons",
        "",
        "Intervals below are paired draw-bootstrap95% intervals over1000 saved",
        "audits on a fixed corpus, with2000 resamples. They do not quantify",
        "future-domain performance or adjust for the broader exploratory history.",
        "",
        "| Corpus | Labels | Per-stratum/full RMSE ratio | Bootstrap interval |",
        "|---|---:|---:|---|",
    ]
    for row in result["comparisons"]:
        if row["primary"]:
            ci = ", ".join(f"{v:.6f}" for v in row["paired_bootstrap_95pct"])
            lines.append(
                f"| {row['dataset']} | {row['budget']} | {row['rmse_ratio']:.6f} | [{ci}] |"
            )
    lines += [
        "",
        "ChildPlay primary per-stratum RMSE is0.199534pp versus0.219884 full",
        "and0.196725 half. UCO primary per-stratum RMSE is0.668021pp versus",
        "0.592311 full and0.751927 half. ChildPlay per-stratum/half ratio is",
        "1.014277 [1.004207,1.024598], a loss to the prior half-weight choice.",
        "UCO per-stratum/half ratio0.888411 [0.878051,0.898796] improves on that",
        "weaker control, while the primary full-weight comparison still loses.",
        "Both comparisons are retained; no test outcomes choose a final weight.",
        "",
        "## All registered method/budget cells",
        "",
        "Bias, RMSE and width use percentage points. Coverage uses percent.",
        "Exact design variance uses squared proportions and is analytical for",
        "this fixed population/design. It need not equal finite-draw sample MSE.",
        "",
        "| Corpus | Labels | Method | Bias pp | RMSE pp | Normal coverage % | "
        "Normal width pp | Exact variance |",
        "|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    for r in result["rows"]:
        lines.append(
            f"| {r['dataset']} | {r['budget']} | {r['method']} | {r['bias_pp']:.6f} | "
            f"{r['rmse_pp']:.6f} | {100 * r['normal_coverage']:.2f} | {r['normal_width_pp']:.6f} | "
            f"{r['exact_design_variance']:.9e} |"
        )
    lines += [
        "",
        "## Every registered paired comparison",
        "",
        "A ratio below1 favors the numerator. All losses and ties remain.",
        "",
        "| Corpus | Labels | Comparison | RMSE ratio | Paired95% interval |",
        "|---|---:|---|---:|---|",
    ]
    for r in result["comparisons"]:
        ci = ", ".join(f"{v:.6f}" for v in r["paired_bootstrap_95pct"])
        lines.append(
            f"| {r['dataset']} | {r['budget']} | {r['comparison']} | "
            f"{r['rmse_ratio']:.6f} | [{ci}] |"
        )
    lines += [
        "",
        "## Validation and evidence",
        "",
        "Before fitting, exhaustive enumeration of two small stratified designs",
        "checked unbiasedness, exact variance and mean sample variance, including",
        "census. Four coefficient boundary/fallback cases passed. Maximum moment",
        "error5.56e-17. The exact training rows/sources matched the protocol.",
        "",
        "All16 full/half budget controls (16000 method/draw cases) reproduced",
        "accepted points, variances and both normal endpoints. Binary-reference",
        "intervals were recomputed on8000 distinct fixed query plans and checked",
        "against accepted full/half endpoints. They are identical for all phi",
        "choices because references and queries are unchanged; they do not",
        "validate the newly weighted normal intervals.",
        "",
        "Independent validation recomputed all five coefficient fits with fsum",
        "centered cross-products, all32000 point/variance/normal calculations,",
        "all exact design variances and summary fields, query RNG/label costs,",
        "and all24 bootstrap comparisons. Bootstrap validation used frequency",
        "weights and manually interpolated sorted quantiles rather than the",
        "primary index-mean/np.quantile path. Maximum differences: point1.67e-16,",
        "variance1.00e-16, bootstrap endpoint4.00e-15. A formatting-only literal",
        "split after replay preserved the validator's exact parsed AST. Ruff passes.",
        "",
        f"All{prior} prior manifest entries and the main result/policy hashes",
        "remain intact. Input hashes match registration. All32 cells and24",
        "comparisons are saved; the complete figure was visually inspected for",
        "readable budgets, methods, units and the coverage reference. No scientific",
        "stage failed; development lint corrections did not change the method.",
        "",
        "## Limits and stopping decision",
        "",
        "The cohorts were repeatedly inspected before U was proposed; no fresh",
        "held-out or universal improvement is claimed. Training residual variance",
        "minimization does not guarantee transfer performance. The primary methods",
        "still differ by corpus, and the ChildPlay high-budget normal coverage",
        "failure remains visible. We do not clip points into binary intervals or",
        "replace previously failing error bars. Source/crop/pretraining limits,",
        "missing media, annotation uncertainty and absence of clinical validation",
        "remain as described in the course guide and earlier addenda.",
        "",
        "Stop experiments here as requested. The project is sufficiently developed",
        "for a course submission; further parameter search on these labels is",
        "unlikely to strengthen its evidential claims. Prepare the report, slides",
        "and demonstration using the checked guide plus T/U addenda. No new run",
        "or timer is queued. The existing demos/services remain unchanged.",
        "",
        "Reproduction commands (a new versioned output/config is required for",
        "another run; the original runner refuses to overwrite evidence):",
        "",
        "```powershell",
        ".venv/Scripts/python.exe scripts/run_stratum_weights.py",
        ".venv/Scripts/python.exe scripts/validate_stratum_weights.py",
        ".venv-mtgs/Scripts/python.exe scripts/report_stratum_weights.py",
        "```",
        "",
        "![Final coefficient experiment](../reports/course-project/stratum-weights-u.png)",
        "",
    ]
    Path("docs/STRATUM_WEIGHTS_U_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    status = {
        "complete": True,
        "final_user_authorized_run": True,
        "independent_draw_checks": 32000,
        "independent_bootstraps": 24,
        "coefficient_fits": 5,
        "prior_manifest_entries_verified": prior,
        "main_evidence_unchanged": True,
        "figure_visually_reviewed": True,
        "automation": "PAUSED per explicit user instruction",
        "pending_experiments": [],
        "recommended_next_work": "course report, slides and demonstration; no further experiments",
    }
    (out / "status.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    names = []
    for filename in [
        "result.json",
        "registration.json",
        "toy-validation.json",
        "coefficient-lock.json",
        "baseline-validation.json",
        "independent-validation.json",
        "status.json",
    ]:
        target = Path("docs/research") / ("u-" + filename)
        shutil.copyfile(out / filename, target)
        names.append(target.as_posix())
    for filename in [
        "stratum-weights-u-v1.log",
        "stratum-weights-u-v1-validation.log",
        "stratum-weights-u-v1-validation-formatted.log",
    ]:
        target = Path("docs/research") / filename
        shutil.copyfile(Path("outputs") / filename, target)
        names.append(target.as_posix())
    names += [
        "docs/STRATUM_WEIGHTS_U.md",
        "docs/STRATUM_WEIGHTS_U_RESULTS.md",
        "docs/FINAL_PROJECT_HANDOFF.md",
        "configs/stratum-weights-u-v1.json",
        "src/gaze_audit/stratum_weights.py",
        "scripts/register_stratum_weights.py",
        "scripts/run_stratum_weights.py",
        "scripts/validate_stratum_weights.py",
        "scripts/report_stratum_weights.py",
        "scripts/archive_stratum_weights.py",
        "reports/course-project/stratum-weights-u.png",
        "reports/course-project/stratum-weights-u.pdf",
    ]
    files = {}
    for name in names:
        raw = Path(name).read_bytes()
        if Path(name).suffix not in [".png", ".pdf"]:
            raw = raw.replace(b"\r\n", b"\n")
        files[name] = sha(raw)
    manifest = {
        "stage": "U final authorized experiment and handoff",
        "files": files,
        "hash_convention": "Tracked text CRLF to LF; binaries/local data raw",
        "local_files": {
            "outputs/stratum-weights-u-v1/draw-results.csv": sha(
                (out / "draw-results.csv").read_bytes()
            )
        },
        "mutable_exclusions": ["docs/CONTINUOUS_RESEARCH_STATUS.md"],
    }
    Path("docs/research/u-evidence-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
