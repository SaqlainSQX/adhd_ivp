"""Acquire a revision-pinned official checkpoint and inspect it without executing pickle globals."""

import hashlib
import json
import pickletools
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

root = Path("/kaggle/working")
revision = "1b8b24a275fa2afe2e39d057291975bd87add35f"
repository = "Idiap/mtgs-vsgaze"


def fetch(url):
    with urllib.request.urlopen(url, timeout=90) as response:
        return response.read()


tree = json.loads(
    fetch(f"https://huggingface.co/api/models/{repository}/tree/{revision}?expand=true")
)
entry = next(row for row in tree if row["path"] == "mtgs-vsgaze.ckpt")
expected = entry["lfs"]["oid"]
url = f"https://huggingface.co/{repository}/resolve/{revision}/mtgs-vsgaze.ckpt?download=true"
checkpoint = root / "mtgs-vsgaze.ckpt"
sha = hashlib.sha256()
with urllib.request.urlopen(url, timeout=120) as response, checkpoint.open("wb") as handle:
    while chunk := response.read(1024 * 1024):
        handle.write(chunk)
        sha.update(chunk)
if sha.hexdigest() != expected or checkpoint.stat().st_size != entry["size"]:
    raise ValueError("Official checkpoint does not match pinned LFS object")
report = {
    "repository": repository,
    "revision": revision,
    "url": url,
    "sha256": sha.hexdigest(),
    "bytes": checkpoint.stat().st_size,
    "unsafe_pickle_execution": False,
}
with zipfile.ZipFile(checkpoint) as archive:
    member = next(name for name in archive.namelist() if name.endswith("/data.pkl"))
    data = archive.read(member)
    strings, globals_found = [], []
    for operation, value, _position in pickletools.genops(data):
        if operation.name in {"BINUNICODE", "SHORT_BINUNICODE", "UNICODE"}:
            strings.append(value)
        if operation.name == "GLOBAL":
            globals_found.append(value)
    report["pickle_globals"] = sorted(set(globals_found))
    (root / "checkpoint-strings.json").write_text(json.dumps(strings, indent=2))
try:
    import torch

    report["torch_version"] = torch.__version__
    report["unsafe_globals"] = torch.serialization.get_unsafe_globals_in_checkpoint(checkpoint)
    weights = torch.load(checkpoint, map_location="cpu", weights_only=True)
    report["top_level_keys"] = list(weights)
    state = weights.get("state_dict", weights)
    report["state_shapes"] = {
        key: list(value.shape) for key, value in state.items() if hasattr(value, "shape")
    }
    report["hyper_parameters"] = str(weights.get("hyper_parameters", {}))[:100000]
except Exception as error:
    report["safe_weight_load_error"] = str(error)[:4000]
(root / "checkpoint-provenance.json").write_text(json.dumps(report, indent=2))
print(json.dumps({key: value for key, value in report.items() if key != "state_shapes"}, indent=2))
