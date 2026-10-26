"""Label-free pair-frame geometry and bounded, gap-aware temporal context."""

import numpy as np
import pandas as pd

FORBIDDEN = {
    "label",
    "gaze_points",
    "inout",
    "lah_pairs",
    "laeo_pairs",
    "coatt_pairs",
    "gaze_class",
    "gaze_x",
    "gaze_y",
}
IDENTITY = [
    "record_id",
    "split",
    "frame_id",
    "source_id",
    "clip_id",
    "person_a",
    "person_b",
    "clip_frame_index_1based",
    "eligible_anchor",
]


def build_static(pairs, people, mapping, predictions):
    for table in [pairs, people, mapping, predictions]:
        if FORBIDDEN & set(table.columns):
            raise ValueError("Reference values are forbidden feature-builder inputs")
    if len(predictions) == 0 or predictions.record_id.duplicated().any():
        raise ValueError("Prediction IDs must be nonempty and unique")
    required = ["record_id", "q", "direction_a_to_b", "direction_b_to_a"]
    data = pairs.merge(predictions[required], on="record_id", how="inner", validate="one_to_one")
    if len(data) != len(predictions) or not data.geometry_valid.eq(1).all():
        raise ValueError("Every prediction must match a geometry-valid public pair")
    data = data.merge(
        mapping[["frame_id", "clip_frame_index_1based"]],
        on="frame_id",
        how="left",
        validate="many_to_one",
    )
    if data.clip_frame_index_1based.isna().any():
        raise ValueError("Missing source-frame mapping")
    scores = data[["q", "direction_a_to_b", "direction_b_to_a"]].to_numpy(float)
    if not np.isfinite(scores).all() or np.any((scores < 0) | (scores > 1)):
        raise ValueError("All public scores must be finite probabilities")
    if not np.allclose(
        data.q, data[["direction_a_to_b", "direction_b_to_a"]].min(axis=1), rtol=0, atol=1e-6
    ):
        raise ValueError("Native q must be the minimum of directional scores")
    result = data[IDENTITY].copy()
    for score in ["q", "direction_a_to_b", "direction_b_to_a"]:
        result[f"f_{score}"] = data[score].to_numpy(float)
    difference = data.direction_a_to_b - data.direction_b_to_a
    result["f_direction_signed_difference"] = difference.to_numpy()
    result["f_direction_absolute_difference"] = difference.abs().to_numpy()
    q = np.clip(data.q.to_numpy(), 1e-12, 1 - 1e-12)
    result["f_q_entropy"] = -(q * np.log(q) + (1 - q) * np.log(1 - q))
    centers = {}
    for suffix, id_column in [("a", "person_a"), ("b", "person_b")]:
        geometry = data[["frame_id", id_column]].merge(
            people,
            left_on=["frame_id", id_column],
            right_on=["frame_id", "person_id"],
            how="left",
            validate="many_to_one",
        )
        if not geometry.geometry_valid.eq(1).all():
            raise ValueError("Missing or invalid person geometry")
        width = geometry.xmax.to_numpy() - geometry.xmin.to_numpy()
        height = geometry.ymax.to_numpy() - geometry.ymin.to_numpy()
        x, y = geometry.xmin.to_numpy() + width / 2, geometry.ymin.to_numpy() + height / 2
        centers[suffix] = (x, y)
        for name, values in [
            ("center_x", x),
            ("center_y", y),
            ("width", width),
            ("height", height),
            ("area", width * height),
        ]:
            result[f"f_head_{suffix}_{name}"] = values
    result["f_pair_center_distance"] = np.hypot(
        centers["a"][0] - centers["b"][0], centers["a"][1] - centers["b"][1]
    )
    result["f_head_area_ratio"] = result.f_head_a_area / np.maximum(result.f_head_b_area, 1e-6)
    occupancy = people.loc[people.geometry_valid == 1].groupby("frame_id").size()
    result["f_real_person_occupancy"] = result.frame_id.map(occupancy)
    if not np.isfinite(result.filter(regex="^f_").to_numpy()).all():
        raise ValueError("Nonfinite geometry feature")
    return result


def _window(values, width):
    values = np.asarray(values, dtype=float)
    padded = np.pad(values, (width // 2, width // 2), constant_values=np.nan)
    return np.lib.stride_tricks.sliding_window_view(padded, width)


def _mean_adjacent_change(windows):
    change = np.abs(np.diff(windows, axis=1))
    count = np.isfinite(change).sum(axis=1)
    return np.divide(np.nansum(change, axis=1), count, out=np.zeros(len(windows)), where=count > 0)


def build_temporal(static: pd.DataFrame, width: int) -> pd.DataFrame:
    if width not in [5, 11]:
        raise ValueError("Use a prespecified temporal width of 5 or 11")
    if FORBIDDEN & set(static.columns):
        raise ValueError("Reference values are forbidden feature-builder inputs")
    sequence = ["clip_id", "person_a", "person_b"]
    result = (
        static.sort_values(sequence + ["clip_frame_index_1based"]).reset_index(drop=True).copy()
    )
    if result.duplicated(sequence + ["clip_frame_index_1based"]).any():
        raise ValueError("Duplicate pair-frame timeline position")
    same_sequence = result[sequence].eq(result[sequence].shift()).all(axis=1)
    continuous = result.clip_frame_index_1based.diff().eq(1)
    segment = (~(same_sequence & continuous)).cumsum()
    for _, rows in result.groupby(segment, sort=False):
        q = rows.f_q.to_numpy()
        windows = _window(q, width)
        features = {
            "q_mean": np.nanmean(windows, axis=1),
            "q_std": np.nanstd(windows, axis=1),
            "q_min": np.nanmin(windows, axis=1),
            "q_max": np.nanmax(windows, axis=1),
            "q_adjacent_change_mean": _mean_adjacent_change(windows),
            "q_previous_difference": np.r_[0, np.diff(q)],
            "q_next_difference": np.r_[np.diff(q), 0],
            "available_context_count": np.isfinite(windows).sum(axis=1),
            "previous_context_missing": np.r_[1, np.zeros(len(rows) - 1)],
            "next_context_missing": np.r_[np.zeros(len(rows) - 1), 1],
        }
        imbalance = _window(rows.f_direction_signed_difference.to_numpy(), width)
        features["direction_imbalance_mean"] = np.nanmean(imbalance, axis=1)
        features["direction_imbalance_std"] = np.nanstd(imbalance, axis=1)
        for column in ["head_a_area", "head_b_area", "pair_center_distance"]:
            features[f"{column}_change_mean"] = _mean_adjacent_change(
                _window(rows[f"f_{column}"].to_numpy(), width)
            )
        for name, values in features.items():
            result.loc[rows.index, f"f_t_{name}"] = values
    if not np.isfinite(result.filter(regex="^f_").to_numpy()).all():
        raise ValueError("Nonfinite temporal feature")
    return result
