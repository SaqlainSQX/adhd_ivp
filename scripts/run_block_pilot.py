"""Execute registered G1 uniform-block pilot."""

from pathlib import Path

from gaze_audit.block_pilot import run

run(Path("configs/block-pilot-g-v1.json"))
