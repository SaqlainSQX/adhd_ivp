"""Create a label-free source-decode mapping before media alignment review."""

import argparse
import json
from pathlib import Path

from gaze_audit.adapters.childplay_media import prepare_mapping

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--processed", type=Path, default=Path("data/processed/vsgaze-17357752-v1"))
parser.add_argument("--metadata", type=Path, default=Path("data/research/childplay-metadata"))
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
print(json.dumps(prepare_mapping(args.processed, args.metadata, args.output), indent=2))
