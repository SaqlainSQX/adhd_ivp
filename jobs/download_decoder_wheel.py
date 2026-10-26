"""Relay an official, hash-verified Windows decoder wheel through private Kaggle output."""

import hashlib
import json
import urllib.request
from pathlib import Path

root = Path("/kaggle/working")
with urllib.request.urlopen(
    "https://pypi.org/pypi/opencv-python-headless/5.0.0.93/json", timeout=30
) as r:
    metadata = json.load(r)
wheel = next(row for row in metadata["urls"] if row["filename"].endswith("cp37-abi3-win_amd64.whl"))
target = root / wheel["filename"]
sha = hashlib.sha256()
with urllib.request.urlopen(wheel["url"], timeout=90) as response, target.open("wb") as handle:
    while block := response.read(1024 * 1024):
        sha.update(block)
        handle.write(block)
if sha.hexdigest() != wheel["digests"]["sha256"] or target.stat().st_size != wheel["size"]:
    raise ValueError("Official PyPI wheel hash mismatch")
(root / "wheel-provenance.json").write_text(
    json.dumps(
        {
            "filename": target.name,
            "sha256": sha.hexdigest(),
            "bytes": target.stat().st_size,
            "url": wheel["url"],
            "metadata": "https://pypi.org/pypi/opencv-python-headless/5.0.0.93/json",
        },
        indent=2,
    )
)
print("Official wheel verified", target.name)
