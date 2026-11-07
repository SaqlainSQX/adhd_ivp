"""Execute a registered E05 interpretation check with the existing frozen cache."""

import argparse
import time
from pathlib import Path

from gaze_audit.followups import run_followup

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("stage", choices=["windows", "summary-only"])
parser.add_argument("--main", type=Path, default=Path("outputs/experiments/course-20261107-v1"))
parser.add_argument("--processed", type=Path, default=Path("data/processed/vsgaze-17357752-v1"))
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--draws", type=int, default=1000)
parser.add_argument("--validation-draws", type=int, default=100)
args = parser.parse_args()
started = time.monotonic()
run_followup(
    args.stage,
    args.main,
    args.processed,
    args.output,
    draws=args.draws,
    validation_draws=args.validation_draws,
)
print(f"Completed {args.stage} in {time.monotonic() - started:.1f} seconds", flush=True)
