import pytest

from gaze_audit.adapters.childplay_media import map_frame


@pytest.mark.parametrize(
    "clip,start,offset,expected",
    [
        ("source_10-20", 10, 2, 11),
        ("source_10-20-downsampled", 10, 2, 14),
        ("31lG75MDwSA_2857-2928", 2857, 2, 2857),
        ("smwfiZd8HLc_7508-8408-downsampled", 7508, 2, 7511),
    ],
)
def test_mapping_matches_official_decode_loop(clip, start, offset, expected):
    source = clip.rsplit("_", 1)[0]
    frame = {
        "frame_id": "f",
        "clip_id": clip,
        "source_id": source,
        "split": "validation",
        "source_start_index": start,
        "original_frame_index": start + offset,
        "annotation_path": "images/f.jpg",
    }
    metadata = {"clip": clip, "video_id": source, "split": "val", "frame_count": 20, "fps": 30}
    result = map_frame(frame, metadata, {"fps": 60 if "downsampled" in clip else 30})
    assert result["source_frame_index_0based"] == expected
    assert result["clip_frame_index_1based"] == 3


def test_mapping_rejects_out_of_range_filename():
    frame = {
        "frame_id": "f",
        "clip_id": "source_10-20",
        "source_id": "source",
        "split": "train",
        "source_start_index": 10,
        "original_frame_index": 0,
    }
    with pytest.raises(ValueError, match="outside"):
        map_frame(
            frame,
            {"clip": "source_10-20", "video_id": "source", "split": "train", "frame_count": 11},
            {"fps": 30},
        )
