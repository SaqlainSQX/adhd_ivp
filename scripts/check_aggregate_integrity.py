"""P six-case source-only check of normal/optimized aggregate validation."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from reproduce_transfer_appendix import FILES, MISSING

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main(phase, output):
    output = output.resolve()
    if not output.is_relative_to(ROOT / "outputs"):
        raise ValueError("Use a new directory inside project outputs")
    output.mkdir(parents=True, exist_ok=False)
    files = list(FILES)
    entry = "scripts/build_transfer_appendix.py"
    if phase == "verified":
        files += [
            "src/gaze_audit/verified_transfer_appendix.py",
            "scripts/build_verified_transfer_appendix.py",
        ]
        entry = "scripts/build_verified_transfer_appendix.py"
    program = (
        "import sys,runpy;from pathlib import Path;"
        "sys.path.insert(0,str(Path.cwd()/'src'));"
        f"runpy.run_path({entry!r},run_name='__main__')"
    )
    expected = {
        name: digest(ROOT / name) for name in ["demo/transfer/data.json", "demo/transfer/data.js"]
    }
    registration = {
        "phase": phase,
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "protocol_sha256": digest(ROOT / "docs/AGGREGATE_INTEGRITY_P.md"),
        "implementation_sha256": digest(Path(__file__)),
        "input_sha256": {p: digest(ROOT / p) for p in files},
        "expected_output_sha256": expected,
        "registered_modes": [["-I", "-S"], ["-I", "-S", "-O"]],
        "registered_cases": ["intact", "missing", "numerically_changed"],
        "numeric_change": "double copied UCO K4-b521 rmse_pp only",
        "program": program,
    }
    if phase == "verified":
        registration["repair_protocol_sha256"] = digest(
            ROOT / "docs/AGGREGATE_INTEGRITY_P_REPAIR.md"
        )
    (output / "registration.json").write_text(json.dumps(registration, indent=2) + "\n")
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    results = []
    for mode in ["normal", "optimized"]:
        for case in registration["registered_cases"]:
            stage = output / f"{mode}-{case}"
            stage.mkdir()
            for name in files:
                if case == "missing" and name == MISSING:
                    continue
                target = stage / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / name).read_bytes().replace(b"\r\n", b"\n"))
            if case == "numerically_changed":
                target = stage / MISSING
                modified = json.loads(target.read_text())
                modified["results"]["K4-b521"]["rmse_pp"] *= 2
                target.write_text(json.dumps(modified, indent=2) + "\n")
            flags = ["-I", "-S"] + (["-O"] if mode == "optimized" else [])
            command = [sys.executable, *flags, "-c", program]
            run = subprocess.run(
                command, cwd=stage, env=env, capture_output=True, text=True, timeout=30
            )
            (output / f"{mode}-{case}.stdout.log").write_text(run.stdout)
            (output / f"{mode}-{case}.stderr.log").write_text(run.stderr)
            generated = [name for name in expected if (stage / name).exists()]
            row = {
                "mode": mode,
                "case": case,
                "exit_code": run.returncode,
                "generated_exports": len(generated),
            }
            if case == "intact":
                passed = run.returncode == 0 and all(
                    (stage / name).exists() and digest(stage / name) == checksum
                    for name, checksum in expected.items()
                )
                row["outputs_match_baseline"] = passed
            else:
                passed = run.returncode != 0 and not generated
                row["changed_or_missing_input_rejected_before_export"] = passed
                if generated and case == "numerically_changed":
                    data = json.loads((stage / "demo/transfer/data.json").read_text())
                    bad = next(
                        r for r in data["uco"]["rows"] if r["method"] == "K4" and r["budget"] == 521
                    )
                    baseline = json.loads((ROOT / MISSING).read_text())
                    row["copied_numeric_change_reached_export"] = (
                        bad["rmse_pp"] == baseline["results"]["K4-b521"]["rmse_pp"] * 2
                    )
            row["accepted_behavior"] = passed
            results.append(row)
    result = {
        "complete": True,
        "phase": phase,
        "cases": results,
        "all_six_cases_accepted": all(r["accepted_behavior"] for r in results),
        "live_source_data_changed": False,
        "new_scientific_outcomes": False,
    }
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if phase == "verified" and not result["all_six_cases_accepted"]:
        raise RuntimeError("Registered repaired integrity controls did not all pass")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["baseline", "verified"])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    main(args.phase, args.output)
