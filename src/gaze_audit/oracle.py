"""An access boundary for offline experiments, not a security sandbox."""

import pandas as pd

from .data import Block


class LabelOracle:
    def __init__(self, labels: pd.DataFrame, expected_ids: set[str]):
        if set(labels.columns) != {"record_id", "label"}:
            raise ValueError("Labels require exactly record_id,label")
        labels = labels.copy()
        if labels.isna().any().any():
            raise ValueError("Labels cannot be null")
        labels["record_id"] = labels.record_id.astype(str)
        if labels.record_id.duplicated().any() or not labels.label.isin([0, 1]).all():
            raise ValueError("Labels must be unique binary references; exclude unknowns upstream")
        if set(labels.record_id) != expected_ids:
            raise ValueError("Prediction and label record IDs must match exactly")
        self._labels = dict(zip(labels.record_id, labels.label.astype(int), strict=True))
        self.log: list[dict] = []

    def query(self, blocks: list[Block], *, seed: int, purpose: str) -> dict[str, int]:
        selected_ids = [r for b in blocks for r in b.record_ids]
        if len(selected_ids) != len(set(selected_ids)):
            raise ValueError("A query cannot contain overlapping blocks")
        if not set(selected_ids) <= self._labels.keys():
            raise ValueError("Query includes unavailable labels")
        values = {}
        for block in blocks:
            values[block.block_id] = sum(self._labels[r] for r in block.record_ids)
            self.log.append(
                {
                    "block_id": block.block_id,
                    "record_ids": list(block.record_ids),
                    "cost": block.cost,
                    "seed": seed,
                    "purpose": purpose,
                }
            )
        return values


def reference_prevalence(labels: pd.DataFrame) -> float:
    """Evaluator-only truth; never passed to a sampler or test policy fitter."""
    return float(labels.label.mean())
