"""Execute only the registered round-C queue, sequentially, with no GPU work."""

import os

for key in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"]:
    os.environ[key] = "1"

import argparse  # noqa: E402
import json  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from pathlib import Path  # noqa: E402

from gaze_audit.extra_experiments import run_stage  # noqa: E402
from gaze_audit.strengthening import write_json  # noqa: E402

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("stage", choices=["all", "ridge", "cost", "squared-rf"])
parser.add_argument("--config", type=Path, default=Path("configs/extra-experiments-c-v1.json"))
args = parser.parse_args()
config = json.loads(args.config.read_text())
root = Path(config["output"])
root.mkdir(parents=True, exist_ok=True)
for short, stage in [
    ("ridge", "C1-ridge"),
    ("cost", "C2-label-cost"),
    ("squared-rf", "C3-squared-rf"),
]:
    if args.stage not in ["all", short]:
        continue
    status = {
        "stage": stage,
        "state": "running",
        "updated_utc": datetime.now(timezone.utc).isoformat(),
    }
    write_json(root / "status.json", status)
    try:
        result = run_stage(args.config, stage)
    except Exception as exc:
        status.update(
            state="failed",
            error=f"{type(exc).__name__}: {exc}",
            updated_utc=datetime.now(timezone.utc).isoformat(),
        )
        write_json(root / "status.json", status)
        raise
    status.update(
        state="completed",
        elapsed_seconds=result["elapsed_seconds"],
        updated_utc=datetime.now(timezone.utc).isoformat(),
    )
    write_json(root / "status.json", status)
print("Registered C stages complete; independent verification and report QA follow.", flush=True)
