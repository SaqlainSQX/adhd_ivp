"""K2: supplied test images and public geometry only; no reference-field access."""

import hashlib
import json
import re
import tarfile
from collections import Counter
from pathlib import Path, PurePosixPath

import numpy as np
from PIL import Image

from gaze_audit.adapters.vsgaze import read_release_table

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/uco-public-k2-v1"
DEST = ROOT / "data/processed/uco-public-k2-v1"


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    DEST.mkdir(parents=True, exist_ok=False)
    clips = set(json.loads((ROOT / "docs/research/j-uco-contract.json").read_text())[
        "official_splits"]["testVids"])
    archive = ROOT / "data/raw/uco/acquisition-k-v1/ucolaeodb_v1.1.tgz"
    size = 0
    count = Counter()
    with tarfile.open(archive, "r|gz") as handle:
        for member in handle:
            parts = PurePosixPath(member.name).parts
            if (len(parts) != 4 or parts[:2] != ("ucolaeodb", "frames")
                    or parts[2] not in clips or not re.fullmatch(r"\d{6}\.jpg", parts[3])):
                continue
            assert member.isfile()
            size += member.size
            assert size <= 8 * 1024**3 and size + archive.stat().st_size <= 20 * 1024**3
            target = DEST / "images" / parts[2] / parts[3]
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as output:
                output.write(handle.extractfile(member).read())
            count[parts[2]] += 1
    assert set(count) == clips
    with tarfile.open(ROOT / "data/research/VSGaze.tar.gz") as handle:
        columns, values = read_release_table(handle, "VSGaze/uco_laeo_test.h5")
    indices = {name: columns.index(name) for name in ("path", "head_bboxes", "person_ids")}
    rows, missing, issues = [], [], []
    for value in values:
        original = str(value[indices["path"]])
        parts = PurePosixPath(original.replace("\\", "/")).parts
        clip, frame = parts[-2].lower(), parts[-1]
        assert clip in clips and re.fullmatch(r"\d{6}\.jpg", frame)
        target = DEST / "images" / clip / frame
        if not target.is_file():
            missing.append(original)
            continue
        pids = np.asarray(value[indices["person_ids"]]).reshape(-1)
        boxes = np.asarray(value[indices["head_bboxes"]], dtype=float)
        assert boxes.shape == (len(pids), 4)
        valid = ~np.all(boxes == 0, axis=1)
        b = boxes[valid]
        if (not np.isfinite(b).all() or (b < 0).any() or (b > 1).any()
                or (b[:, 2:] <= b[:, :2]).any()):
            issues.append(original)
        with Image.open(target) as image:
            dimensions = image.size
            image.verify()
        rows.append({"original_path": original, "clip": clip, "frame": int(frame[:-4]),
                     "width": dimensions[0], "height": dimensions[1],
                     "person_ids": pids.tolist(), "head_bboxes": boxes.tolist()})
    keys = [(r["clip"], r["frame"]) for r in rows]
    assert len(keys) == len(set(keys))
    (DEST / "public-frames.json").write_text(json.dumps(rows) + "\n")
    (OUT / "mapping-issues.json").write_text(json.dumps({"missing": missing,
                                                       "geometry": issues}, indent=2) + "\n")
    result = {"stage": "K2-public-mapping", "source_rows": len(values), "mapped_rows": len(rows),
              "missing_rows": len(missing), "geometry_issue_rows": len(issues),
              "test_clips": len(clips), "extracted_images": sum(count.values()),
              "extracted_bytes": size, "images_by_clip": dict(count),
              "public_table_sha256": hashlib.sha256((DEST / "public-frames.json").read_bytes())
              .hexdigest(), "mixed_container_deserialized": True,
              "reference_fields_accessed": False, "performance_evaluated": False,
              "visual_and_temporal_identity_gates": "pending"}
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
