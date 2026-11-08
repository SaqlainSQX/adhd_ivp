"""Exercise S integrity checks on separate copies, including optimized Python."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / "outputs/submission-synthesis-s-controls-v1"
    output.mkdir(parents=True, exist_ok=False)
    results = []
    for optimized in [False, True]:
        for case in ["intact", "changed-summary", "changed-guide"]:
            folder = output / f"{'optimized' if optimized else 'normal'}-{case}"
            folder.mkdir()
            for name in [
                "registration.json",
                "claim-map.json",
                "guide-summary.json",
                "course-guide.md",
            ]:
                shutil.copyfile(ROOT / "outputs/submission-synthesis-s-v1" / name, folder / name)
            if case == "changed-summary":
                path = folder / "guide-summary.json"
                data = json.loads(path.read_text(encoding="utf-8"))
                data["main_static"]["value"] *= 2
                path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            if case == "changed-guide":
                path = folder / "course-guide.md"
                data = path.read_text(encoding="utf-8")
                summary = json.loads((folder / "guide-summary.json").read_text(encoding="utf-8"))
                token = summary["main_static"]["display"] + "<!-- s:main_static -->"
                if data.count(token) != 1:
                    raise ValueError("Ambiguous guide control marker")
                path.write_text(
                    data.replace(token, "99.9999<!-- s:main_static -->"), encoding="utf-8"
                )
            command = [sys.executable, "-I", "-S"] + (["-O"] if optimized else [])
            command += [str(ROOT / "scripts/check_course_synthesis.py"), "--bundle", str(folder)]
            process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
            (folder / "stdout.log").write_text(process.stdout, encoding="utf-8")
            (folder / "stderr.log").write_text(process.stderr, encoding="utf-8")
            expected = 0 if case == "intact" else 1
            if process.returncode != expected:
                raise ValueError(f"Unexpected S integrity control: {case}")
            results.append(
                {
                    "optimized": optimized,
                    "case": case,
                    "exit_code": process.returncode,
                    "accepted_behavior": True,
                }
            )
    result = {
        "complete": True,
        "cases": results,
        "live_guide_or_sources_modified": False,
        "scope": "copied bundle integrity; not adversarial security or fresh installation",
    }
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
