"""Freeze an available-media subset only after the 95-source inventory and review gates."""

import argparse
import copy
import json
from pathlib import Path

import pandas as pd

from gaze_audit.frame_study import file_hash

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--inventory", type=Path, required=True)
parser.add_argument("--review-pools", type=Path, nargs="*", default=[])
parser.add_argument("--reviews", type=Path, nargs="*", default=[])
parser.add_argument("--exclusion-reviews", type=Path, nargs="*", default=[])
parser.add_argument("--processed", type=Path, default=Path("data/processed/vsgaze-17357752-v1"))
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
if args.output.exists():
    parser.error("Choose a new immutable population directory")
inventory = json.loads((args.inventory / "acquisition.json").read_text())
expected = set(pd.read_csv(args.processed / "sources.csv").source_id)
attempts = {r["source_id"]: r for r in inventory["sources"]}
if set(attempts) != expected or any(r["status"] == "started" for r in attempts.values()):
    raise ValueError("Attempt and record every original source before freezing the final subset")
approved_clips, review_hashes = set(), {}
manual_exclusions = {}
for path in args.exclusion_reviews:
    review = json.loads(path.read_text())
    if not review["geometry_visual_review"].startswith("failed"):
        raise ValueError("Source exclusions require a failed public-media review")
    for source in review["excluded_sources"]:
        if source not in expected:
            raise ValueError("Unknown source in exclusion review")
        manual_exclusions[source] = review["geometry_visual_review"]
    review_hashes[str(path)] = file_hash(path)
for path in args.reviews:
    review = json.loads(path.read_text())
    if not review["geometry_visual_review"].startswith("passed"):
        raise ValueError("Unapproved visual review supplied")
    if any(row["missing_frames"] for row in review["clip_checks"]):
        raise ValueError("Visual review includes missing frames")
    approved_clips.update(row["clip_id"] for row in review["clip_checks"])
    review_hashes[str(path)] = file_hash(path)
retained, acquisition_hashes = {}, {}
for root in [args.inventory, *args.review_pools]:
    path = root / "acquisition.json"
    report = json.loads(path.read_text())
    acquisition_hashes[str(path)] = file_hash(path)
    for original in report["sources"]:
        if original["status"] != "complete":
            continue
        row = copy.deepcopy(original)
        if row["source_id"] in manual_exclusions:
            continue
        if (row.get("alignment_review_required") or row["metadata_frame_count"] == 0) and not all(
            clip["clip_id"] in approved_clips for clip in row["clips"]
        ):
            raise ValueError(f"Additional alignment review missing for {row['source_id']}")
        archive = root / row["archive"]
        if file_hash(archive) != row["archive_sha256"]:
            raise ValueError("Source archive changed")
        row["archive"] = str(archive.resolve())
        if row["source_id"] in retained:
            raise ValueError("Duplicate completed source across acquisition pools")
        retained[row["source_id"]] = row
if not retained or not approved_clips:
    raise ValueError("Media and visual review evidence are required")
public = pd.read_csv(args.processed / "public/public_pairs.csv")
anchors = public[public.source_id.isin(retained) & public.eligible_anchor.eq(1)]
args.output.mkdir(parents=True)
anchor_path = args.output / "retained-anchors.csv"
anchors[["record_id", "frame_id", "split", "source_id", "clip_id"]].to_csv(anchor_path, index=False)
sources = pd.read_csv(args.processed / "sources.csv")
sources[sources.source_id.isin(retained)].to_csv(args.output / "retained-sources.csv", index=False)
manifest = {
    "stage": "P03",
    "media_alignment_complete": True,
    "population_status": "documented available-media subset",
    "original_sources_attempted": len(attempts),
    "retained_sources": len(retained),
    "retained_eligible_anchors_by_split": {
        str(k): int(v) for k, v in anchors.groupby("split").size().items()
    },
    "retained_anchor_file_sha256": file_hash(anchor_path),
    "acquisition_report_hashes": acquisition_hashes,
    "visual_review_hashes": review_hashes,
    "excluded_sources": [
        {
            "source_id": key,
            "reason": manual_exclusions.get(key, attempts[key].get("error", "not verified")),
        }
        for key in sorted(expected - set(retained))
    ],
    "alignment_limitations": (
        "Official decoder mapping, cadence and visual geometry checks; "
        "original JPEG byte equivalence unavailable"
    ),
    "oracle_values_used": False,
}
(args.output / "population-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
(args.output / "acquisition.json").write_text(
    json.dumps(
        {
            "sources": [retained[key] for key in sorted(retained)],
            "complete": True,
            "scope": "frozen verified subset; original videos with failed checks stay excluded",
        },
        indent=2,
    )
    + "\n"
)
print(
    json.dumps(
        {key: manifest[key] for key in ["retained_sources", "retained_eligible_anchors_by_split"]},
        indent=2,
    )
)
