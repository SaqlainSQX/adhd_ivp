"""Execute registered course-strengthening stages using the immutable cache."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from gaze_audit.strengthening import run_baselines, run_coverage, write_json

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("stage", choices=["baselines", "coverage", "all"])
parser.add_argument("--config", type=Path, default=Path("configs/strengthening-v1.json"))
args = parser.parse_args()
config = json.loads(args.config.read_text())
root = Path(config["output"])
root.mkdir(parents=True, exist_ok=True)
for stage, runner in [("baselines", run_baselines), ("coverage", run_coverage)]:
    if args.stage not in ["all", stage]:
        continue
    status = {
        "stage": stage,
        "state": "running",
        "updated_utc": datetime.now(timezone.utc).isoformat(),
    }
    write_json(root / "status.json", status)
    try:
        report = runner(args.config)
    except Exception as exc:
        status.update(state="failed", error=f"{type(exc).__name__}: {exc}")
        write_json(root / "status.json", status)
        raise
    status.update(state="completed", elapsed_seconds=report["elapsed_seconds"])
    write_json(root / "status.json", status)
print("Registered requested stages completed; figures/report/demo QA follow.", flush=True)
