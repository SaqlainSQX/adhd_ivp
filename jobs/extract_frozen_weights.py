"""Create a tensor-only checkpoint from the official hash-pinned training artifact."""

import hashlib
import json
from pathlib import Path

import torch
from torch.optim.swa_utils import SWALR

root = Path("/kaggle/working")
checkpoint = next(Path("/kaggle/input").rglob("mtgs-vsgaze.ckpt"))
sha = hashlib.sha256()
with checkpoint.open("rb") as handle:
    for block in iter(lambda: handle.read(1024 * 1024), b""):
        sha.update(block)
expected = "1b5db64e2fc13945e07c570a6686efda38c1d99400b263e1b7c80677862c267a"
if sha.hexdigest() != expected:
    raise ValueError("Input checkpoint hash mismatch")
report = {
    "source_sha256": expected,
    "torch_version": torch.__version__,
    "source_kernel": "watasimycola/social-gaze-checkpoint-audit/1",
    "load_mode": "weights_only with explicit training-scheduler globals",
}
try:
    # These two training-state globals were statically inspected in the preceding job.
    with torch.serialization.safe_globals([getattr, SWALR]):
        state = torch.load(checkpoint, map_location="cpu", weights_only=True)
    report["top_level_keys"] = list(state)
    weights = state["state_dict"]
    if not all(isinstance(value, torch.Tensor) for value in weights.values()):
        raise ValueError("Model state contains a non-tensor value")
    report["state_shapes"] = {key: list(value.shape) for key, value in weights.items()}
    report["hyper_parameters"] = str(state.get("hyper_parameters", {}))[:100000]
    target = root / "mtgs-state-dict.pt"
    torch.save(dict(weights), target)
    report["tensor_checkpoint_sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
    report["tensor_checkpoint_bytes"] = target.stat().st_size
    report["complete"] = True
except Exception as error:
    report["complete"] = False
    report["error"] = str(error)
(root / "frozen-weights.json").write_text(json.dumps(report, indent=2))
print(json.dumps({key: value for key, value in report.items() if key != "state_shapes"}, indent=2))
