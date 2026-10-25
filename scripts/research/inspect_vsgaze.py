"""Inspect the pinned public release without extracting files or general unpickling.

Run after `uv sync --frozen --extra research`:
  uv run python scripts/research/inspect_vsgaze.py --archive data/research/VSGaze.tar.gz
"""

import argparse
import hashlib
import io
import json
import pickle
import re
import tarfile
from collections import Counter, defaultdict
from pathlib import Path

import h5py
import numpy as np

RELEASE_MD5 = "c83980c07b349df3af84981721045d3b"
RELEASE_URL = "https://zenodo.org/records/17357752"


class ArrayOnlyUnpickler(pickle.Unpickler):
    """The release stores pandas object columns as NumPy array pickles."""

    def find_class(self, module, name):
        permitted = {
            ("numpy", "ndarray"): np.ndarray,
            ("numpy", "dtype"): np.dtype,
            ("numpy.core.multiarray", "_reconstruct"): np._core.multiarray._reconstruct,
            ("numpy._core.multiarray", "_reconstruct"): np._core.multiarray._reconstruct,
            ("numpy.core.multiarray", "scalar"): np._core.multiarray.scalar,
            ("numpy._core.multiarray", "scalar"): np._core.multiarray.scalar,
            ("numpy.core.numeric", "_frombuffer"): np._core.numeric._frombuffer,
            ("numpy._core.numeric", "_frombuffer"): np._core.numeric._frombuffer,
        }
        if (module, name) not in permitted:
            raise pickle.UnpicklingError(f"Unsupported object: {module}.{name}")
        return permitted[(module, name)]


def read_table(archive, member):
    with h5py.File(io.BytesIO(archive.extractfile(member).read()), "r") as h5:
        group = h5["data"]
        columns = [x.decode() for x in group["block0_items"][:]]
        values = ArrayOnlyUnpickler(io.BytesIO(group["block0_values"][0].tobytes())).load()
        if values.shape[1] != len(columns):
            raise ValueError("Unexpected release table layout")
        return columns, values


def inspect(archive_path):
    content = archive_path.read_bytes()
    if hashlib.md5(content).hexdigest() != RELEASE_MD5:
        raise ValueError("Release checksum differs from the pinned public archive")
    report = {
        "release_url": RELEASE_URL,
        "release_md5": RELEASE_MD5,
        "archive_sha256": hashlib.sha256(content).hexdigest(),
        "annotation_only": True,
        "predictions_or_media_inspected": False,
        "splits": {},
    }
    with tarfile.open(fileobj=io.BytesIO(content), mode="r:gz") as archive:
        for split in ["train", "val", "test"]:
            columns, values = read_table(archive, f"VSGaze/childplay_{split}.h5")
            if split == "train":
                print("Columns:", columns)
                print("First path:", values[0, columns.index("path")])
            counts = Counter()
            clips = set()
            sources = set()
            positive_by_source = Counter()
            sequences = defaultdict(list)
            for row in values:
                record = dict(zip(columns, row, strict=True))
                path = str(record["path"])
                clip = Path(path).parent.name
                clips.add(clip)
                source, bounds = clip.rsplit("_", 1)
                if not re.fullmatch(r"\d+-\d+(-downsampled)?", bounds):
                    raise ValueError("Unexpected clip/source naming convention")
                sources.add(source)
                frame = int(Path(path).stem.rsplit("_", 1)[1])
                canonical = {}
                for pair, label in zip(record["pairs"], record["laeo_pairs"], strict=True):
                    a, b = (int(x) for x in pair)
                    if a < 0 or b < 0:
                        counts["placeholder_or_negative_id"] += 1
                        continue
                    if a == b:
                        counts["self_pairs"] += 1
                        continue
                    key = tuple(sorted((a, b)))
                    label = int(label)
                    if label not in {-1, 0, 1}:
                        raise ValueError("Unexpected reference value")
                    if key in canonical:
                        counts["reverse_or_duplicate_rows"] += 1
                        if canonical[key] != label:
                            raise ValueError("Conflicting pair orientations")
                    canonical[key] = label
                for (a, b), label in canonical.items():
                    counts[{1: "positive", 0: "negative", -1: "unknown"}[label]] += 1
                    if label == 1:
                        positive_by_source[source] += 1
                    if label != -1:
                        sequences[(clip, a, b)].append((frame, label))
            eligible_count = counts["positive"] + counts["negative"]
            report["splits"][split] = {
                "frames": len(values),
                "clip_paths": len(clips),
                **dict(counts),
                "source_video_ids": sorted(sources),
                "source_videos": len(sources),
                "sources_with_positive_labels": len(positive_by_source),
                "largest_source_share_of_positive_labels": (
                    max(positive_by_source.values()) / counts["positive"]
                ),
                "eligible_binary_pairs": eligible_count,
                "prevalence": counts["positive"] / eligible_count,
            }
            structures = {}
            p = counts["positive"] / eligible_count
            frame_variance = p * (1 - p) * eligible_count / (eligible_count - 1)
            for length in [1, 2, 5, 10]:
                query_units = []
                for sequence in sequences.values():
                    chunk = []
                    previous = None
                    for frame, label in sorted(sequence):
                        if chunk and (frame != previous + 1 or len(chunk) == length):
                            query_units.append(chunk)
                            chunk = []
                        chunk.append(label)
                        previous = frame
                    if chunk:
                        query_units.append(chunk)
                cost = np.array([len(b) for b in query_units])
                positives = np.array([sum(b) for b in query_units])
                # Constant q=p is a label-informed diagnostic, not an available predictor.
                residual = positives - p * cost
                structures[length] = {
                    "units": len(query_units),
                    "mean_cost": float(cost.mean()),
                    "positive_containing_units": int((positives > 0).sum()),
                    "constant_score_block_variance_ratio": float(
                        np.var(residual, ddof=1) / (cost.mean() * frame_variance)
                    ),
                }
            report["splits"][split]["label_only_block_diagnostic"] = structures
            print(
                split, {k: v for k, v in report["splits"][split].items() if k != "source_video_ids"}
            )
    source_sets = {s: set(v["source_video_ids"]) for s, v in report["splits"].items()}
    report["source_overlap_counts"] = {
        f"{a}/{b}": len(source_sets[a] & source_sets[b])
        for a, b in [("train", "val"), ("train", "test"), ("val", "test")]
    }
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/research/vsgaze-inventory.json")
    )
    args = parser.parse_args()
    result = inspect(args.archive)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
