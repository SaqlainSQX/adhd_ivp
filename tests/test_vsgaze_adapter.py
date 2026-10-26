import numpy as np
import pytest

from gaze_audit.adapters.vsgaze import normalize_entry, parse_path, prepare_archive


def entry(label=1):
    return {
        "path": "images/abc_def-ghi_10-20/abc_def-ghi_10.jpg",
        "person_ids": np.array([-1, 3, 1001]),
        "head_bboxes": np.array([[0, 0, 0, 0], [0.1, 0.2, 0.3, 0.4], [0.5, 0.2, 0.7, 0.4]]),
        "pairs": np.array([[-1, 3], [1001, 3], [3, 1001]]),
        "laeo_pairs": np.array([-1, label, label]),
        "gaze_points": np.array([[0.1, 0.2]]),
    }


def test_reference_changes_do_not_change_public_features_or_ids():
    first = normalize_entry(entry(0), "train")
    second = normalize_entry(entry(1), "train")
    for key in ["frame", "people", "pairs"]:
        assert first[key] == second[key]
    assert first["oracle"][0]["label"] == 0
    assert second["oracle"][0]["label"] == 1
    assert first["pairs"][0]["person_a"] == 3
    assert first["pairs"][0]["person_b"] == 1001


def test_conflicting_reverse_labels_fail():
    record = entry()
    record["laeo_pairs"][-1] = 0
    with pytest.raises(ValueError, match="Conflicting"):
        normalize_entry(record, "train")


def test_unknown_is_not_a_negative_reference():
    normalized = normalize_entry(entry(-1), "validation")
    assert normalized["oracle"] == []
    assert normalized["pairs"][0]["eligible_anchor"] == 0
    assert normalized["counts"]["unknown"] == 1


def test_invalid_geometry_excluded_and_clipping_recorded():
    record = entry()
    record["head_bboxes"][1] = [-0.1, 0.2, 0.3, 0.4]
    normalized = normalize_entry(record, "train")
    assert normalized["people"][0]["bbox_clipped"] == 1
    assert normalized["pairs"][0]["eligible_anchor"] == 1
    record["head_bboxes"][1] = [2, 0.2, 3, 0.4]
    normalized = normalize_entry(record, "train")
    assert normalized["oracle"] == []
    assert normalized["pairs"][0]["geometry_valid"] == 0


def test_downsampled_path_preserves_source_and_original_index():
    parsed = parse_path("images/abc_def-ghi_10-20-downsampled/abc_def-ghi_12.jpg")
    assert parsed["source_id"] == "abc_def-ghi"
    assert parsed["downsampled"] is True
    assert parsed["original_frame_index"] == 12


def test_wrong_archive_rejected_before_creating_output(tmp_path):
    archive = tmp_path / "wrong.tar.gz"
    archive.write_bytes(b"not the pinned archive")
    with pytest.raises(ValueError, match="checksum-pinned"):
        prepare_archive(archive, tmp_path / "output")
    assert not (tmp_path / "output").exists()
