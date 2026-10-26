"""Acquire official DINO source and hash-verified small runtime wheels for local inference."""

import hashlib
import json
import urllib.request
from pathlib import Path

root = Path("/kaggle/working")


def fetch(url):
    with urllib.request.urlopen(url, timeout=90) as response:
        return response.read()


commit = json.loads(fetch("https://api.github.com/repos/facebookresearch/dinov2/commits/main"))
revision = commit["sha"]
source = fetch(f"https://codeload.github.com/facebookresearch/dinov2/zip/{revision}")
(root / "dinov2-source.zip").write_bytes(source)
report = {
    "dinov2": {
        "repository": "facebookresearch/dinov2",
        "revision": revision,
        "zip_sha256": hashlib.sha256(source).hexdigest(),
        "zip_bytes": len(source),
    },
    "wheels": [],
}
for package, version in [
    ("einops", "0.6.0"),
    ("timm", "0.9.2"),
    ("torch-geometric", "2.7.0"),
    ("xxhash", "3.6.0"),
]:
    metadata = json.loads(fetch(f"https://pypi.org/pypi/{package}/{version}/json"))
    candidates = [
        r
        for r in metadata["urls"]
        if r["filename"].endswith(("py3-none-any.whl", "cp313-cp313-win_amd64.whl"))
    ]
    wheel = candidates[0]
    content = fetch(wheel["url"])
    if hashlib.sha256(content).hexdigest() != wheel["digests"]["sha256"]:
        raise ValueError("PyPI wheel hash mismatch")
    (root / wheel["filename"]).write_bytes(content)
    report["wheels"].append(
        {
            "package": package,
            "version": version,
            "filename": wheel["filename"],
            "url": wheel["url"],
            "sha256": wheel["digests"]["sha256"],
            "bytes": len(content),
        }
    )
(root / "inference-assets.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
