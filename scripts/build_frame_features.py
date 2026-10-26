"""P06: generate versioned static/temporal features from public geometry and frozen q."""

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from gaze_audit.frame_features import build_static, build_temporal

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--processed", type=Path, default=Path("data/processed/vsgaze-17357752-v1"))
parser.add_argument(
    "--mapping", type=Path, default=Path("data/processed/childplay-mapping-v1/frame_mapping.csv")
)
parser.add_argument("--predictions", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
if args.output.exists():
    parser.error("Choose a new feature directory")
inputs = {
    "pairs": args.processed / "public/public_pairs.csv",
    "people": args.processed / "public/public_people.csv",
    "mapping": args.mapping,
    "predictions": args.predictions,
}
tables = {key: pd.read_csv(path) for key, path in inputs.items()}
static = build_static(**tables)
args.output.mkdir(parents=True)
report = {
    "stage": "P06",
    "complete": False,
    "oracle_values_used": False,
    "inputs_sha256": {
        key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in inputs.items()
    },
    "feature_files": {},
}
for name, data in [
    ("static", static),
    ("temporal-w5", build_temporal(static, 5)),
    ("temporal-w11", build_temporal(static, 11)),
]:
    target = args.output / f"features-{name}.csv"
    data.to_csv(target, index=False)
    report["feature_files"][name] = {
        "filename": target.name,
        "rows": len(data),
        "feature_columns": [column for column in data if column.startswith("f_")],
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
    }
report["complete"] = True
(args.output / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"stage": "P06", "rows": len(static), "output": str(args.output)}, indent=2))
