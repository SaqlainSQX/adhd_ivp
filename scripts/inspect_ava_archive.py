"""Download the registered AVA annotation archive and inspect member metadata only."""

import hashlib
import json
import tarfile
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = "https://www.robots.ox.ac.uk/~vgg/research/laeonet/downloads/ava_laeo.tar.gz"
CAP = 64 * 1024 * 1024


def main():
    output = ROOT / "outputs/external-metadata-j-v1"
    destination = ROOT / "data/research/ava-laeo-metadata-j-v1"
    destination.mkdir(parents=True, exist_ok=False)
    target = destination / "ava_laeo.tar.gz"
    digest = hashlib.sha256()
    total = 0
    with urllib.request.urlopen(URL, timeout=20) as response, target.open("xb") as handle:
        assert int(response.headers.get("Content-Length", CAP + 1)) <= CAP
        while chunk := response.read(1024 * 1024):
            total += len(chunk)
            if total > CAP:
                raise ValueError("Registered annotation download cap exceeded")
            handle.write(chunk)
            digest.update(chunk)
    with tarfile.open(target, "r:gz") as archive:
        members = [{"name": m.name, "bytes": m.size, "file": m.isfile()}
                   for m in archive.getmembers()]
    (output / "archive-members.json").write_text(json.dumps(members, indent=2) + "\n")
    result = {
        "stage": "J-annotation-archive-members-only", "created_utc":
        datetime.now(timezone.utc).isoformat(), "url": URL, "bytes": total,
        "sha256": digest.hexdigest(), "member_count": len(members),
        "file_count": sum(m["file"] for m in members),
        "suffix_counts": dict(Counter(Path(m["name"]).suffix for m in members if m["file"])),
        "annotation_values_read": False, "archive_extracted": False,
        "media_downloaded": False, "performance_evaluated": False,
    }
    (output / "archive-metadata.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    print("FIRST_MEMBER_NAMES", [m["name"] for m in members[:12]])


if __name__ == "__main__":
    main()
