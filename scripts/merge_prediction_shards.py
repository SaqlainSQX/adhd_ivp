"""Verify model/source provenance and exact public-population coverage before merging q."""

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from gaze_audit.frame_study import file_hash

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--population", type=Path, required=True)
parser.add_argument("--processed", type=Path, default=Path("data/processed/vsgaze-17357752-v1"))
parser.add_argument("--shards", type=Path, nargs="+", required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
if args.output.exists():
    parser.error("Choose a new cache directory")
population = json.loads((args.population / "population-manifest.json").read_text())
if (args.population / "WITHDRAWN.json").exists():
    raise ValueError("This staging population was withdrawn; use its recorded replacement")
if not population["media_alignment_complete"]:
    raise ValueError("Final media alignment gate has not passed")
media = json.loads((args.population / "acquisition.json").read_text())
source_hashes = {r["source_id"]: r["archive_sha256"] for r in media["sources"]}
public = pd.read_csv(args.processed / "public/public_pairs.csv")
expected = public[public.source_id.isin(source_hashes) & public.geometry_valid.eq(1)]
parts, contracts, shard_hashes, excluded_cache_clips = [], [], {}, []
for shard in args.shards:
    report_path = shard / "inference-provenance.json"
    report = json.loads(report_path.read_text())
    if not report["complete"] or report["stage"] != "P05":
        raise ValueError("Only completed full source shards can enter the final cache")
    contracts.append(
        {
            key: report[key]
            for key in [
                "checkpoint_sha256",
                "mtgs_commit",
                "dinov2_commit",
                "model_settings",
                "precision",
                "input_convention",
                "missing_context",
                "geometry_policy",
                "public_inputs_sha256",
            ]
        }
    )
    shard_hashes[str(shard)] = file_hash(report_path)
    for clip in report["clips"]:
        if clip["source_id"] not in source_hashes:
            excluded_cache_clips.append(
                {
                    "source_id": clip["source_id"],
                    "clip_id": clip["clip_id"],
                    "reason": "source excluded by frozen media population",
                }
            )
            continue
        if source_hashes.get(clip["source_id"]) != clip["archive_sha256"]:
            raise ValueError("Prediction/media source hash mismatch")
        path = shard / clip["file"]
        if file_hash(path) != clip["sha256"]:
            raise ValueError("Prediction shard changed")
        parts.append(pd.read_csv(path))
if any(contract != contracts[0] for contract in contracts[1:]):
    raise ValueError("Cannot mix prediction/runtime/input conventions")
for name, sha in contracts[0]["public_inputs_sha256"].items():
    if file_hash(args.processed / "public" / name) != sha:
        raise ValueError("Public population input changed")
merged = pd.concat(parts, ignore_index=True)
if merged.record_id.duplicated().any() or set(merged.record_id) != set(expected.record_id):
    raise ValueError(
        "Caches must cover exactly the final public pair population, without duplicates"
    )
merged = merged.set_index("record_id").loc[expected.record_id].reset_index()
args.output.mkdir(parents=True)
path = args.output / "predictions.csv"
merged.to_csv(path, index=False)
manifest = {
    "stage": "P05",
    "complete": True,
    "model_contract": contracts[0],
    "prediction_rows": len(merged),
    "eligible_anchors": int(expected.eligible_anchor.sum()),
    "source_count": len(source_hashes),
    "prediction_sha256": file_hash(path),
    "population_manifest_sha256": file_hash(args.population / "population-manifest.json"),
    "public_pair_id_hash": hashlib.sha256("\n".join(expected.record_id).encode()).hexdigest(),
    "shard_manifest_hashes": shard_hashes,
    "excluded_cache_clips": excluded_cache_clips,
    "oracle_values_used": False,
}
(args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps(manifest, indent=2))
