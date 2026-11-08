import json
from pathlib import Path

import pytest

from gaze_audit.transfer_appendix import SOURCES, build_summary

ROOT = Path(__file__).resolve().parents[1]


def test_projection_matches_frozen_outcomes_and_excludes_individual_data():
    data = build_summary(ROOT)
    source = json.loads((ROOT / "docs/research/l-transfer-result.json").read_text())
    assert len(data["uco"]["rows"]) == 12
    for row in data["uco"]["rows"]:
        original = source["results"][f"{row['method']}-b{row['budget']}"]
        assert row["rmse_pp"] == original["rmse_pp"]
        assert row["exact"] == original["intervals"]["exact_binary_reference"]
    assert data["uco"]["comparisons"]["power-score/K4-b521"]["rmse_ratio"] > 1
    payload = json.dumps(data)
    for private in ['"record_id"', '"person_id"', '"selected"', '"label"', '"prediction_rows"']:
        assert private not in payload


def test_projection_rejects_changed_evidence(tmp_path):
    for source, manifest in SOURCES.items():
        for name in [source, manifest]:
            target = tmp_path / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / name).read_bytes())
    target = tmp_path / "docs/research/l-transfer-result.json"
    target.write_text(target.read_text().replace('"complete": true', '"complete": false'))
    with pytest.raises(AssertionError):
        build_summary(tmp_path)
