"""Inspect the official ChildPlay-Hand archive for reusable ChildPlay media."""

import json
import tarfile
import urllib.request
from pathlib import Path

root = Path("/kaggle/working")
url = "https://zenodo.org/records/14958923/files/childplay_hand.tar.gz?download=1"
report = {"url": url, "members": [], "media_found": False}
with urllib.request.urlopen(url, timeout=90) as response:
    with tarfile.open(fileobj=response, mode="r|gz") as archive:
        for index, member in enumerate(archive):
            report["members"].append({"path": member.name, "bytes": member.size})
            if member.name.lower().endswith((".mp4", ".jpg", ".png", ".avi")):
                report["media_found"] = True
                break
            if member.name.lower().endswith(("readme.md", "readme.txt")) and member.size < 100000:
                (root / "alternative-readme.txt").write_bytes(archive.extractfile(member).read())
            if index >= 500:
                break
(root / "alternative-media-inspection.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
