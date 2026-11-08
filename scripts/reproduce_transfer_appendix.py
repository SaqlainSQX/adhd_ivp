"""O: reproduce the pinned appendix in source-only trees using Python -I -S."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "src/gaze_audit/__init__.py",
    "src/gaze_audit/transfer_appendix.py",
    "scripts/build_transfer_appendix.py",
    "scripts/serve_transfer_appendix.py",
    "demo/transfer/index.html",
    "demo/transfer/style.css",
    "demo/transfer/app.js",
    "demo/research/data.json",
    "docs/research/l-transfer-result.json",
    "docs/research/m-variance-result.json",
    "docs/research/h-evidence-manifest.json",
    "docs/research/l-transfer-evidence-manifest.json",
    "docs/research/m-evidence-manifest.json",
]
MISSING = "docs/research/l-transfer-result.json"

PROGRAM = r"""
import json, runpy, sys
from pathlib import Path
root = Path.cwd().resolve()
sys.path.insert(0, str(root / "src"))
opens = []
def observe(event, args):
    if event == "open" and isinstance(args[0], (str, bytes)):
        path = Path(args[0]).resolve()
        if path.is_relative_to(root):
            opens.append(str(path.relative_to(root)))
sys.addaudithook(observe)
runpy.run_path(str(root / "scripts/build_transfer_appendix.py"), run_name="__main__")
import gaze_audit.transfer_appendix as module
assert Path(module.__file__).resolve() == root / "src/gaze_audit/transfer_appendix.py"
blocked = [name for name in ["site", "numpy", "pandas", "torch", "sklearn"] if name in sys.modules]
assert not blocked, blocked
report = {"staged_module_used": True, "site_or_scientific_packages_loaded": blocked,
          "staged_files_opened": sorted(set(opens)),
          "interpreter_flags": {"isolated": sys.flags.isolated, "no_site": sys.flags.no_site}}
(root / "child-proof.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
"""


def digest(data):
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def main(output):
    output = output.resolve()
    if not output.is_relative_to(ROOT / "outputs"):
        raise ValueError("Use a new output directory inside the project outputs folder")
    tracked = set(subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines())
    assert set(FILES) <= tracked
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    output.mkdir(parents=True, exist_ok=False)
    expected = {
        name: digest((ROOT / name).read_bytes())
        for name in ["demo/transfer/data.json", "demo/transfer/data.js"]
    }
    registration = {
        "stage": "O-source-only-reproduction",
        "source_commit": commit,
        "protocol_sha256": digest((ROOT / "docs/TEAM_REPRODUCIBILITY_O.md").read_bytes()),
        "implementation_sha256": digest(Path(__file__).read_bytes()),
        "input_sha256": {name: digest((ROOT / name).read_bytes()) for name in FILES},
        "expected_output_sha256": expected,
        "child_program_sha256": digest(PROGRAM.encode()),
        "cases_registered_before_run": ["success", "tampered", "missing"],
    }
    (output / "registration.json").write_text(json.dumps(registration, indent=2) + "\n")
    cases = []
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    for case in registration["cases_registered_before_run"]:
        stage = output / (case + "-tree")
        stage.mkdir()
        for name in FILES:
            if case == "missing" and name == MISSING:
                continue
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / name).read_bytes().replace(b"\r\n", b"\n"))
        if case == "tampered":
            target = stage / MISSING
            target.write_bytes(target.read_bytes() + b"\n ")
        for forbidden in ["data", "outputs", "external", "checkpoints", ".venv", ".venv-mtgs"]:
            assert not (stage / forbidden).exists()
        command = [sys.executable, "-I", "-S", "-c", PROGRAM]
        run = subprocess.run(
            command, cwd=stage, env=env, capture_output=True, text=True, timeout=30
        )
        (output / f"{case}-stdout.log").write_text(run.stdout, encoding="utf-8")
        (output / f"{case}-stderr.log").write_text(run.stderr, encoding="utf-8")
        evidence = {
            "case": case,
            "exit_code": run.returncode,
            "no_raw_model_or_environment_directories": True,
        }
        if case == "success":
            assert run.returncode == 0, run.stderr
            for name, expected_hash in expected.items():
                assert digest((stage / name).read_bytes()) == expected_hash
            proof = json.loads((stage / "child-proof.json").read_text())
            assert proof["interpreter_flags"] == {"isolated": 1, "no_site": 1}
            evidence.update(outputs_match_registered_hashes=True, **proof)
        else:
            error = "AssertionError" if case == "tampered" else "FileNotFoundError"
            assert run.returncode != 0 and error in run.stderr
            assert not (stage / "demo/transfer/data.json").exists()
            assert not (stage / "demo/transfer/data.js").exists()
            evidence.update(failure_detected_as_registered=error, no_export_generated=True)
        cases.append(evidence)
    result = {
        "complete": True,
        "source_commit": commit,
        "tracked_input_files": len(FILES),
        "cases": cases,
        "output_hashes": expected,
        "new_dependency_installation_claimed": False,
        "cross_platform_claimed": False,
        "raw_data_models_GPU_packages_needed": False,
        "browser_download_capture_limitation_unchanged": True,
    }
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/team-reproduction-o-v1")
    args = parser.parse_args()
    main(args.output)
