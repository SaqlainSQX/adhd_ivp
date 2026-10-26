"""Run the same public-media acquisition code on this PC, with project-local outputs."""

import argparse
import json
import os
import runpy
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--config", type=Path)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--direct", action="store_true")
args = parser.parse_args()
config = {
    "mode": "pilot",
    "sources": ["1Aea8BH-PCs", "31lG75MDwSA", "smwfiZd8HLc"],
    "clips_per_source": 1,
    "shard_index": 0,
    "shard_count": 1,
}
if args.config:
    config = json.loads(args.config.read_text())
config["metadata_archive"] = "outputs/kaggle-discovery-v1/ChildPlay-gaze.tar.gz"
if args.direct:
    for key in list(os.environ):
        if key.upper() in {"HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"}:
            del os.environ[key]
runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "jobs/acquire_media.py"),
    init_globals={
        "JOB_CONFIG": config,
        "OUTPUT_ROOT": str(args.output.resolve()),
        "SCRATCH_ROOT": str((args.output / "scratch").resolve()),
    },
    run_name="__main__",
)
