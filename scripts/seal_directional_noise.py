"""Hash aggregate R delivery without altering any prior evidence manifest."""

import hashlib
import json
from pathlib import Path


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    checked = 0
    for path in Path("docs/research").glob("*evidence-manifest.json"):
        if path.name == "r-evidence-manifest.json":
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for name, expected in payload.get("files", {}).items():
            raw = Path(name).read_bytes()
            if expected not in (digest(raw), digest(raw.replace(b"\r\n", b"\n"))):
                raise ValueError(f"Prior evidence changed: {name}")
            checked += 1
    names = [
        "src/gaze_audit/directional_noise.py",
        "configs/directional-noise-r-v1.json",
        "scripts/register_directional_noise.py",
        "scripts/run_directional_noise.py",
        "scripts/validate_directional_noise.py",
        "scripts/report_directional_noise.py",
        "scripts/archive_directional_noise.py",
        "scripts/seal_directional_noise.py",
        "docs/DIRECTIONAL_NOISE_R_RESULTS.md",
        "docs/ASYMMETRIC_NOISE_R.md",
        "docs/SUBMISSION_SYNTHESIS_S.md",
        "reports/course-project/directional-noise-r.png",
        "reports/course-project/directional-noise-r.pdf",
    ]
    names += [
        p.as_posix()
        for p in Path("docs/research").glob("r-*.json")
        if p.name != "r-evidence-manifest.json"
    ]
    names += [p.as_posix() for p in Path("docs/research").glob("directional-noise-r-*.log")]
    files = {}
    for name in sorted(set(names)):
        raw = Path(name).read_bytes()
        if Path(name).suffix not in (".png", ".pdf"):
            raw = raw.replace(b"\r\n", b"\n")
        files[name] = digest(raw)
    output = {
        "stage": "R directional synthetic label-error sensitivity",
        "hash_convention": "Tracked text CRLF to LF; binaries and local files raw",
        "files": files,
        "prior_manifest_file_checks": checked,
        "local_files": {
            "outputs/directional-noise-r-v1/draw-results.csv": digest(
                Path("outputs/directional-noise-r-v1/draw-results.csv").read_bytes()
            )
        },
        "mutable_exclusions": ["docs/CONTINUOUS_RESEARCH_STATUS.md"],
    }
    Path("docs/research/r-evidence-manifest.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Sealed {len(files)} R delivery files; {checked} prior manifest entries intact")


if __name__ == "__main__":
    main()
