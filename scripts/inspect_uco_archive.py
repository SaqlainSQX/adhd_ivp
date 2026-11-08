"""K1 post-download member/terms inspection; no extraction or label reads."""

import hashlib
import json
import re
import tarfile
from collections import Counter
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/uco-archive-k2-v1"


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    status = json.loads((ROOT / "outputs/uco-acquisition-k-v1/status.json").read_text())
    path = ROOT / status["file"]
    assert path.stat().st_size == status["bytes"] == 4066161261
    with path.open("rb") as handle:
        sha = hashlib.file_digest(handle, "sha256").hexdigest()
    assert sha == status["sha256"]
    members, unsafe, documents = [], [], []
    with tarfile.open(path, "r|gz") as archive:
        for member in archive:
            name = member.name.replace("\\", "/")
            parts = PurePosixPath(name).parts
            safe = not (name.startswith("/") or ".." in parts or ":" in name)
            safe = safe and (member.isfile() or member.isdir())
            if not safe:
                unsafe.append(name)
            members.append({"name": name, "bytes": member.size,
                            "file": member.isfile(), "safe": safe})
            base = PurePosixPath(name).name.lower()
            if (safe and member.isfile() and member.size <= 65536
                    and re.match(r"^(readme|licen[cs]e|copying|terms)(\.|$)", base)):
                content = archive.extractfile(member).read()
                target = OUT / f"document-{len(documents)}.txt"
                target.write_bytes(content)
                documents.append({"member": name, "local": str(target.relative_to(ROOT)),
                                  "sha256": hashlib.sha256(content).hexdigest()})
    (OUT / "members.json").write_text(json.dumps(members, indent=2) + "\n")
    images = [m for m in members if m["file"] and m["name"].lower().endswith(".jpg")]
    result = {"stage": "K1-archive-integrity-members", "archive_sha256": sha,
              "archive_bytes": path.stat().st_size, "members": len(members),
              "unsafe_members": unsafe, "documents": documents,
              "regular_files": sum(m["file"] for m in members),
              "total_regular_bytes": sum(m["bytes"] for m in members if m["file"]),
              "jpeg_count": len(images), "jpeg_bytes": sum(m["bytes"] for m in images),
              "jpeg_parent_counts": dict(Counter(str(PurePosixPath(m["name"]).parent)
                                                  for m in images)),
              "labels_read": False, "media_extracted": False, "inference_started": False}
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "jpeg_parent_counts"}, indent=2))
    print("FIRST_MEMBERS", [m["name"] for m in members[:14]])
    print("IMAGE_PARENT_EXAMPLES", list(result["jpeg_parent_counts"].items())[:6])


if __name__ == "__main__":
    main()
