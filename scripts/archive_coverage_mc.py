"""Package complete T diagnostics and preserve all prior project evidence."""

import hashlib
import json
import shutil
from pathlib import Path


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    out = Path("outputs/coverage-mc-t-v1")
    proof, result = read(out / "independent-validation.json"), read(out / "result.json")
    if not proof["complete"] or proof["intervals_checked"] != 148:
        raise ValueError("T validation incomplete")
    frozen = read("docs/research/timed-d-registration.json")["config"]["frozen_hashes"]
    base = Path("outputs/experiments/course-20261107-v1")
    for rel, key in [
        ("evaluation/result.json", "main_result"),
        ("development/policy-lock.json", "main_policy_lock"),
    ]:
        if digest((base / rel).read_bytes()) != frozen[key]:
            raise ValueError("T frozen main evidence differs")
    checked = 0
    for manifest in Path("docs/research").glob("*evidence-manifest.json"):
        if manifest.name == "t-evidence-manifest.json":
            continue
        for name, expected in read(manifest).get("files", {}).items():
            raw = Path(name).read_bytes()
            if expected not in (digest(raw), digest(raw.replace(b"\r\n", b"\n"))):
                raise ValueError(f"T prior evidence changed: {name}")
            checked += 1
    rows = result["rows"]
    lines = [
        "# T: Monte Carlo uncertainty in normal-interval coverage",
        "",
        "This deterministic reliability analysis uses all74 registered saved",
        "coverage cells. No new models, queries, labels or predictions were made.",
        "The family/counts/code were committed at2663c37 before T endpoints.",
        "All original coverages were already inspected: this is exploratory",
        "diagnosis, not fresh confirmation or a correction to the intervals.",
        "",
        "## Primary main-study cells",
        "",
        "| Main method/budget | Observed % | Individual95% MC interval % | "
        "Family95% MC interval % |",
        "|---|---:|---|---|",
    ]

    def bounds(values):
        return "[" + ", ".join(f"{100 * v:.4f}" for v in values) + "]"

    for row in rows:
        if row["primary"]:
            lines.append(
                f"| {row['id']} | {100 * row['coverage']:.4f} | "
                f"{bounds(row['individual_interval'])} | {bounds(row['family_interval'])} |"
            )
    lines += [
        "",
        "Both primary individual upper bounds are below95%; neither family",
        "upper bound is below95%. The wider simultaneous intervals do not",
        "establish nominal coverage. They express uncertainty in a coverage",
        "probability over random audits, not in prevalence or future domains.",
        "",
        "Main M3-b2063 and M4-b2063 retain upper bounds below95% even with the",
        "registered family adjustment. Do not hide them or imply all main",
        "intervals have demonstrated reliable nominal coverage.",
        "",
        "## Complete diagnostic counts",
        "",
        "| Group | Cells | Individual undercoverage flags | Family undercoverage flags |",
        "|---|---:|---:|---:|",
    ]
    for group, counts in result["counts"].items():
        lines.append(
            f"| {group} | {sum(r['group'] == group for r in rows)} | "
            f"{counts['individual_undercoverage']} | {counts['family_undercoverage']} |"
        )
    lines += [
        "",
        "No individual or family overcoverage flag occurs in this normal-interval",
        "family. Cells are dependent and include repeated clean controls; counts",
        "are diagnostic cells, not independent discoveries. UCO having no flags",
        "does not prove coverage equals or exceeds95%.",
        "",
        "## Every registered cell",
        "",
        "All endpoints below use percent; each cell has1000 draws. Flag means",
        "the interval's upper endpoint is below95%. All endpoints are retained",
        "at full precision in the aggregate JSON.",
        "",
        "| Group | Cell | k/n | Observed % | Individual95% MC interval % | "
        "Family95% MC interval % | Individual flag | Family flag |",
        "|---|---|---|---:|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['group']} | {r['id']} | {r['k']}/{r['n']} | "
            f"{100 * r['coverage']:.2f} | {bounds(r['individual_interval'])} | "
            f"{bounds(r['family_interval'])} | {r['individual_undercoverage']} | "
            f"{r['family_undercoverage']} |"
        )
    lines += [
        "",
        "## Verification and interpretation limits",
        "",
        "All three elementary reference cases passed before scientific endpoints",
        "(maximum error2.43e-17). The independent standard-library validator",
        "imports no beta quantile: it uses log-binomial sums at284 interior",
        "endpoints and elementary boundary expressions at12 endpoints. All148",
        "intervals/74 counts, selectors, alpha allocation, flags and summaries",
        "passed; maximum tail/boundary error1.66e-14. All four input hashes and",
        f"{checked} prior manifest entries plus locked main result/policy hashes",
        "remain intact. Ruff passes. The four-panel PNG was visually inspected",
        "for labels, nominal reference, interval widths and differing x-axis",
        "ranges. PDF uses the same plot. Purple diamonds mark the primary cells.",
        "",
        "Clopper-Pearson intervals concern the Bernoulli Monte Carlo coverage",
        "under the saved randomization model. The Bonferroni allocation uses",
        "alpha/74 and is conservative under between-cell dependence for a fixed",
        "family. This exploratory diagnostic family does not adjust for the",
        "broader adaptive research history, earlier policy exploration or prior",
        "inspection of the original coverages. It is not a new confirmatory test.",
        "",
        "A prevalence interval, an RMSE-ratio bootstrap interval and an interval",
        "for repeated-audit coverage answer different questions. T cannot fix",
        "bias, prove domain generalization or validate real annotator accuracy.",
        "Q/R synthetic-label clean-target failures remain assumption stress tests.",
        "An interval containing95% is lack of a detected departure at that level,",
        "not acceptance of nominal reliability. No policy is replaced or tuned.",
        "",
        "Reproduce in a new versioned output/config: run scripts/run_coverage_mc.py,",
        "then scripts/validate_coverage_mc.py (standard-library, -I -S supported).",
        "Plot with the Matplotlib environment using scripts/report_coverage_mc.py.",
        "The runner refuses to overwrite evidence. Accepted aggregate outputs",
        "and proofs are tracked under docs/research/t-*; no raw labels are needed",
        "for this analysis. Source hashes and exact selectors are in the config.",
        "",
        "Next U preregisters training-only global/per-stratum control-variate",
        "coefficients, with frozen allocations and no test-selected weights.",
        "",
        "![Coverage uncertainty](../reports/course-project/coverage-mc-t.png)",
        "",
    ]
    Path("docs/COVERAGE_MC_T_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    status = {
        "complete": True,
        "rows": 74,
        "independent_intervals": 148,
        "prior_manifest_entries_verified": checked,
        "main_evidence_unchanged": True,
        "figure_visually_reviewed": True,
        "new_queries_models_labels": False,
        "next": "docs/STRATUM_WEIGHTS_U.md",
    }
    (out / "status.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    files = []
    for filename in [
        "result.json",
        "registration.json",
        "toy-validation.json",
        "independent-validation.json",
        "status.json",
    ]:
        target = Path("docs/research") / ("t-" + filename)
        shutil.copyfile(out / filename, target)
        files.append(target.as_posix())
    for filename in ["coverage-mc-t-v1.log", "coverage-mc-t-v1-validation.log"]:
        target = Path("docs/research") / filename
        shutil.copyfile(Path("outputs") / filename, target)
        files.append(target.as_posix())
    files += [
        "docs/COVERAGE_MC_T.md",
        "docs/COVERAGE_MC_T_RESULTS.md",
        "docs/STRATUM_WEIGHTS_U.md",
        "configs/coverage-mc-t-v1.json",
        "scripts/register_coverage_mc.py",
        "scripts/run_coverage_mc.py",
        "scripts/validate_coverage_mc.py",
        "scripts/report_coverage_mc.py",
        "scripts/archive_coverage_mc.py",
        "reports/course-project/coverage-mc-t.png",
        "reports/course-project/coverage-mc-t.pdf",
    ]
    hashes = {}
    for name in files:
        raw = Path(name).read_bytes()
        if Path(name).suffix not in [".png", ".pdf"]:
            raw = raw.replace(b"\r\n", b"\n")
        hashes[name] = digest(raw)
    Path("docs/research/t-evidence-manifest.json").write_text(
        json.dumps(
            {
                "stage": "T exploratory coverage MC uncertainty",
                "files": hashes,
                "hash_convention": "Tracked text CRLF to LF; binaries raw",
                "mutable_exclusions": ["docs/CONTINUOUS_RESEARCH_STATUS.md"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
