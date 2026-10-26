"""Independently check P02 files, identity joins, source isolation and public columns."""

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--processed", type=Path, default=Path("data/processed/vsgaze-17357752-v1"))
parser.add_argument("--report", type=Path, required=True)
args = parser.parse_args()
root = args.processed
manifest = json.loads((root / "manifest.json").read_text())
assert manifest["completed"] is True
for name, entry in manifest["files"].items():
    path = root / name.replace("\\", "/")
    assert path.stat().st_size == entry["bytes"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]
frames = pd.read_csv(root / "public/frames.csv")
people = pd.read_csv(root / "public/public_people.csv")
pairs = pd.read_csv(root / "public/public_pairs.csv")
labels = pd.read_csv(root / "oracle/oracle_labels.csv")
sources = pd.read_csv(root / "sources.csv")
folds = pd.read_csv(root / "development_folds.csv")
assert frames.frame_id.is_unique and pairs.record_id.is_unique and labels.record_id.is_unique
assert not people.duplicated(["frame_id", "person_id"]).any()
assert set(people.frame_id) <= set(frames.frame_id)
assert set(pairs.frame_id) <= set(frames.frame_id)
assert set(labels.record_id) == set(pairs.loc[pairs.eligible_anchor == 1, "record_id"])
assert labels.label.isin([0, 1]).all()
assert (pairs.person_a < pairs.person_b).all()
for person in ["person_a", "person_b"]:
    joined = pairs.merge(
        people[["frame_id", "person_id"]],
        left_on=["frame_id", person],
        right_on=["frame_id", "person_id"],
        how="left",
        validate="many_to_one",
    )
    assert not joined.person_id.isna().any()
assert frames.groupby("source_id").split.nunique().max() == 1
assert set(folds.source_id) == set(sources.loc[sources.split == "train", "source_id"])
assert folds.source_id.is_unique and set(folds.fold) == set(range(5))
for table in [frames, people, pairs]:
    assert not set(table.columns) & {
        "label",
        "gaze_points",
        "inout",
        "lah_pairs",
        "laeo_pairs",
        "coatt_pairs",
        "gaze_class",
        "gaze_x",
        "gaze_y",
    }
report = {
    "stage": "P02",
    "independent_validation": "passed",
    "checks": [
        "all CSV byte sizes and SHA256",
        "unique stable IDs",
        "person/frame joins",
        "exact binary oracle/eligible ID equality",
        "canonical unordered pairs",
        "source-disjoint splits",
        "five source-group training folds",
        "no reference values in public inference columns",
    ],
    "splits": manifest["splits"],
    "population_status": manifest["population_status"],
    "training_fold_source_counts": {str(k): int(v) for k, v in folds.fold.value_counts().items()},
    "normalized_manifest_sha256": hashlib.sha256((root / "manifest.json").read_bytes()).hexdigest(),
    "geometry_policy": manifest["geometry_policy"],
    "public_index_caution": (
        "original_frame_index is the annotation filename index; use P03 mapping"
    ),
}
args.report.parent.mkdir(parents=True, exist_ok=True)
args.report.write_text(json.dumps(report, indent=2) + "\n")
print(
    json.dumps(
        {
            "status": "passed",
            "report": str(args.report),
            "frames": len(frames),
            "eligible_anchors": len(labels),
        },
        indent=2,
    )
)
