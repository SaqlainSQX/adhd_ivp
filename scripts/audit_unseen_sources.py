"""Audit source membership and media provenance without opening reference labels."""

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/external-review-i-v1"


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def sha(relative):
    return hashlib.file_digest((ROOT / relative).open("rb"), "sha256").hexdigest()


def reason_group(reason):
    text = reason.lower()
    if "frame count changed" in text:
        return "frame_count_alignment"
    if "cadence differs" in text:
        return "cadence_alignment"
    if "alignment review" in text:
        return "visual_alignment"
    if "403" in text:
        return "http_403"
    if "sign in" in text or "sign-in" in text:
        return "sign_in_required"
    if "not available" in text or "unavailable" in text:
        return "unavailable"
    raise ValueError("Unclassified exclusion; inspect metadata before proceeding")


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    files = {
        "population": "data/raw/childplay/verified-population-v2/population-manifest.json",
        "retained": "data/raw/childplay/verified-population-v2/retained-sources.csv",
        "public_frames": "data/processed/vsgaze-17357752-v1/public/frames.csv",
        "full": "data/raw/childplay/acquisition-full-v1/acquisition.json",
        "review": "data/raw/childplay/acquisition-framecount-review-v1/acquisition.json",
        "inventory": "docs/research/annotation-inventory.json",
        "strict_cache": "outputs/inference/mtgs-strict-shard-v1/inference-provenance.json",
        "remaining_cache": "outputs/inference/mtgs-remaining-shard-v1/inference-provenance.json",
        "script": "scripts/audit_unseen_sources.py",
    }
    pop = read_json(files["population"])
    acq = {key: {r["source_id"]: r for r in read_json(files[key])["sources"]}
           for key in ("full", "review")}
    with (ROOT / files["retained"]).open(newline="") as handle:
        retained = {r["source_id"]: r for r in csv.DictReader(handle)}
    sources = {}
    with (ROOT / files["public_frames"]).open(newline="") as handle:
        for row in csv.DictReader(handle):
            sid, split = row["source_id"], row["split"]
            assert sources.setdefault(sid, split) == split
    excluded = {r["source_id"]: r["reason"] for r in pop["excluded_sources"]}
    cached = set()
    for key in ("strict_cache", "remaining_cache"):
        cached.update(r["source_id"] for r in read_json(files[key])["clips"])
    assert set(sources) == set(acq["full"]) == set(retained) | set(excluded)
    assert not set(retained) & set(excluded)
    assert set(retained) <= cached <= set(sources)
    assert len(retained) == pop["retained_sources"] == 53
    inventory = read_json(files["inventory"])
    assert sum(v["source_videos"] for v in inventory["splits"].values()) == len(sources)
    rows = []
    for index, sid in enumerate(sorted(sources), 1):
        row = {
            "alias": f"I{index:03}", "source_id": sid, "split": sources[sid],
            "in_frozen_population": sid in retained,
            "exclusion_category": reason_group(excluded[sid]) if sid in excluded else None,
            "cached": sid in cached,
            "prior_broad_annotation_inventory": True,
            "source_specific_prior_inspection": "used_in_frozen_study" if sid in retained
            else "not_fully_documented; independence_not_established",
            "accepted_as_unseen": False,
        }
        for key in ("full", "review"):
            record = acq[key].get(sid, {})
            relative = Path(files[key]).parent / record.get("archive", "__absent__")
            archive = ROOT / relative
            exists = "archive" in record and archive.is_file()
            row[key] = {
                "recorded_status": record.get("status", "not_attempted"),
                "archive_exists": exists,
                "recorded_archive_sha256": record.get("archive_sha256"),
                "size_matches": archive.stat().st_size == record.get("archive_bytes")
                if exists else None,
                "archive_hash_recomputed": False,
            }
            assert not exists or row[key]["size_matches"]
        rows.append(row)
    aggregate = {
        "stage": "I-metadata-only-feasibility", "complete": True,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "new_reference_label_values_read": False, "performance_evaluation_run": False,
        "archive_contents_opened": False, "main_population_changed": False,
        "input_sha256": {v: sha(v) for v in files.values()},
        "original_sources": len(sources), "retained_sources": len(retained),
        "excluded_sources": len(excluded),
        "original_splits": dict(Counter(sources.values())),
        "retained_splits": dict(Counter(r["split"] for r in retained.values())),
        "excluded_splits": dict(Counter(sources[sid] for sid in excluded)),
        "exclusion_categories": dict(Counter(reason_group(v) for v in excluded.values())),
        "full_complete": sum(r["status"] == "complete" for r in acq["full"].values()),
        "review_complete": sum(r["status"] == "complete" for r in acq["review"].values()),
        "existing_archives_by_pool": {key: sum(r[key]["archive_exists"] for r in rows)
                                      for key in ("full", "review")},
        "excluded_with_existing_archive": sum(
            not r["in_frozen_population"] and any(r[k]["archive_exists"]
                                                  for k in ("full", "review")) for r in rows),
        "cached_sources": len(cached), "cached_excluded_sources": len(cached & set(excluded)),
        "qualifying_local_unseen_sources": 0,
        "prior_inspection_evidence": inventory["diagnostic_scope"],
        "interpretation": "No local source is presently accepted as independent unseen evidence. "
        "Broad label-summary exposure is known; individual exposure for exclusions is not proven.",
        "checks": {"source_partition": True, "cache_membership": True,
                   "original_inventory_count": True, "present_archive_sizes": True},
    }
    (OUT / "source-ledger.json").write_text(json.dumps(rows, indent=2) + "\n")
    aggregate["local_ledger_sha256"] = sha("outputs/external-review-i-v1/source-ledger.json")
    text = json.dumps(aggregate, indent=2) + "\n"
    (OUT / "result.json").write_text(text)
    (ROOT / "docs/research/i-local-feasibility.json").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
