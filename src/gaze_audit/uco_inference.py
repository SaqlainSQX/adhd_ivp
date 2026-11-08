"""Public-only UCO input mapping and directional score decoding."""

import csv
import itertools
import json
from pathlib import Path

import numpy as np


def load_public(root):
    root = Path(root)
    rows = json.loads((root / "data/processed/uco-public-k2-v1/public-frames.json").read_text())
    frames, people = {}, {}
    for row in rows:
        clip, frame = row["clip"], row["frame"]
        key = (clip, frame)
        if key in frames:
            raise ValueError("Duplicate public frame")
        fid = f"{clip}:{frame}"
        frames[key] = {
            "frame_id": fid,
            "clip_id": clip,
            "original_frame_index": frame,
            "annotation_path": f"{clip}/{frame:06d}.jpg",
        }
        people[fid] = {}
        for pid, box in zip(row["person_ids"], row["head_bboxes"], strict=True):
            if not np.isfinite(pid) or float(pid) % 1:
                raise ValueError("Nonintegral public person ID")
            if int(pid) < 0 or not any(box):
                continue
            box = np.asarray(box, float)
            if int(pid) in people[fid] or not np.isfinite(box).all() or np.any(box[2:] <= box[:2]):
                raise ValueError("Invalid or duplicate public person geometry")
            people[fid][int(pid)] = box.tolist()
    pairs, seen = {}, set()
    with (root / "data/processed/uco-eligible-k4-v2/eligible-pairs.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            key = row["clip"], int(row["frame"])
            fid = frames[key]["frame_id"]
            a, b = int(row["person_a"]), int(row["person_b"])
            if a == b or a not in people[fid] or b not in people[fid] or row["record_id"] in seen:
                raise ValueError("Public pair membership or uniqueness failed")
            seen.add(row["record_id"])
            pairs.setdefault(fid, []).append(
                {"record_id": row["record_id"], "person_a": a, "person_b": b}
            )
    return frames, people, pairs


def decode_scores(lah, pids, pairs, laeo=None):
    lah = np.asarray(lah, float).reshape(-1)
    slots = {pid: i for i, pid in enumerate(pids, 1)}
    order = list(itertools.permutations(range(len(pids) + 1), 2))
    if len(slots) != len(pids) or len(lah) != len(order):
        raise ValueError("Native output/track-slot shape mismatch")
    if not np.isfinite(lah).all() or np.any((lah < 0) | (lah > 1)):
        raise ValueError("Invalid native probability")
    indices = {pair: i for i, pair in enumerate(order)}
    out = []
    for pair in pairs:
        a, b = slots[pair["person_a"]], slots[pair["person_b"]]
        # Released LAH: second slot looks at first slot.
        ab, ba = float(lah[indices[b, a]]), float(lah[indices[a, b]])
        q = min(ab, ba)
        if laeo is not None and abs(q - float(laeo[indices[b, a]])) > 1e-6:
            raise ValueError("Directional native LAEO reconstruction failed")
        out.append(
            {"record_id": pair["record_id"], "q": q, "direction_a_to_b": ab, "direction_b_to_a": ba}
        )
    return out
