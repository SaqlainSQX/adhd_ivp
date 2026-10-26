"""Normalize the pinned VSGaze release into auditable public and oracle tables."""

import csv
import hashlib
import io
import json
import pickle
import re
import tarfile
from collections import Counter
from contextlib import ExitStack
from pathlib import Path, PurePosixPath

import numpy as np
from sklearn.model_selection import GroupKFold

RELEASE_SHA256 = "3bf42763c968b9684a3276e32b41403a43392282c67bdc8e461058ca949cb386"
EXPECTED = {
    "train": (100209, 285585, 6396, 279189, 129441, 68),
    "validation": (10283, 33568, 259, 33309, 11741, 6),
    "test": (9986, 38847, 651, 38196, 41572, 21),
}


class _ArrayOnlyUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        allowed = {("numpy", "ndarray"): np.ndarray, ("numpy", "dtype"): np.dtype}
        for prefix in ["numpy.core", "numpy._core"]:
            allowed[(f"{prefix}.multiarray", "_reconstruct")] = np._core.multiarray._reconstruct
            allowed[(f"{prefix}.multiarray", "scalar")] = np._core.multiarray.scalar
            allowed[(f"{prefix}.numeric", "_frombuffer")] = np._core.numeric._frombuffer
        if (module, name) not in allowed:
            raise pickle.UnpicklingError(f"Unsupported release object: {module}.{name}")
        return allowed[(module, name)]


def read_release_table(archive, member):
    import h5py

    content = archive.extractfile(member)
    if content is None:
        raise ValueError(f"Missing release member: {member}")
    with h5py.File(io.BytesIO(content.read()), "r") as h5:
        group = h5["data"]
        columns = [x.decode() for x in group["block0_items"][:]]
        values = _ArrayOnlyUnpickler(io.BytesIO(group["block0_values"][0].tobytes())).load()
        if values.ndim != 2 or values.shape[1] != len(columns):
            raise ValueError("Unexpected release table shape")
        return columns, values


def stable_id(kind: str, *parts) -> str:
    encoded = json.dumps([kind, *parts], separators=(",", ":"), ensure_ascii=True).encode()
    return f"{kind}-{hashlib.sha256(encoded).hexdigest()[:24]}"


def parse_path(value: str) -> dict:
    path = PurePosixPath(value.replace("\\", "/"))
    clip_id = path.parent.name
    match = re.fullmatch(r"(.+)_(\d+)-(\d+)(-downsampled)?", clip_id)
    if not match:
        raise ValueError(f"Unsupported ChildPlay clip path: {value}")
    source, start, end, downsampled = match.groups()
    frame_match = re.fullmatch(re.escape(source) + r"_(\d+)", path.stem)
    if not frame_match:
        raise ValueError(f"Unsupported ChildPlay frame path: {value}")
    return {
        "source_id": source,
        "clip_id": clip_id,
        "source_start_index": int(start),
        "source_end_index": int(end),
        "downsampled": bool(downsampled),
        "original_frame_index": int(frame_match.group(1)),
        "annotation_path": str(path),
    }


def normalize_entry(record: dict, split: str) -> dict:
    """Pure conversion. Reference values are returned separately from public tables."""
    location = parse_path(str(record["path"]))
    frame_id = stable_id("frame", location["clip_id"], location["original_frame_index"])
    frame = {"frame_id": frame_id, "split": split, **location}
    boxes = np.asarray(record["head_bboxes"], dtype=float)
    ids = np.asarray(record["person_ids"])
    if boxes.shape != (len(ids), 4):
        raise ValueError("Head-box/person-ID shape mismatch")
    people, geometry = [], {}
    issues = Counter()
    for raw_id, raw_box in zip(ids, boxes, strict=True):
        if not np.isfinite(raw_id) or float(raw_id) % 1:
            raise ValueError("Person IDs must be finite integers")
        person = int(raw_id)
        if person < 0:
            continue
        if person in geometry:
            raise ValueError("Duplicate real person ID in one frame")
        clipped = np.clip(raw_box, 0, 1)
        valid = bool(
            np.isfinite(raw_box).all() and clipped[0] < clipped[2] and clipped[1] < clipped[3]
        )
        changed = bool(valid and not np.array_equal(raw_box, clipped))
        geometry[person] = valid
        if not valid:
            issues["invalid_geometry_person"] += 1
        elif changed:
            issues["clipped_geometry_person"] += 1
        people.append(
            {
                "frame_id": frame_id,
                "person_id": person,
                "geometry_valid": int(valid),
                "bbox_clipped": int(changed),
                **dict(zip(["xmin", "ymin", "xmax", "ymax"], clipped.tolist(), strict=True)),
            }
        )
    canonical = {}
    for pair, raw_label in zip(record["pairs"], record["laeo_pairs"], strict=True):
        if len(pair) != 2 or any(not np.isfinite(x) or float(x) % 1 for x in pair):
            raise ValueError("Malformed pair IDs")
        a, b = (int(x) for x in pair)
        if a < 0 or b < 0:
            issues["placeholder_pair_rows"] += 1
            continue
        if a == b:
            issues["self_pair_rows"] += 1
            continue
        if not np.isfinite(raw_label) or float(raw_label) % 1 or raw_label not in [-1, 0, 1]:
            raise ValueError("Unknown LAEO reference encoding")
        pair_id = tuple(sorted((a, b)))
        label = int(raw_label)
        if pair_id in canonical:
            issues["reverse_or_duplicate_pair_rows"] += 1
            if canonical[pair_id] != label:
                raise ValueError("Conflicting reverse-orientation references")
        canonical[pair_id] = label
    public_pairs, oracle, exclusions = [], [], []
    counts = Counter()
    for (a, b), label in sorted(canonical.items()):
        counts[{1: "positive", 0: "negative", -1: "unknown"}[label]] += 1
        record_id = stable_id("pair", location["clip_id"], location["original_frame_index"], a, b)
        valid = geometry.get(a, False) and geometry.get(b, False)
        eligible = label != -1 and valid
        public_pairs.append(
            {
                "record_id": record_id,
                "frame_id": frame_id,
                "split": split,
                "source_id": location["source_id"],
                "clip_id": location["clip_id"],
                "original_frame_index": location["original_frame_index"],
                "person_a": a,
                "person_b": b,
                "reference_available": int(label != -1),
                "geometry_valid": int(valid),
                "eligible_anchor": int(eligible),
            }
        )
        if eligible:
            oracle.append({"record_id": record_id, "label": label})
            counts["eligible_anchors"] += 1
        reason = (
            "unknown_reference" if label == -1 else "invalid_pair_geometry" if not valid else None
        )
        if reason:
            exclusions.append(
                {"frame_id": frame_id, "record_id": record_id, "reason": reason, "count": 1}
            )
    exclusions.extend(
        {"frame_id": frame_id, "record_id": "", "reason": reason, "count": n}
        for reason, n in sorted(issues.items())
    )
    return {
        "frame": frame,
        "people": people,
        "pairs": public_pairs,
        "oracle": oracle,
        "exclusions": exclusions,
        "counts": counts,
        "issues": issues,
    }


def prepare_archive(archive_path: Path, output: Path) -> dict:
    archive_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    if archive_hash != RELEASE_SHA256:
        raise ValueError("Archive is not the checksum-pinned VSGaze release")
    if output.exists():
        raise ValueError("Output already exists; select a new data version")
    output.mkdir(parents=True)
    summary = {
        "stage": "P02",
        "archive_sha256": archive_hash,
        "population_status": "pre-media-normalization",
        "splits": {},
        "completed": False,
    }
    (output / "manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    sources, clips, train_groups = {}, {}, []
    seen_frames = set()
    schemas = {
        "frames": [
            "frame_id",
            "split",
            "source_id",
            "clip_id",
            "source_start_index",
            "source_end_index",
            "downsampled",
            "original_frame_index",
            "annotation_path",
        ],
        "public_people": [
            "frame_id",
            "person_id",
            "geometry_valid",
            "bbox_clipped",
            "xmin",
            "ymin",
            "xmax",
            "ymax",
        ],
        "public_pairs": [
            "record_id",
            "frame_id",
            "split",
            "source_id",
            "clip_id",
            "original_frame_index",
            "person_a",
            "person_b",
            "reference_available",
            "geometry_valid",
            "eligible_anchor",
        ],
        "oracle_labels": ["record_id", "label"],
        "exclusions": ["frame_id", "record_id", "reason", "count"],
    }
    with ExitStack() as stack:
        writers = {}
        for name, fields in schemas.items():
            folder = output / ("oracle" if name == "oracle_labels" else "public")
            folder.mkdir(exist_ok=True)
            handle = stack.enter_context(
                (folder / f"{name}.csv").open("w", newline="", encoding="utf-8")
            )
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writers[name] = writer
        archive = stack.enter_context(tarfile.open(archive_path, "r:gz"))
        for split, member_split in [("train", "train"), ("validation", "val"), ("test", "test")]:
            columns, values = read_release_table(archive, f"VSGaze/childplay_{member_split}.h5")
            stats, issues = Counter(), Counter()
            split_sources = set()
            for row in values:
                normalized = normalize_entry(dict(zip(columns, row, strict=True)), split)
                frame = normalized["frame"]
                if frame["frame_id"] in seen_frames:
                    raise ValueError("Duplicate frame path or cross-split frame leakage")
                seen_frames.add(frame["frame_id"])
                source, clip = frame["source_id"], frame["clip_id"]
                if source in sources and sources[source]["split"] != split:
                    raise ValueError("Original source crosses dataset splits")
                sources.setdefault(
                    source, {"split": split, "clips": set(), "frames": 0, "eligible_anchors": 0}
                )
                sources[source]["clips"].add(clip)
                sources[source]["frames"] += 1
                sources[source]["eligible_anchors"] += len(normalized["oracle"])
                split_sources.add(source)
                clips.setdefault(
                    clip,
                    {
                        k: frame[k]
                        for k in [
                            "source_id",
                            "split",
                            "source_start_index",
                            "source_end_index",
                            "downsampled",
                        ]
                    },
                )
                writers["frames"].writerow(frame)
                for key, name in [
                    ("people", "public_people"),
                    ("pairs", "public_pairs"),
                    ("oracle", "oracle_labels"),
                    ("exclusions", "exclusions"),
                ]:
                    writers[name].writerows(normalized[key])
                stats.update(normalized["counts"])
                issues.update(normalized["issues"])
                if split == "train":
                    train_groups.extend([source] * len(normalized["oracle"]))
            expected = EXPECTED[split]
            observed = (
                len(values),
                stats["positive"] + stats["negative"],
                stats["positive"],
                stats["negative"],
                stats["unknown"],
                len(split_sources),
            )
            if observed != expected:
                raise ValueError(f"Release inventory mismatch in {split}: {observed}")
            summary["splits"][split] = {
                "frames": len(values),
                "source_videos": len(split_sources),
                **dict(stats),
                "issues": dict(issues),
            }
            print(
                f"{split}: {len(values)} frames, "
                f"{stats['eligible_anchors']} geometry-valid binary anchors",
                flush=True,
            )

    def write_small(name, fields, rows):
        with (output / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    write_small(
        "sources.csv",
        ["source_id", "split", "clip_count", "frame_count", "eligible_anchors"],
        [
            {
                "source_id": s,
                "split": v["split"],
                "clip_count": len(v["clips"]),
                "frame_count": v["frames"],
                "eligible_anchors": v["eligible_anchors"],
            }
            for s, v in sorted(sources.items())
        ],
    )
    write_small(
        "clips.csv",
        ["clip_id", "source_id", "split", "source_start_index", "source_end_index", "downsampled"],
        [{"clip_id": k, **v} for k, v in sorted(clips.items())],
    )
    groups = np.asarray(train_groups)
    folds = {}
    for fold, (_, held) in enumerate(
        GroupKFold(n_splits=5).split(np.zeros(len(groups)), groups=groups)
    ):
        for source in np.unique(groups[held]):
            folds[str(source)] = fold
    write_small(
        "development_folds.csv",
        ["source_id", "fold"],
        [{"source_id": s, "fold": f} for s, f in sorted(folds.items())],
    )
    summary.update(
        {
            "completed": True,
            "original_source_overlap": 0,
            "training_folds": 5,
            "reference_values_in_public_tables": False,
            "geometry_policy": "clip boxes to image bounds, exclude nonfinite/zero-area boxes",
            "files": {
                str(p.relative_to(output)): {
                    "bytes": p.stat().st_size,
                    "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                }
                for p in sorted(output.rglob("*.csv"))
            },
        }
    )
    (output / "manifest.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary
