"""Seal Q aggregate delivery after validation and check prior tracked evidence."""

import hashlib
import json
from pathlib import Path


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    checked = 0
    for manifest in Path("docs/research").glob("*evidence-manifest.json"):
        if manifest.name == "q-evidence-manifest.json":
            continue
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        for name, expected in payload.get("files", {}).items():
            raw = Path(name).read_bytes()
            if expected not in (digest(raw), digest(raw.replace(b"\r\n", b"\n"))):
                raise ValueError(f"Prior evidence differs: {manifest}: {name}")
            checked += 1
    sources = [
        "src/gaze_audit/query_noise.py",
        "scripts/run_query_noise.py",
        "scripts/run_query_noise_v2.py",
        "scripts/validate_query_noise.py",
        "scripts/report_query_noise.py",
        "scripts/archive_query_noise.py",
        "scripts/seal_query_noise.py",
        "configs/query-noise-q-v1.json",
        "configs/query-noise-q-v2.json",
        "docs/QUERY_NOISE_Q_REPAIR.md",
        "docs/QUERY_NOISE_Q_RESULTS.md",
        "docs/ASYMMETRIC_NOISE_R.md",
        "reports/course-project/query-noise-q.png",
        "reports/course-project/query-noise-q.pdf",
    ]
    sources += [p.as_posix() for p in Path("docs/research").glob("q-*")]
    sources += [p.as_posix() for p in Path("docs/research").glob("query-noise-q-*.log")]
    files = {}
    for name in sorted(set(sources)):
        if name.endswith("q-evidence-manifest.json"):
            continue
        raw = Path(name).read_bytes()
        if Path(name).suffix not in (".png", ".pdf"):
            raw = raw.replace(b"\r\n", b"\n")
        files[name] = digest(raw)
    local_names = [
        "outputs/query-noise-q-v1/implementation.py",
        "outputs/query-noise-q-v2/draw-results.csv",
        "outputs/query-noise-q-v2-validation-formatted.log",
    ]
    manifest = {
        "stage": "Q synthetic symmetric query-label error sensitivity",
        "hash_convention": "Tracked text normalized CRLF to LF; binaries/local files raw",
        "files": files,
        "local_files": {name: digest(Path(name).read_bytes()) for name in local_names},
        "prior_manifest_file_checks": checked,
        "mutable_exclusions": ["docs/CONTINUOUS_RESEARCH_STATUS.md"],
    }
    Path("docs/research/q-evidence-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Sealed {len(files)} Q files; {checked} prior manifest entries intact")


if __name__ == "__main__":
    main()
