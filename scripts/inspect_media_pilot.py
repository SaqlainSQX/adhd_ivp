"""Create public-geometry contact sheets and verify all pilot JPEG paths."""

import argparse
import hashlib
import json
import tarfile
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--acquisition", type=Path, required=True)
parser.add_argument("--processed", type=Path, default=Path("data/processed/vsgaze-17357752-v1"))
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--page-rows", type=int, default=4)
args = parser.parse_args()
if args.output.exists():
    parser.error("Choose a new review output directory")
report = json.loads((args.acquisition / "acquisition.json").read_text())
frames = pd.read_csv(args.processed / "public/frames.csv")
people = pd.read_csv(args.processed / "public/public_people.csv")
args.output.mkdir(parents=True)
panels, checks = [], []
for source in report["sources"]:
    if source["status"] != "complete":
        continue
    path = args.acquisition / source["archive"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != source["archive_sha256"]:
        raise ValueError("Acquisition archive hash mismatch")
    with tarfile.open(path) as archive:
        members = {member.name: member for member in archive if member.isfile()}
        for clip in source["clips"]:
            subset = frames[frames.clip_id == clip["clip_id"]].sort_values("original_frame_index")
            missing = [p for p in subset.annotation_path if p not in members]
            checks.append(
                {
                    "clip_id": clip["clip_id"],
                    "expected_vsgaze_frames": len(subset),
                    "missing_frames": len(missing),
                    "downloaded_frames": clip["frames"],
                }
            )
            if missing or len(subset) == 0:
                raise ValueError("Pilot clip missing expected VSGaze paths")
            for position in sorted({0, len(subset) // 2, len(subset) - 1}):
                row = subset.iloc[position]
                payload = archive.extractfile(members[row.annotation_path]).read()
                image = cv2.imdecode(np.frombuffer(payload, np.uint8), cv2.IMREAD_COLOR)
                if image is None:
                    raise ValueError("Pilot JPEG decode failed")
                height, width = image.shape[:2]
                for person in people[people.frame_id == row.frame_id].itertuples():
                    a = (round(person.xmin * width), round(person.ymin * height))
                    b = (round(person.xmax * width), round(person.ymax * height))
                    cv2.rectangle(image, a, b, (0, 255, 0), max(2, round(width / 500)))
                    cv2.putText(
                        image,
                        str(person.person_id),
                        a,
                        cv2.FONT_HERSHEY_SIMPLEX,
                        width / 1200,
                        (0, 255, 0),
                        2,
                    )
                image = cv2.resize(image, (600, 338))
                panel = np.zeros((390, 600, 3), dtype=np.uint8)
                panel[:338] = image
                cv2.putText(
                    panel,
                    f"{row.source_id} / {row.original_frame_index}",
                    (8, 360),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    1,
                )
                cv2.putText(
                    panel,
                    row.clip_id.split("_", 1)[-1],
                    (8, 382),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1,
                )
                panels.append(panel)
if not panels:
    raise ValueError("No completed media source available for review")
while len(panels) % 3:
    panels.append(np.zeros_like(panels[0]))
paths = []
for page, offset in enumerate(range(0, len(panels), args.page_rows * 3)):
    subset = panels[offset : offset + args.page_rows * 3]
    sheet = np.vstack([np.hstack(subset[i : i + 3]) for i in range(0, len(subset), 3)])
    path = args.output / f"geometry-contact-sheet-{page + 1:02d}.jpg"
    cv2.imwrite(str(path), sheet)
    paths.append(str(path))
(args.output / "review-checks.json").write_text(
    json.dumps(
        {
            "clip_checks": checks,
            "geometry_visual_review": "pending human/agent inspection",
            "oracle_values_used": False,
        },
        indent=2,
    )
)
print("\n".join(paths))
