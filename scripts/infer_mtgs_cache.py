"""Frozen, geometry-only MTGS inference over verified source JPEG archives."""

import argparse
import csv
import hashlib
import io
import itertools
import json
import os
import platform
import sys
import tarfile
import time
from functools import lru_cache
from pathlib import Path

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd
import torch
from PIL import Image

from gaze_audit.mtgs_runtime import (
    MODEL_SETTINGS,
    load_model,
    prepare_public_frame,
    prepare_window,
    prune_unused_heatmap,
)

CHECKPOINT_SHA256 = "5599382ab78f3993d31300f4e16ed13bc20bed26d7ec9735a37473eb374d994f"


def sha256(path):
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed", type=Path, default=Path("data/processed/vsgaze-17357752-v1"))
    parser.add_argument("--acquisition", type=Path, required=True)
    parser.add_argument("--mtgs-root", type=Path, default=Path("external/MTGS-pinned"))
    parser.add_argument("--dino-root", type=Path, default=Path("external/dinov2-pinned"))
    parser.add_argument(
        "--checkpoint", type=Path, default=Path("checkpoints/mtgs-dino-vsgaze/mtgs-state-dict.pt")
    )
    parser.add_argument("--sources", nargs="*")
    parser.add_argument("--max-frames", type=int)
    parser.add_argument("--benchmark-batches", action="store_true")
    parser.add_argument(
        "--amp", action="store_true", help="Validated float16 autocast for native heads"
    )
    parser.add_argument("--memory-fraction", type=float, default=0.5)
    parser.add_argument("--no-preprocess-cache", action="store_true")
    parser.add_argument("--runtime-lock", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new inference output directory")
    if not torch.cuda.is_available():
        raise RuntimeError("This run requires a verified CUDA runtime")
    if sha256(args.checkpoint) != CHECKPOINT_SHA256:
        raise ValueError("Frozen tensor checkpoint hash mismatch")
    torch.set_num_threads(4)
    torch.manual_seed(42)
    np.random.seed(42)
    torch.backends.cudnn.benchmark = False
    torch.use_deterministic_algorithms(True)
    torch.cuda.set_per_process_memory_fraction(args.memory_fraction)
    acquisition = json.loads((args.acquisition / "acquisition.json").read_text())
    sources = [
        s
        for s in acquisition["sources"]
        if s["status"] == "complete" and (not args.sources or s["source_id"] in args.sources)
    ]
    if not sources:
        raise ValueError("No completed public media sources selected")
    frames = pd.read_csv(args.processed / "public/frames.csv")
    frames = frames[frames.source_id.isin([s["source_id"] for s in sources])]
    people = pd.read_csv(args.processed / "public/public_people.csv")
    people = people[people.frame_id.isin(frames.frame_id) & (people.geometry_valid == 1)]
    pairs = pd.read_csv(
        args.processed / "public/public_pairs.csv",
        usecols=[
            "record_id",
            "frame_id",
            "source_id",
            "clip_id",
            "person_a",
            "person_b",
            "geometry_valid",
        ],
    )
    pairs = pairs[pairs.frame_id.isin(frames.frame_id) & (pairs.geometry_valid == 1)]
    pair_rows = {frame: group.to_dict("records") for frame, group in pairs.groupby("frame_id")}
    frame_rows = {(r["clip_id"], r["original_frame_index"]): r for r in frames.to_dict("records")}
    frames_by_id = {row["frame_id"]: row for row in frame_rows.values()}
    person_rows = {
        frame: {int(r.person_id): [r.xmin, r.ymin, r.xmax, r.ymax] for r in group.itertuples()}
        for frame, group in people.groupby("frame_id")
    }
    args.output.mkdir(parents=True)
    report = {
        "stage": "P04-smoke" if args.max_frames else "P05",
        "complete": False,
        "oracle_values_used": False,
        "input_convention": "one zero placeholder; all real tracks",
        "missing_context": "zero tensors; no interpolation or cross-clip context",
        "geometry_policy": "P02 clipped geometry, then upstream square_bbox",
        "model_variant": "MTGS-DINO temporal, released Idiap/mtgs-vsgaze",
        "mtgs_commit": "a2ce45f44ed73d86e89e16bffb6be7a9567e3052",
        "dinov2_commit": "7764ea0f912e53c92e82eb78a2a1631e92725fc8",
        "model_settings": MODEL_SETTINGS,
        "checkpoint_sha256": CHECKPOINT_SHA256,
        "runtime": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0),
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "precision": "float16-autocast" if args.amp else "float32",
        "memory_fraction": args.memory_fraction,
        "public_preprocess_cache_frames": 0 if args.no_preprocess_cache else 64,
        "batch_benchmarks": [],
        "clips": [],
    }
    report["public_inputs_sha256"] = {
        name: sha256(args.processed / "public" / name)
        for name in ["frames.csv", "public_people.csv", "public_pairs.csv"]
    }
    report_path = args.output / "inference-provenance.json"
    if args.amp and not args.max_frames:
        if args.runtime_lock is None:
            raise ValueError("Full AMP runs require a passed development smoke --runtime-lock")
        runtime_lock = json.loads(args.runtime_lock.read_text())
        if (
            not runtime_lock["complete"]
            or runtime_lock["stage"] != "P04-smoke"
            or runtime_lock["checkpoint_sha256"] != CHECKPOINT_SHA256
            or runtime_lock["precision"] != "float16-autocast"
            or not runtime_lock.get("amp_development_check")
        ):
            raise ValueError("Invalid development runtime lock")
        report["runtime_lock_sha256"] = sha256(args.runtime_lock)
        report["amp_development_check"] = runtime_lock["amp_development_check"]

    def save():
        report_path.write_text(json.dumps(report, indent=2) + "\n")

    save()
    model, square_bbox = load_model(args.mtgs_root, args.dino_root, args.checkpoint)
    print("Strict frozen model load passed", flush=True)

    def forward(inputs):
        with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=args.amp):
            return model(inputs)

    processed, benchmarked = 0, False
    started = time.monotonic()
    with torch.inference_mode():
        for source in sources:
            archive_path = args.acquisition / source["archive"]
            if sha256(archive_path) != source["archive_sha256"]:
                raise ValueError("Source JPEG archive hash mismatch")
            with tarfile.open(archive_path) as archive:

                def image_loader(path):
                    member = archive.extractfile(path)
                    if member is None:
                        raise ValueError("Missing JPEG member")
                    image = Image.open(io.BytesIO(member.read()))
                    image.load()
                    return image

                @lru_cache(maxsize=64)
                def prepared_loader(frame_id):
                    return prepare_public_frame(
                        frames_by_id[frame_id], person_rows, image_loader, square_bbox
                    )

                subset = frames[frames.source_id == source["source_id"]]
                for clip_id, clip in subset.groupby("clip_id", sort=True):
                    rows = []
                    clip_start = time.monotonic()
                    for anchor in clip.sort_values("original_frame_index").to_dict("records"):
                        if anchor["frame_id"] not in pair_rows:
                            continue
                        inputs, pids = prepare_window(
                            anchor,
                            frame_rows,
                            person_rows,
                            image_loader,
                            square_bbox,
                            prepared_loader=None if args.no_preprocess_cache else prepared_loader,
                        )
                        if not report.get("auxiliary_pruning_verified"):
                            # A single-time input fits the cap and exercises the same native heads.
                            single = {
                                key: value[:, 2:3].contiguous()
                                if key != "num_valid_people"
                                else value[2:3]
                                for key, value in inputs.items()
                            }
                            full = model(single)
                            native_before = [full[index].detach().cpu().clone() for index in [4, 5]]
                            del full
                            prune_unused_heatmap(model)
                            torch.cuda.empty_cache()
                            trimmed = model(single)
                            differences = [
                                float((before - trimmed[index].cpu()).abs().max())
                                for before, index in zip(native_before, [4, 5], strict=True)
                            ]
                            if max(differences) > 1e-6:
                                raise ValueError(
                                    "Auxiliary pruning changed native social-gaze outputs"
                                )
                            report["auxiliary_pruning_verified"] = {
                                "full_vs_pruned_single_time_max_abs_difference": differences,
                                "auxiliary_heatmap_values_available": False,
                                "native_weights_or_computation_changed": False,
                            }
                            del trimmed, native_before, single
                            save()
                        if args.amp and not report.get("amp_development_check"):
                            reference = model(inputs)
                            reference = [
                                reference[index].float().sigmoid().cpu() for index in [4, 5]
                            ]
                            accelerated = forward(inputs)
                            differences = [
                                float(
                                    (before - accelerated[index].float().sigmoid().cpu())
                                    .abs()
                                    .max()
                                )
                                for before, index in zip(reference, [4, 5], strict=True)
                            ]
                            if max(differences) > 0.002:
                                raise ValueError(
                                    "AMP exceeds prespecified .002 probability tolerance"
                                )
                            report["amp_development_check"] = {
                                "max_abs_probability_difference_LAH_LAEO": differences,
                                "tolerance": 0.002,
                                "scope": "first public development window",
                            }
                            del reference, accelerated
                            save()
                        if args.benchmark_batches and not benchmarked:
                            for batch in [1, 2, 4]:
                                try:
                                    repeated = {
                                        key: value.repeat(batch, *([1] * (value.ndim - 1)))
                                        if key != "num_valid_people"
                                        else value.repeat(batch)
                                        for key, value in inputs.items()
                                    }
                                    torch.cuda.reset_peak_memory_stats()
                                    t0 = time.monotonic()
                                    output = forward(repeated)
                                    torch.cuda.synchronize()
                                    report["batch_benchmarks"].append(
                                        {
                                            "batch_size": batch,
                                            "status": "passed",
                                            "seconds": time.monotonic() - t0,
                                            "peak_allocated_bytes": (
                                                torch.cuda.max_memory_allocated()
                                            ),
                                        }
                                    )
                                    del output, repeated
                                except torch.cuda.OutOfMemoryError:
                                    report["batch_benchmarks"].append(
                                        {"batch_size": batch, "status": "out_of_memory"}
                                    )
                                    if "repeated" in locals():
                                        del repeated
                                    torch.cuda.empty_cache()
                            benchmarked = True
                            save()
                        output = forward(inputs)
                        lah = output[4][0, 2].float().sigmoid().cpu().numpy()
                        laeo = output[5][0, 2].float().sigmoid().cpu().numpy()
                        permutation = list(itertools.permutations(range(len(pids) + 1), 2))
                        slots = {pid: i for i, pid in enumerate(pids, start=1)}
                        for pair in pair_rows[anchor["frame_id"]]:
                            a, b = slots[pair["person_a"]], slots[pair["person_b"]]
                            # Released LAH pairs encode "second person looks at first".
                            ba_index, ab_index = (
                                permutation.index((a, b)),
                                permutation.index((b, a)),
                            )
                            ab, ba = float(lah[ab_index]), float(lah[ba_index])
                            q = min(ab, ba)
                            if not np.isfinite(q) or abs(q - float(laeo[ab_index])) > 1e-6:
                                raise ValueError("Native LAEO probability reconstruction failed")
                            rows.append(
                                {
                                    "record_id": pair["record_id"],
                                    "q": q,
                                    "direction_a_to_b": ab,
                                    "direction_b_to_a": ba,
                                }
                            )
                        processed += 1
                        del output, inputs
                        if processed % 25 == 0:
                            print(
                                f"{processed} frames; "
                                f"{processed / (time.monotonic() - started):.2f} fps",
                                flush=True,
                            )
                        if args.max_frames and processed >= args.max_frames:
                            break
                    target = args.output / f"predictions-{clip_id}.csv"
                    if rows:
                        with target.open("w", newline="", encoding="utf-8") as handle:
                            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                            writer.writeheader()
                            writer.writerows(rows)
                        report["clips"].append(
                            {
                                "clip_id": clip_id,
                                "source_id": source["source_id"],
                                "prediction_rows": len(rows),
                                "file": target.name,
                                "sha256": sha256(target),
                                "archive_sha256": source["archive_sha256"],
                                "seconds": time.monotonic() - clip_start,
                            }
                        )
                        save()
                    if args.max_frames and processed >= args.max_frames:
                        break
            if args.max_frames and processed >= args.max_frames:
                break
    report.update(
        {
            "complete": True,
            "processed_frames": processed,
            "elapsed_seconds": time.monotonic() - started,
            "frames_per_second": processed / max(time.monotonic() - started, 1e-9),
            "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(),
            "scope": "smoke only" if args.max_frames else "selected completed acquisition sources",
        }
    )
    save()
    print(
        json.dumps(
            {
                key: report[key]
                for key in [
                    "stage",
                    "processed_frames",
                    "frames_per_second",
                    "peak_gpu_allocated_bytes",
                ]
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
