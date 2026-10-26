"""P02: export the checksum-pinned VSGaze ChildPlay annotation tables."""

import argparse
import json
from pathlib import Path

from gaze_audit.adapters.vsgaze import prepare_archive

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=Path("data/research/VSGaze.tar.gz"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/vsgaze-17357752-v1"))
    args = parser.parse_args()
    result = prepare_archive(args.archive, args.output)
    print(
        json.dumps(
            {
                "completed": result["completed"],
                "output": str(args.output.resolve()),
                "splits": result["splits"],
            },
            indent=2,
        )
    )
