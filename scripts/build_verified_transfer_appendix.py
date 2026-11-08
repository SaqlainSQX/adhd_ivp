"""Build the portable appendix with explicit integrity validation, including under -O."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gaze_audit.verified_transfer_appendix import build_verified_summary

root = Path(__file__).resolve().parents[1]
payload = json.dumps(build_verified_summary(root), indent=2, allow_nan=False)
target = root / "demo/transfer"
target.mkdir(parents=True, exist_ok=True)
(target / "data.json").write_text(payload + "\n", encoding="utf-8")
(target / "data.js").write_text("window.TRANSFER_DATA = " + payload + ";\n", encoding="utf-8")
print("Built explicitly verified aggregate appendix; no raw data or model accessed.")
