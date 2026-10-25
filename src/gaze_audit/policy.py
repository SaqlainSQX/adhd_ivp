"""Development-only risk learning and fixed, positive-probability query plans."""

from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold

from .data import Block, feature_matrix


@dataclass
class RiskPolicy:
    model: RandomForestRegressor
    cut_points: np.ndarray
    residual_sd: np.ndarray

    def strata(self, blocks: list[Block]) -> np.ndarray:
        return np.searchsorted(self.cut_points, self.model.predict(feature_matrix(blocks)))


def fit_policy(blocks: list[Block], labels: dict[str, int], seed: int) -> RiskPolicy:
    x = feature_matrix(blocks)
    residual = np.array([labels[b.block_id] - b.q_sum for b in blocks])
    groups = np.array([b.source_id for b in blocks])
    count = len(np.unique(groups))
    if count < 2:
        raise ValueError("Risk learning requires at least two independent training sources")

    def model() -> RandomForestRegressor:
        return RandomForestRegressor(
            n_estimators=64,
            max_depth=4,
            min_samples_leaf=4,
            random_state=seed,
            n_jobs=1,
        )

    held_out_scores = np.zeros(len(blocks))
    for train, held in GroupKFold(n_splits=min(5, count)).split(x, groups=groups):
        fold = model().fit(x[train], residual[train] ** 2)
        held_out_scores[held] = fold.predict(x[held])
    cuts = np.unique(np.quantile(held_out_scores, [0.25, 0.5, 0.75]))
    strata = np.searchsorted(cuts, held_out_scores)
    global_sd = max(float(np.std(residual, ddof=1)), 1e-6)
    sd = []
    for h in range(len(cuts) + 1):
        values = residual[strata == h]
        sd.append(max(float(np.std(values, ddof=1)), 1e-6) if len(values) > 1 else global_sd)
    return RiskPolicy(model().fit(x, residual**2), cuts, np.asarray(sd))


@dataclass(frozen=True)
class StratumPlan:
    stratum: int
    population: tuple[int, ...]
    selected: tuple[int, ...]
    expected_blocks: float


def _continuous_counts(
    weights: np.ndarray, sizes: np.ndarray, costs: np.ndarray, budget: float
) -> np.ndarray:
    lower = np.minimum(sizes, 2)
    if budget < float(lower @ costs) - 1e-8:
        raise ValueError("Budget cannot support two blocks per non-census stratum")
    if budget >= sizes @ costs:
        return sizes.astype(float)
    lo, hi = 0.0, 1.0
    while np.clip(hi * weights, lower, sizes) @ costs < budget:
        hi *= 2
    for _ in range(80):
        mid = (lo + hi) / 2
        if np.clip(mid * weights, lower, sizes) @ costs < budget:
            lo = mid
        else:
            hi = mid
    return np.clip((lo + hi) / 2 * weights, lower, sizes)


def draw_plan(
    blocks: list[Block], strata: np.ndarray, sd: np.ndarray, budget: float, mix: float, seed: int
) -> list[StratumPlan]:
    if not 0 <= mix <= 1 or not np.isfinite(budget) or budget <= 0:
        raise ValueError("Require a positive finite budget and mix in [0, 1]")
    if budget > sum(b.cost for b in blocks):
        raise ValueError("Budget exceeds the label population")
    if len(strata) != len(blocks) or not len(blocks):
        raise ValueError("Strata must match a nonempty block population")
    present = np.unique(strata)
    populations = [np.flatnonzero(strata == h) for h in present]
    sizes = np.array([len(p) for p in populations])
    costs = np.array([np.mean([blocks[i].cost for i in p]) for p in populations])
    uniform = _continuous_counts(sizes.astype(float), sizes, costs, budget)
    active_weights = sizes * np.maximum(sd[present], 1e-6) / np.sqrt(costs)
    active = _continuous_counts(active_weights, sizes, costs, budget)
    expected = (1 - mix) * uniform + mix * active
    rng = np.random.default_rng(seed)
    plan = []
    for h, pop, target in zip(present, populations, expected, strict=True):
        count = min(len(pop), int(np.floor(target)) + int(rng.random() < target % 1))
        selected = tuple(int(i) for i in rng.choice(pop, size=count, replace=False))
        plan.append(StratumPlan(int(h), tuple(int(i) for i in pop), selected, float(target)))
    return plan
