"""Map annotation filenames to decoded source positions using release extraction rules."""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

SPECIAL_CLIPS = frozenset(
    {
        "smwfiZd8HLc_7508-8408-downsampled",
        "smwfiZd8HLc_10346-12974-downsampled",
        "smwfiZd8HLc_16176-16586-downsampled",
        "smwfiZd8HLc_20322-20668-downsampled",
        "31lG75MDwSA_2857-2928",
        "31lG75MDwSA_3180-3306",
        "31lG75MDwSA_4686-4764",
        "EuYseDl2jm8_1869-2033",
        "EuYseDl2jm8_3680-3791",
    }
)


def map_frame(frame: dict, clip: dict, video: dict) -> dict:
    """P02 original_frame_index is an annotation filename index, not decoded position."""
    if frame["clip_id"] != clip["clip"] or frame["source_id"] != clip["video_id"]:
        raise ValueError("Clip/source metadata disagree")
    split = {"val": "validation"}.get(clip["split"], clip["split"])
    if frame["split"] != split:
        raise ValueError("Official source split disagrees with VSGaze")
    start = int(frame["source_start_index"])
    filename_index = int(frame["original_frame_index"])
    relative = filename_index - start + 1
    if not 1 <= relative <= int(clip["frame_count"]):
        raise ValueError("Annotation filename lies outside released clip length")
    downsampled = frame["clip_id"].endswith("-downsampled")
    lagged = frame["clip_id"] in SPECIAL_CLIPS
    stride = 2 if downsampled else 1
    decoded_index = start - 1 + stride * (relative - 1) + int(downsampled) - int(lagged)
    if decoded_index < 0:
        raise ValueError("Negative source position")
    return {
        "frame_id": frame["frame_id"],
        "clip_id": frame["clip_id"],
        "source_id": frame["source_id"],
        "split": frame["split"],
        "annotation_filename_index": filename_index,
        "clip_frame_index_1based": relative,
        "source_frame_index_0based": decoded_index,
        "source_stride": stride,
        "release_one_frame_lag": int(lagged),
        "metadata_source_fps": video["fps"],
        "metadata_clip_fps": clip["fps"],
        "annotation_path": frame["annotation_path"],
        "media_status": "not_yet_verified",
    }


def prepare_mapping(processed: Path, metadata: Path, output: Path) -> dict:
    if output.exists():
        raise ValueError("Use a new output directory; completed stage artifacts are immutable")

    def read(path):
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    clips = {r["clip"]: r for r in read(metadata / "clips.csv")}
    videos = {r["video_id"]: r for r in read(metadata / "videos.csv")}
    frames = read(processed / "public/frames.csv")
    mapped = [map_frame(r, clips[r["clip_id"]], videos[r["source_id"]]) for r in frames]
    output.mkdir(parents=True)
    path = output / "frame_mapping.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(mapped[0]))
        writer.writeheader()
        writer.writerows(mapped)
    report = {
        "stage": "P03-mapping",
        "mapping_complete": True,
        "media_alignment_complete": False,
        "frames": len(mapped),
        "split_counts": dict(Counter(r["split"] for r in mapped)),
        "downsampled_frames": sum(r["source_stride"] == 2 for r in mapped),
        "lagged_release_frames": sum(r["release_one_frame_lag"] for r in mapped),
        "mapping_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "inputs_sha256": {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [
                processed / "manifest.json",
                metadata / "clips.csv",
                metadata / "videos.csv",
                metadata / "extract-clips-from-videos.py",
            ]
        },
        "index_semantics": "P02 original_frame_index denotes annotation filename index only",
        "formula_0based": "start-1+stride*(clip_frame_1based-1)+downsampled-special_lag",
        "release_frame_difference": sum(int(c["frame_count"]) for c in clips.values())
        - len(mapped),
    }
    (output / "mapping-report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report
