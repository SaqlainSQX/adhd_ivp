"""Acquire hash-verified plotting wheels for the project CPU environment."""

import hashlib
import json
import urllib.request
from pathlib import Path

root = Path("/kaggle/working")
packages = [
    ("matplotlib", "3.10.7"),
    ("contourpy", "1.3.3"),
    ("kiwisolver", "1.4.9"),
    ("fonttools", "4.60.1"),
    ("cycler", "0.12.1"),
]
report = []
for package, version in packages:
    with urllib.request.urlopen(
        f"https://pypi.org/pypi/{package}/{version}/json", timeout=30
    ) as response:
        metadata = json.load(response)
    wheel = next(
        row
        for row in metadata["urls"]
        if row["filename"].endswith(("cp313-cp313-win_amd64.whl", "py3-none-any.whl"))
    )
    with urllib.request.urlopen(wheel["url"], timeout=90) as response:
        data = response.read()
    sha = hashlib.sha256(data).hexdigest()
    if sha != wheel["digests"]["sha256"]:
        raise ValueError("Plotting wheel hash mismatch")
    (root / wheel["filename"]).write_bytes(data)
    report.append(
        {
            "package": package,
            "version": version,
            "filename": wheel["filename"],
            "sha256": sha,
            "url": wheel["url"],
        }
    )
(root / "plotting-wheels.json").write_text(json.dumps(report, indent=2))
print("Verified plotting wheels", len(report))
