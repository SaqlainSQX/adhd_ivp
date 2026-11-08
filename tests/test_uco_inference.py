import itertools
import json

import numpy as np
import pytest

from gaze_audit.uco_inference import decode_scores, load_public


def test_decoder_uses_track_slots_and_both_directions():
    order = list(itertools.permutations(range(4), 2))
    lah = np.zeros(12)
    lah[order.index((3, 1))], lah[order.index((1, 3))] = 0.8, 0.3
    result = decode_scores(lah, [19, 7, 42], [{"record_id": "r", "person_a": 19, "person_b": 42}])[
        0
    ]
    assert result == {"record_id": "r", "q": 0.3, "direction_a_to_b": 0.8, "direction_b_to_a": 0.3}


def test_decoder_rejects_nonfinite_and_wrong_native_reconstruction():
    pair = [{"record_id": "r", "person_a": 1, "person_b": 2}]
    with pytest.raises(ValueError, match="Invalid native"):
        decode_scores([np.nan] * 6, [1, 2], pair)
    with pytest.raises(ValueError, match="reconstruction"):
        decode_scores(np.zeros(6), [1, 2], pair, np.ones(6))


def test_public_loader_preserves_border_boxes_without_oracle(tmp_path):
    path = tmp_path / "data/processed/uco-public-k2-v1"
    path.mkdir(parents=True)
    row = {
        "clip": "x",
        "frame": 0,
        "person_ids": [0, 8, 3],
        "head_bboxes": [[0, 0, 0, 0], [-0.1, 0.1, 0.2, 0.5], [0.5, 0.1, 0.8, 0.5]],
    }
    (path / "public-frames.json").write_text(json.dumps([row]))
    pairs = tmp_path / "data/processed/uco-eligible-k4-v2"
    pairs.mkdir()
    (pairs / "eligible-pairs.csv").write_text("record_id,clip,frame,person_a,person_b\nr,x,0,3,8\n")
    frames, people, mapped = load_public(tmp_path)
    assert frames["x", 0]["annotation_path"] == "x/000000.jpg"
    assert set(people["x:0"]) == {3, 8}
    assert people["x:0"][8][0] == -0.1
    assert mapped["x:0"][0]["record_id"] == "r"
    assert not (pairs / "oracle.csv").exists()
