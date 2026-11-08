"""Build a portable aggregate-only research dashboard from tracked evidence."""

import json
from pathlib import Path

from gaze_audit.research_explorer import build_summary

project = Path(__file__).resolve().parents[1]
summary = build_summary(project)
target = project / "demo/research"
target.mkdir(parents=True, exist_ok=True)
payload = json.dumps(summary, indent=2, allow_nan=False)
(target / "data.json").write_text(payload + "\n", encoding="utf-8")
(target / "data.js").write_text("window.RESEARCH_DATA = " + payload + ";\n", encoding="utf-8")
print("Built aggregate-only research data; no raw labels, media or queries included.")
