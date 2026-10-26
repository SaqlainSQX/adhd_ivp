"""Exact-cost pair-frame sampling and finite-population residual estimation."""

from dataclasses import asdict, dataclass
from statistics import NormalDist

import numpy as np


def integer_budget(fraction: float, population_size: int) -> int:
    if not 0 < fraction <= 1 or population_size < 1:
        raise ValueError("Require fraction in (0,1] and a nonempty population")
    return int(np.floor(fraction * population_size + 0.5))


def allocate_counts(sizes, sd, budget: int, mix: float, minimum: int = 20) -> np.ndarray:
    sizes, sd = np.asarray(sizes), np.asarray(sd, dtype=float)
    if (
        sizes.ndim != 1
        or len(sizes) == 0
        or np.any(sizes <= 0)
        or np.any(sizes % 1)
        or sd.shape != sizes.shape
        or not np.isfinite(sd).all()
        or np.any(sd < 0)
        or not 0 <= mix <= 1
        or minimum < 2
        or not isinstance(budget, (int, np.integer))
    ):
        raise ValueError("Invalid allocation inputs")
    sizes = sizes.astype(int)
    lower = np.minimum(sizes, minimum)
    if not lower.sum() <= budget <= sizes.sum():
        raise ValueError("Budget infeasible for fixed strata and declared minima")

    def continuous(weights):
        if budget == sizes.sum():
            return sizes.astype(float)
        lo, hi = 0.0, float(budget / np.min(weights) + 1)
        for _ in range(80):
            mid = (lo + hi) / 2
            if np.clip(mid * weights, lower, sizes).sum() < budget:
                lo = mid
            else:
                hi = mid
        return np.clip((lo + hi) / 2 * weights, lower, sizes)

    uniform = continuous(sizes.astype(float))
    neyman = continuous(sizes * np.maximum(sd, 1e-6))
    target = (1 - mix) * uniform + mix * neyman
    counts = np.floor(target).astype(int)
    remaining = int(budget - counts.sum())
    # Stable order makes tied remainders deterministic in the declared stratum order.
    order = np.argsort(-(target - counts), kind="stable")
    for h in order:
        if remaining and counts[h] < sizes[h]:
            counts[h] += 1
            remaining -= 1
    if remaining or counts.sum() != budget or np.any(counts < lower) or np.any(counts > sizes):
        raise ArithmeticError("Exact bounded allocation failed")
    return counts


@dataclass(frozen=True)
class FrameStratum:
    population: tuple[int, ...]
    selected: tuple[int, ...]


def draw_frame_plan(strata, counts, rng: np.random.Generator) -> tuple[FrameStratum, ...]:
    strata, counts = np.asarray(strata), np.asarray(counts)
    present = np.unique(strata)
    if strata.ndim != 1 or len(strata) == 0 or counts.shape != present.shape:
        raise ValueError("Strata and counts disagree")
    result = []
    for h, count in zip(present, counts, strict=True):
        population = np.flatnonzero(strata == h)
        if count % 1 or not 1 <= count <= len(population):
            raise ValueError("Invalid stratum count")
        selected = rng.choice(population, size=int(count), replace=False)
        result.append(FrameStratum(tuple(map(int, population)), tuple(map(int, selected))))
    return tuple(result)


class FrameOracle:
    """Offline access boundary, not a security sandbox. Samplers never receive this object."""

    def __init__(self, labels: dict[str, int], expected_ids: tuple[str, ...]):
        if len(set(expected_ids)) != len(expected_ids) or set(labels) != set(expected_ids):
            raise ValueError("Oracle IDs must match the unique population exactly")
        if any(value not in (0, 1) for value in labels.values()):
            raise ValueError("Oracle references must be binary")
        self._labels = labels.copy()
        self.total_queries = 0

    def query(self, record_ids: tuple[str, ...]) -> dict[str, int]:
        if len(set(record_ids)) != len(record_ids) or not set(record_ids) <= self._labels.keys():
            raise ValueError("Queries must be unique and available")
        self.total_queries += len(record_ids)
        return {key: self._labels[key] for key in record_ids}


@dataclass(frozen=True)
class FrameEstimate:
    prevalence: float
    variance: float
    normal_low: float
    normal_high: float
    bounded_low: float
    bounded_high: float
    bounded_empty: bool
    labels_revealed: int
    positives_revealed: int

    def as_dict(self):
        return asdict(self)


def estimate_frames(
    ids: tuple[str, ...],
    q,
    plan: tuple[FrameStratum, ...],
    queried: dict[str, int],
    alpha: float = 0.05,
) -> FrameEstimate:
    q = np.asarray(q, dtype=float)
    size = len(ids)
    if (
        not size
        or len(set(ids)) != size
        or q.shape != (size,)
        or not np.isfinite(q).all()
        or np.any((q < 0) | (q > 1))
        or not 0 < alpha < 1
    ):
        raise ValueError("Invalid public population, frozen predictions or confidence level")
    population = [i for h in plan for i in h.population]
    if sorted(population) != list(range(size)):
        raise ValueError("Plan must partition the population exactly")
    selected = [i for h in plan for i in h.selected]
    if len(set(selected)) != len(selected) or any(i < 0 or i >= size for i in selected):
        raise ValueError("Duplicate or invalid selections")
    if set(queried) != {ids[i] for i in selected} or any(y not in (0, 1) for y in queried.values()):
        raise ValueError("Estimator requires exactly the selected binary labels")
    total, variance, radius = float(q.sum()), 0.0, 0.0
    for h in plan:
        nh, count = len(h.population), len(h.selected)
        if count < 1 or not set(h.selected) <= set(h.population):
            raise ValueError("Each stratum requires positive inclusion and valid selections")
        residuals = np.array([queried[ids[i]] - q[i] for i in h.selected])
        total += nh / count * float(residuals.sum())
        if count != nh:
            if count < 2:
                raise ValueError("Non-census strata need at least two queries")
            variance += nh**2 * (1 - count / nh) * float(np.var(residuals, ddof=1)) / count
            public_q = q[list(h.population)]
            residual_range = float((1 - public_q).max() + public_q.max())
            radius += (
                nh / size * residual_range * np.sqrt(np.log(2 * len(plan) / alpha) / (2 * count))
            )
    point, variance = total / size, variance / size**2
    half = NormalDist().inv_cdf(1 - alpha / 2) * np.sqrt(variance)
    low, high = max(0.0, point - radius), min(1.0, point + radius)
    return FrameEstimate(
        float(point),
        float(variance),
        float(point - half),
        float(point + half),
        float(low),
        float(high),
        bool(low > high),
        len(selected),
        sum(queried.values()),
    )


def hypergeometric_interval(
    successes: int, sample_size: int, population_size: int, alpha: float = 0.05
) -> tuple[float, float]:
    """Equal-tailed exact inversion for binary SRS without replacement, integer totals."""
    from scipy.stats import hypergeom

    if not 0 <= successes <= sample_size <= population_size or sample_size < 1 or not 0 < alpha < 1:
        raise ValueError("Invalid hypergeometric inputs")
    support_low, support_high = successes, population_size - sample_size + successes
    lo, hi = support_low, support_high
    while lo < hi:
        middle = (lo + hi) // 2
        if hypergeom.sf(successes - 1, population_size, middle, sample_size) >= alpha / 2:
            hi = middle
        else:
            lo = middle + 1
    lower = lo
    lo, hi = support_low, support_high
    while lo < hi:
        middle = (lo + hi + 1) // 2
        if hypergeom.cdf(successes, population_size, middle, sample_size) >= alpha / 2:
            lo = middle
        else:
            hi = middle - 1
    return lower / population_size, lo / population_size
