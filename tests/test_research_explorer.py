import json
from pathlib import Path

import pytest

from gaze_audit.research_explorer import ResearchExplorer, build_summary

PROJECT = Path(__file__).resolve().parents[1]


def test_aggregate_dashboard_matches_tracked_evidence_and_needs_no_raw_cache(tmp_path):
    data = build_summary(PROJECT)
    built = json.loads((PROJECT / "demo/research/data.json").read_text())
    assert data == built
    assert data["frame"]["results"]["power-score-b1032"]["rmse_pp"] == pytest.approx(
        0.1967251202605417, abs=1e-6
    )
    assert data["source_variation"]["assessment"]["positive_sources"] == dict(total=6, improved=3)
    assert data["block_primary"]["rmse_ratio"] > 1
    encoded = json.dumps(data)
    assert "KGAT_" not in encoded and "record_id" not in encoded
    assert "timeline" not in data and "queries" not in data
    offline = ResearchExplorer(tmp_path, aggregate_only=True)
    assert offline.health()["ready"] and not offline.health()["replay_available"]
    with pytest.raises(FileNotFoundError):
        offline.replay()


@pytest.fixture(scope="module")
def explorer():
    instance = ResearchExplorer(PROJECT)
    if not instance.health()["replay_available"]:
        pytest.skip("Optional accepted raw caches are not installed in this checkout")
    return instance


@pytest.mark.parametrize("method", ["power-score", "K4", "power-uniform"])
@pytest.mark.parametrize("fraction,draw", [(0.05, 0), (0.1, 17), (0.2, 500), (0.4, 999)])
def test_replay_matches_accepted_audits_and_hides_labels_by_default(
    explorer, method, fraction, draw
):
    replay = explorer.replay(method, fraction, draw)
    assert replay["verified"] and not replay["labels_revealed"]
    assert len(replay["queries"]) == replay["budget"] == replay["estimate"]["labels_revealed"]
    assert len({r["id"] for r in replay["queries"]}) == replay["budget"]
    assert all(r["label"] is None for r in replay["queries"] + replay["timeline"])
    assert "truth" not in replay and "reference_prevalence" not in replay
    assert replay["correction_weight"] == (1 if method == "K4" else 0.5)
    assert not replay["exact_binary_reference"]["centers_on_residual_estimate"]


def test_revealed_labels_are_exactly_queries_and_score_queries_are_shared(explorer):
    weighted = explorer.replay("power-score", 0.1, 17, reveal=True)
    base = explorer.replay("K4", 0.1, 17)
    assert [r["id"] for r in weighted["queries"]] == [r["id"] for r in base["queries"]]
    selected = {r["id"]: r["label"] for r in weighted["queries"]}
    assert set(selected.values()) <= {0, 1}
    for row in weighted["timeline"]:
        assert row["label"] == selected.get(row["id"])


@pytest.mark.parametrize(
    "method,fraction,draw",
    [
        ("../../secret", 0.1, 0),
        ("power-score", 0.11, 0),
        ("K4", 0.1, -1),
        ("K4", 0.1, 1000),
        ("K4", 0.1, True),
    ],
)
def test_invalid_replay_inputs_are_rejected_without_loading(method, fraction, draw, tmp_path):
    with pytest.raises(ValueError):
        ResearchExplorer(tmp_path).replay(method, fraction, draw)


def test_unknown_frame_cannot_access_an_arbitrary_path(explorer):
    with pytest.raises(ValueError):
        explorer.frame("../../credentials")
