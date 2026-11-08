"""Build registered public-only visual sheets and temporal correspondence flags."""

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/uco-visual-k3-v1"
DATA = ROOT / "data/processed/uco-public-k2-v1"
COLORS = ["#00ff66", "#ffbb00", "#ff44ee", "#55ccff", "#ffffff"]


def people(row):
    return {int(pid): np.asarray(box) for pid, box in
            zip(row["person_ids"], row["head_bboxes"], strict=True) if any(box)}


def iou(a, b):
    overlap = np.maximum(0, np.minimum(a[2:], b[2:]) - np.maximum(a[:2], b[:2])).prod()
    return float(overlap / (np.prod(a[2:] - a[:2]) + np.prod(b[2:] - b[:2]) - overlap))


def panel(row):
    image = Image.open(DATA / "images" / row["clip"] / f"{row['frame']:06d}.jpg").convert("RGB")
    image = image.resize((420, 236))
    draw = ImageDraw.Draw(image)
    for pid, box in people(row).items():
        xy = box * np.array([420, 236, 420, 236])
        color = COLORS[pid % len(COLORS)]
        draw.rectangle(xy.tolist(), outline=color, width=2)
        draw.text((max(0, xy[0]), max(0, xy[1])), str(pid), fill=color,
                  stroke_width=1, stroke_fill="black")
    result = Image.new("RGB", (420, 260), "#101820")
    result.paste(image, (0, 24))
    ImageDraw.Draw(result).text((5, 3), f"{row['clip']} frame {row['frame']:06d}", fill="white")
    return result


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    rows = json.loads((DATA / "public-frames.json").read_text())
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["clip"]].append(row)
    selections = {}
    sheets = []
    for clip, records in sorted(grouped.items()):
        records.sort(key=lambda r: r["frame"])
        indices = np.linspace(0, len(records) - 1, 5).astype(int)
        selected = [records[i] for i in indices]
        selections[clip] = [r["frame"] for r in selected]
        strip = Image.new("RGB", (2100, 260))
        for col, row in enumerate(selected):
            strip.paste(panel(row), (col * 420, 0))
        sheets.append(strip)
    for index in range(3):
        sheet = Image.new("RGB", (2100, 1300))
        for row, strip in enumerate(sheets[index * 5:index * 5 + 5]):
            sheet.paste(strip, (0, row * 260))
        sheet.save(OUT / f"contact-{index + 1}.jpg", quality=95)
    lookup = {(r["clip"], r["frame"]): r for r in rows}
    flags, comparisons, missing = [], 0, 0
    for row in rows:
        for offset in (3, 6):
            other = lookup.get((row["clip"], row["frame"] + offset))
            if other is None:
                missing += 1
                continue
            old, new = people(row), people(other)
            for pid in old.keys() & new.keys():
                comparisons += 1
                same = iou(old[pid], new[pid])
                alternatives = [(iou(old[pid], b), p) for p, b in new.items() if p != pid]
                if alternatives:
                    best, alternative = max(alternatives)
                    if best > .5 and best > same + .2:
                        flags.append({"clip": row["clip"], "frame": row["frame"],
                                      "neighbor": other["frame"], "pid": pid,
                                      "alternative_pid": alternative,
                                      "same_iou": same, "alternative_iou": best})
    (OUT / "temporal-flags.json").write_text(json.dumps(flags, indent=2) + "\n")
    # Local synthetic confirmation of PIL's out-of-image crop padding.
    crop = Image.new("RGB", (10, 10), "white").crop((-2, -2, 4, 4))
    assert crop.getpixel((0, 0)) == (0, 0, 0) and crop.getpixel((3, 3)) == (255, 255, 255)
    result = {"stage": "K3-public-visual-and-identity-screen", "clips": len(grouped),
              "selected_frames": selections, "contact_sheets": 3,
              "same_id_comparisons": comparisons, "alternative_id_iou_flags": len(flags),
              "missing_positive_offset_neighbors": missing,
              "iou_screen_rule": "offset3/6; alternative IoU>.5 and>.2 above same ID",
              "iou_screen_is_not_identity_ground_truth": True,
              "out_of_frame_padding_synthetic_check": True,
              "geometry_altered": False, "reference_fields_accessed": False,
              "visual_review": "pending", "inference_started": False}
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "selected_frames"}, indent=2))


if __name__ == "__main__":
    main()
