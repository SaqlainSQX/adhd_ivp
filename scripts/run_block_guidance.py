"""Execute only the registered G2 block-guidance experiment."""

import argparse
from pathlib import Path

from gaze_audit.block_guidance import run

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--config", type=Path, default=Path("configs/block-guidance-g2-v1.json"))
run(parser.parse_args().config)
