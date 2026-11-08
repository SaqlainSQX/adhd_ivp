"""Registered K4: export eligibility and private references without prevalence readout."""

import csv
import hashlib
import json
import tarfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

import numpy as np

from gaze_audit.adapters.vsgaze import read_release_table, stable_id

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/uco-eligibility-k4-v2"
DEST = ROOT / "data/processed/uco-eligible-k4-v2"


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def write_csv(path, rows, columns):
    with path.open("x", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def prepare():
    public_path = ROOT / "data/processed/uco-public-k2-v1/public-frames.json"
    assert digest(public_path) == "7d5aba5fc7ef73b83dfe31f99a3094525c75645ef3ccaf9e12c3e37d1418281e"
    public = json.loads(public_path.read_text())
    clips = set(
        json.loads((ROOT / "docs/research/j-uco-contract.json").read_text())["official_splits"][
            "testVids"
        ]
    )
    ambiguous, annotation_hashes, indices = {}, {}, {}
    with tarfile.open(ROOT / "data/raw/uco/acquisition-k-v1/ucolaeodb_v1.1.tgz", "r|gz") as ar:
        for member in ar:
            parts = PurePosixPath(member.name).parts
            if (
                len(parts) != 4
                or parts[:3] != ("ucolaeodb", "annotations", "annotations_frame")
                or PurePosixPath(parts[3]).stem not in clips
            ):
                continue
            assert member.isfile() and member.size < 65536
            clip = PurePosixPath(parts[3]).stem
            content = ar.extractfile(member).read()
            annotation_hashes[clip] = hashlib.sha256(content).hexdigest()
            frame_ids = []
            for line in content.decode().splitlines():
                if not line.strip():
                    continue
                fields = line.split()
                assert len(fields) == 2, "Unexpected original frame-code schema"
                frame, code = map(int, fields)
                assert frame >= 0 and code in (0, 1, 2, 9), "Unexpected frame/code encoding"
                key = (clip, frame - 1)
                assert key not in ambiguous, "Duplicate original frame code"
                ambiguous[key] = code == 9
                frame_ids.append(frame)
            assert frame_ids == list(range(1, len(frame_ids) + 1)), (
                "Nonconsecutive original ordinals"
            )
            indices[clip] = {
                "rows": len(frame_ids),
                "min": min(frame_ids),
                "max": max(frame_ids),
                "consecutive": frame_ids == list(range(min(frame_ids), max(frame_ids) + 1)),
            }
    assert set(annotation_hashes) == clips
    (DEST / "ambiguity-mask.json").write_text(
        json.dumps(
            [{"clip": c, "frame": f, "ambiguous": b} for (c, f), b in sorted(ambiguous.items())]
        )
        + "\n"
    )
    release = ROOT / "data/research/VSGaze.tar.gz"
    assert digest(release) == "3bf42763c968b9684a3276e32b41403a43392282c67bdc8e461058ca949cb386"
    with tarfile.open(release) as ar:
        columns, values = read_release_table(ar, "VSGaze/uco_laeo_test.h5")
    col = {
        k: columns.index(k) for k in ("path", "person_ids", "head_bboxes", "pairs", "laeo_pairs")
    }
    expected = {(r["clip"], r["frame"]) for r in public}
    seen, eligible, oracle = set(), [], []
    counts, per_clip = Counter(), defaultdict(Counter)
    for value in values:
        path = PurePosixPath(str(value[col["path"]]).replace("\\", "/"))
        clip, frame = path.parent.name.lower(), int(path.stem)
        key = (clip, frame)
        assert key in expected and key not in seen, "Unexpected/duplicate unified frame"
        seen.add(key)
        assert key in ambiguous, "Original frame index missing; mapping gate failed"
        pids, boxes = value[col["person_ids"]], value[col["head_bboxes"]]
        valid = set()
        for pid, box in zip(pids, boxes, strict=True):
            assert np.isfinite(pid) and float(pid).is_integer(), "Invalid person ID"
            if pid >= 0 and np.any(box):
                assert np.isfinite(box).all() and np.all(box[2:] > box[:2])
                valid.add(int(pid))
        canonical = {}
        for pair, label in zip(value[col["pairs"]], value[col["laeo_pairs"]], strict=True):
            assert len(pair) == 2 and all(np.isfinite(p) and float(p).is_integer() for p in pair)
            assert np.isfinite(label) and label in (-1, 0, 1), "Unexpected unified encoding"
            a, b = map(int, pair)
            if a not in valid or b not in valid:
                counts["placeholder_or_invalid_pair_rows"] += 1
                continue
            if a == b:
                counts["self_pair_rows"] += 1
                continue
            pair_key = tuple(sorted((a, b)))
            if pair_key in canonical:
                counts["duplicate_direction_rows"] += 1
                assert canonical[pair_key] == label, "Conflicting duplicate pair labels"
            canonical[pair_key] = int(label)
        if ambiguous[key]:
            counts["original_ambiguous_unified_frames"] += 1
            counts["ambiguous_frames_with_unified_binary_pair"] += int(
                any(v != -1 for v in canonical.values())
            )
        for (a, b), label in sorted(canonical.items()):
            if label == -1:
                counts["unknown_canonical_pairs"] += 1
                continue
            if ambiguous[key]:
                counts["binary_pairs_excluded_by_original_ambiguity"] += 1
                continue
            record = stable_id("uco-pair", clip, frame, a, b)
            eligible.append(
                {"record_id": record, "clip": clip, "frame": frame, "person_a": a, "person_b": b}
            )
            oracle.append({"record_id": record, "label": label})
            per_clip[clip]["eligible_pairs"] += 1
    assert seen == expected and len(eligible) == len({r["record_id"] for r in eligible})
    write_csv(
        DEST / "eligible-pairs.csv",
        eligible,
        ["record_id", "clip", "frame", "person_a", "person_b"],
    )
    write_csv(DEST / "oracle.csv", oracle, ["record_id", "label"])
    n = len(eligible)
    result = {
        "stage": "K4b-eligibility-only-original-ordinal-minus-one",
        "complete": True,
        "unified_frames": len(seen),
        "eligible_pairs": n,
        "candidate_budgets": [int(n * f) for f in (0.05, 0.1, 0.2, 0.4)],
        "exclusion_and_duplicate_counts": dict(counts),
        "eligible_pairs_by_clip": {c: dict(v) for c, v in sorted(per_clip.items())},
        "original_frame_index_schema": indices,
        "original_annotation_sha256": annotation_hashes,
        "output_sha256": {p.name: digest(p) for p in sorted(DEST.iterdir()) if p.is_file()},
        "prevalence_or_positive_counts_computed": False,
        "scores_or_performance_computed": False,
        "geometry_changed": False,
    }
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=False)
    DEST.mkdir(parents=True, exist_ok=False)
    try:
        prepare()
    except Exception as error:
        (OUT / "failure.json").write_text(
            json.dumps({"type": type(error).__name__, "message": str(error)}, indent=2) + "\n"
        )
        raise
