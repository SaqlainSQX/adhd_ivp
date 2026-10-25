"""Finite-population stratified difference estimator and normal interval."""

from dataclasses import asdict, dataclass

import numpy as np

from .data import Block
from .policy import StratumPlan


@dataclass(frozen=True)
class Estimate:
    prevalence: float
    standard_error: float
    ci_low: float
    ci_high: float
    labels_revealed: int

    def as_dict(self) -> dict:
        return asdict(self)


def estimate(
    blocks: list[Block], plan: list[StratumPlan], queried: dict[str, int], human_only: bool = False
) -> Estimate:
    populations = [i for h in plan for i in h.population]
    if sorted(populations) != list(range(len(blocks))) or not blocks:
        raise ValueError("Strata must partition the entire nonempty population")
    selected_ids = {blocks[i].block_id for h in plan for i in h.selected}
    if set(queried) != selected_ids:
        raise ValueError("Estimator must receive exactly the selected block labels")
    total = 0.0 if human_only else sum(b.q_sum for b in blocks)
    variance = 0.0
    cost = 0
    for stratum in plan:
        size, count = len(stratum.population), len(stratum.selected)
        if count < 1 or len(set(stratum.selected)) != count:
            raise ValueError("Each stratum must have unique selections and positive inclusion")
        if not set(stratum.selected) <= set(stratum.population):
            raise ValueError("Selections must belong to their stratum")
        residuals = []
        for i in stratum.selected:
            block = blocks[i]
            y = queried[block.block_id]
            if not np.isfinite(y) or y % 1 or not 0 <= y <= block.cost:
                raise ValueError("Invalid block positive count")
            residuals.append(y - (0 if human_only else block.q_sum))
            cost += block.cost
        total += size / count * sum(residuals)
        if count < size:
            if count < 2:
                raise ValueError("Non-census strata need two samples to estimate variance")
            variance += size**2 * (1 - count / size) * np.var(residuals, ddof=1) / count
    population_labels = sum(b.cost for b in blocks)
    value = total / population_labels
    se = float(np.sqrt(variance) / population_labels)
    # Keep raw endpoints and estimates: clipping would change the reported estimator.
    return Estimate(float(value), se, float(value - 1.96 * se), float(value + 1.96 * se), cost)
