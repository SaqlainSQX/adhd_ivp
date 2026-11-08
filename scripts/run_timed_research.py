"""Run the registered bounded D round without GPU work."""

import argparse
import traceback
from pathlib import Path

from gaze_audit.timed_research import run

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--config", type=Path, default=Path("configs/timed-research-d-v1.json"))
args = parser.parse_args()
try:
    run(args.config)
except Exception:
    traceback.print_exc()
    raise
