"""Normalized prediction cache. Hidden label values never enter block features."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

KEY = ["source_id", "clip_id", "frame_index", "person_a", "person_b"]
FEATURES = ["q_mean", "q_std", "q_sum", "entropy", "variation", "cost"]


def normalize_predictions(frame: pd.DataFrame) -> pd.DataFrame:
    required = ["record_id", *KEY, "probability"]
    missing = set(required) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing prediction columns: {sorted(missing)}")
    if set(frame.columns) - set(required):
        raise ValueError("Prediction cache must contain only the documented columns (no labels)")
    frame = frame.copy()
    if frame[required].isna().any().any():
        raise ValueError("Prediction fields cannot be null")
    for col in ["record_id", "source_id", "clip_id"]:
        frame[col] = frame[col].astype(str)
        if (frame[col].str.strip() == "").any():
            raise ValueError(f"Empty {col}")
    for col in ["frame_index", "person_a", "person_b"]:
        values = pd.to_numeric(frame[col], errors="raise")
        if not np.isfinite(values).all() or (values % 1 != 0).any():
            raise ValueError(f"{col} must contain finite integers")
        frame[col] = values.astype(int)
    if (frame.frame_index < 0).any():
        raise ValueError("Frame indices must be nonnegative")
    frame["probability"] = pd.to_numeric(frame.probability, errors="raise")
    if not np.isfinite(frame.probability).all() or not frame.probability.between(0, 1).all():
        raise ValueError("Probabilities must be finite and between zero and one")
    frame = frame.loc[
        (frame.person_a >= 0) & (frame.person_b >= 0) & (frame.person_a != frame.person_b)
    ].copy()
    frame[["person_a", "person_b"]] = np.sort(frame[["person_a", "person_b"]], axis=1)
    if frame.record_id.duplicated().any() or frame.duplicated(KEY).any():
        raise ValueError("Duplicate record or unordered pair-frame; reconcile upstream explicitly")
    if frame.empty:
        raise ValueError("No eligible pair-frame records")
    return frame.sort_values(KEY).reset_index(drop=True)


@dataclass(frozen=True)
class Block:
    block_id: str
    source_id: str
    record_ids: tuple[str, ...]
    q_sum: float
    features: tuple[float, ...]

    @property
    def cost(self) -> int:
        return len(self.record_ids)


def make_blocks(frame: pd.DataFrame, length: int = 5) -> list[Block]:
    if length < 1:
        raise ValueError("Block length must be positive")
    frame = normalize_predictions(frame)
    blocks = []
    for _, group in frame.groupby(["source_id", "clip_id", "person_a", "person_b"], sort=True):
        runs = group.frame_index.diff().ne(1).cumsum()
        for _, run in group.groupby(runs):
            for start in range(0, len(run), length):
                chunk = run.iloc[start : start + length]
                q = chunk.probability.to_numpy(float)
                safe = np.clip(q, 1e-12, 1 - 1e-12)
                entropy = float(np.mean(-safe * np.log(safe) - (1 - safe) * np.log(1 - safe)))
                features = (
                    float(q.mean()),
                    float(q.std()),
                    float(q.sum()),
                    entropy,
                    float(np.abs(np.diff(q)).mean()) if len(q) > 1 else 0.0,
                    float(len(q)),
                )
                blocks.append(
                    Block(
                        f"block-{len(blocks):08d}",
                        str(chunk.source_id.iloc[0]),
                        tuple(chunk.record_id),
                        float(q.sum()),
                        features,
                    )
                )
    return blocks


def feature_matrix(blocks: list[Block]) -> np.ndarray:
    return np.asarray([b.features for b in blocks], dtype=float)


def assert_disjoint_sources(splits: dict[str, list[Block]]) -> None:
    seen: set[str] = set()
    for name, blocks in splits.items():
        sources = {b.source_id for b in blocks}
        if seen & sources:
            raise ValueError(f"Source leakage in {name}: {sorted(seen & sources)}")
        seen |= sources
