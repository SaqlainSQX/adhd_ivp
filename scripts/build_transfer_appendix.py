"""Build portable, aggregate-only appendix assets from pinned tracked evidence."""

import json
from pathlib import Path

from gaze_audit.transfer_appendix import build_summary

root = Path(__file__).resolve().parents[1]
target = root / "demo/transfer"
target.mkdir(parents=True, exist_ok=True)
payload = json.dumps(build_summary(root), indent=2, allow_nan=False)
(target / "data.json").write_text(payload + "\n")
(target / "data.js").write_text("window.TRANSFER_DATA = " + payload + ";\n")
print("Built pinned aggregate appendix; no raw data or model accessed.")
