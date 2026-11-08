"""Publish the checked S documentation without modifying historical artifacts."""

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    bundle = ROOT / "outputs/submission-synthesis-s-v1"
    process = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            str(ROOT / "scripts/check_course_synthesis.py"),
            "--bundle",
            str(bundle),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    proof = json.loads(process.stdout)
    controls = json.loads(
        (ROOT / "outputs/submission-synthesis-s-controls-v1/result.json").read_text(
            encoding="utf-8"
        )
    )
    if len(controls["cases"]) != 6 or not all(c["accepted_behavior"] for c in controls["cases"]):
        raise ValueError("S integrity controls incomplete")
    copies = {bundle / "course-guide.md": ROOT / "docs/COURSE_PROJECT_GUIDE_S.md"}
    for name in [
        "claim-map.json",
        "guide-summary.json",
        "registration.json",
        "independent-validation.json",
    ]:
        copies[bundle / name] = ROOT / "docs/research" / ("s-" + name)
    copies[ROOT / "outputs/submission-synthesis-s-controls-v1/result.json"] = (
        ROOT / "docs/research/s-controls-result.json"
    )
    for name in [
        "submission-synthesis-s-v1-build.log",
        "submission-synthesis-s-v1-check.log",
        "submission-synthesis-s-controls-v1.log",
    ]:
        copies[ROOT / "outputs" / name] = ROOT / "docs/research" / name
    if any(path.exists() for path in copies.values()):
        raise FileExistsError("S delivery exists; register a versioned repair instead")
    for source, target in copies.items():
        shutil.copyfile(source, target)
    status = {
        "complete": True,
        "stage": "S course guide and checked claim map",
        "scientific_outcomes_created": False,
        "claims_checked": proof["claims_independently_resolved"],
        "aggregate_sources": proof["aggregate_sources"],
        "local_links_checked": proof["local_links_checked"],
        "prior_manifest_entries_checked": proof["prior_manifest_entries_checked"],
        "normal_and_optimized_integrity_controls": 6,
        "main_evidence_unchanged": proof["main_result_and_lock_unchanged"],
        "new_figure_created": False,
        "scope": "this PC and accepted saved evidence",
        "branch": "codex/course-synthesis-s-v1",
        "next": "docs/COVERAGE_MC_T.md",
    }
    (bundle / "status.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    (ROOT / "docs/research/s-status.json").write_text(
        json.dumps(status, indent=2) + "\n", encoding="utf-8"
    )
    names = [p.relative_to(ROOT).as_posix() for p in copies.values()]
    names += [
        "docs/research/s-status.json",
        "docs/SUBMISSION_SYNTHESIS_S.md",
        "docs/COVERAGE_MC_T.md",
        "docs/templates/course-guide-s.md",
        "scripts/build_course_synthesis.py",
        "scripts/check_course_synthesis.py",
        "scripts/check_synthesis_controls.py",
        "scripts/archive_course_synthesis.py",
    ]
    files = {
        name: hashlib.sha256((ROOT / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        for name in sorted(names)
    }
    local = {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (ROOT / "outputs/submission-synthesis-s-controls-v1").glob("*/*.log")
    }
    manifest = {
        "stage": "S reporting and claim traceability; no new science",
        "hash_convention": "Tracked text CRLF to LF; local logs raw",
        "files": files,
        "local_files": local,
        "mutable_exclusions": ["docs/CONTINUOUS_RESEARCH_STATUS.md"],
    }
    (ROOT / "docs/research/s-evidence-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
