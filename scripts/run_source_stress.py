"""Execute the registered frozen-query source sensitivity diagnostic."""

from pathlib import Path

from gaze_audit.source_stress import run

run(Path("configs/source-stress-e-v1.json"))
