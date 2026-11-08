"""Frozen L UCO inference, using public files only and never opening the oracle."""

import csv
import hashlib
import json
import os
import platform
import sys
import time
from functools import lru_cache
from pathlib import Path

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import torch
from PIL import Image

from gaze_audit.mtgs_runtime import (
    load_model,
    prepare_public_frame,
    prepare_window,
    prune_unused_heatmap,
)
from gaze_audit.uco_inference import decode_scores, load_public

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/uco-transfer-l-v1.json"


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def main():
    cfg = json.loads(CONFIG.read_text())
    out = ROOT / cfg["score_cache"]
    if out.exists():
        raise ValueError("Preserve old inference evidence; choose a registered new version")
    # External reference/mask bytes are not opened here, even for hashing.
    checked = {}
    for relative, expected in cfg["input_sha256"].items():
        if Path(relative).name in ("oracle.csv", "ambiguity-mask.json"):
            continue
        actual = sha(ROOT / relative)
        if actual != expected:
            raise ValueError(f"Frozen public/runtime hash mismatch: {relative}")
        checked[relative] = actual
    checkpoint = ROOT / "checkpoints/mtgs-dino-vsgaze/mtgs-state-dict.pt"
    assert sha(checkpoint) == cfg["checkpoint_sha256"]
    frames, people, pairs = load_public(ROOT)
    assert sum(map(len, pairs.values())) == cfg["population_size"]
    assert torch.cuda.is_available()
    torch.set_num_threads(4)
    torch.manual_seed(42)
    np.random.seed(42)
    torch.backends.cudnn.benchmark = False
    torch.use_deterministic_algorithms(True)
    torch.cuda.set_per_process_memory_fraction(0.5)
    out.mkdir(parents=True)
    report = {
        "stage": "L-inference",
        "complete": False,
        "status": "loading_model",
        "pid": os.getpid(),
        "oracle_opened": False,
        "reference_values_used": False,
        "config_sha256": sha(CONFIG),
        "implementation_sha256": sha(Path(__file__)),
        "public_adapter_sha256": sha(ROOT / "src/gaze_audit/uco_inference.py"),
        "verified_inputs": checked,
        "checkpoint_sha256": cfg["checkpoint_sha256"],
        "clips": [],
        "processed_anchor_frames": 0,
        "precision": "float16-autocast",
        "memory_fraction": 0.5,
        "upstream_geometry": cfg["upstream_geometry"],
        "runtime": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0),
        },
    }

    def save():
        temp = out / "provenance.tmp"
        temp.write_text(json.dumps(report, indent=2) + "\n")
        temp.replace(out / "inference-provenance.json")

    save()
    started = time.monotonic()
    try:
        model, square = load_model(
            ROOT / "external/MTGS-pinned", ROOT / "external/dinov2-pinned", checkpoint
        )
        # Auxiliary-only pruning was validated in the existing same-checkpoint runtime lock.
        lock_path = ROOT / "outputs/inference/mtgs-smoke-cache-v1/inference-provenance.json"
        lock = json.loads(lock_path.read_text())
        assert lock["complete"] and lock.get("amp_development_check")
        assert lock.get("auxiliary_pruning_verified")
        report["existing_runtime_lock_sha256"] = sha(lock_path)
        prune_unused_heatmap(model)
        report["auxiliary_pruning"] = "reuse same-checkpoint auxiliary independence validation"

        def image_loader(path):
            with Image.open(ROOT / "data/processed/uco-public-k2-v1/images" / path) as image:
                return image.convert("RGB")

        by_id = {row["frame_id"]: row for row in frames.values()}

        @lru_cache(maxsize=64)
        def prepared(fid):
            return prepare_public_frame(by_id[fid], people, image_loader, square)

        with torch.inference_mode():
            for clip in sorted({key[0] for key in frames}):
                rows = []
                for key in sorted(k for k in frames if k[0] == clip):
                    anchor = frames[key]
                    if anchor["frame_id"] not in pairs:
                        continue
                    inputs, pids = prepare_window(
                        anchor, frames, people, image_loader, square, prepared_loader=prepared
                    )
                    if "amp_uco_check" not in report:
                        uncached, ids = prepare_window(anchor, frames, people, image_loader, square)
                        assert ids == pids and all(
                            torch.equal(inputs[k], uncached[k]) for k in inputs
                        )
                        del uncached
                        report["first_public_cached_uncached_input_parity"] = True
                        reference = model(inputs)
                        native = [reference[i].float().sigmoid().cpu() for i in (4, 5)]
                        del reference
                        with torch.autocast("cuda", dtype=torch.float16):
                            accelerated = model(inputs)
                        differences = [
                            float((before - accelerated[i].float().sigmoid().cpu()).abs().max())
                            for before, i in zip(native, (4, 5), strict=True)
                        ]
                        assert max(differences) <= 0.002, "UCO AMP probability tolerance exceeded"
                        report["amp_uco_check"] = {
                            "max_abs_LAH_LAEO": differences,
                            "tolerance": 0.002,
                            "scope": "first public UCO window, no labels",
                        }
                        del native, accelerated
                    with torch.autocast("cuda", dtype=torch.float16):
                        output = model(inputs)
                    lah = output[4][0, 2].float().sigmoid().cpu().numpy()
                    laeo = output[5][0, 2].float().sigmoid().cpu().numpy()
                    rows.extend(decode_scores(lah, pids, pairs[anchor["frame_id"]], laeo))
                    del output, inputs
                    report["processed_anchor_frames"] += 1
                    if report["processed_anchor_frames"] % 25 == 0:
                        report.update(status="running", elapsed_seconds=time.monotonic() - started)
                        save()
                        print(
                            f"UCO anchors completed: {report['processed_anchor_frames']}",
                            flush=True,
                        )
                target = out / f"predictions-{clip}.csv"
                with target.open("x", newline="") as handle:
                    writer = csv.DictWriter(
                        handle,
                        fieldnames=["record_id", "q", "direction_a_to_b", "direction_b_to_a"],
                    )
                    writer.writeheader()
                    writer.writerows(rows)
                report["clips"].append(
                    {"clip": clip, "rows": len(rows), "file": target.name, "sha256": sha(target)}
                )
                prepared.cache_clear()
                save()
        assert sum(c["rows"] for c in report["clips"]) == cfg["population_size"]
        report.update(
            complete=True,
            status="complete",
            elapsed_seconds=time.monotonic() - started,
            peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),
        )
        save()
    except Exception as error:
        report.update(status="failed", error_type=type(error).__name__, error=str(error))
        save()
        raise


if __name__ == "__main__":
    main()
