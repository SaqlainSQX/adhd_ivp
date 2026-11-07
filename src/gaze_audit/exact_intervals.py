"""Established hypergeometric stratum intervals with simultaneous Bonferroni coverage."""

from functools import lru_cache

import numpy as np
from scipy.stats import hypergeom

from .frames import hypergeometric_interval


@lru_cache(maxsize=10000)
def checked_binary_interval(successes, count, size, alpha):
    low, high = hypergeometric_interval(successes, count, size, alpha)
    lower, upper = int(round(low * size)), int(round(high * size))
    support_low, support_high = successes, size - count + successes
    tolerance = 1e-11
    # Independently verify acceptance and neighboring integer boundaries using
    # complementary CDF/SF evaluations, rather than trusting the original search.
    def lower_tail(total):
        return 1 - hypergeom.cdf(successes - 1, size, total, count)

    def upper_tail(total):
        return 1 - hypergeom.sf(successes, size, total, count)
    if lower_tail(lower) < alpha / 2 - tolerance or upper_tail(upper) < alpha / 2 - tolerance:
        raise ValueError("Exact endpoint does not satisfy its tail acceptance condition")
    if lower > support_low and lower_tail(lower - 1) >= alpha / 2 + tolerance:
        raise ValueError("Exact lower endpoint is not the minimal accepted integer")
    if upper < support_high and upper_tail(upper + 1) >= alpha / 2 + tolerance:
        raise ValueError("Exact upper endpoint is not the maximal accepted integer")
    return low, high


def stratified_binary_interval(successes, counts, sizes, alpha=0.05):
    successes, counts, sizes = [np.asarray(v) for v in [successes, counts, sizes]]
    if (
        sizes.ndim != 1
        or len(sizes) == 0
        or successes.shape != sizes.shape
        or counts.shape != sizes.shape
        or not 0 < alpha < 1
        or not all(
            np.isfinite(v).all() and np.equal(v, np.floor(v)).all()
            for v in [successes, counts, sizes]
        )
        or (sizes < 1).any()
        or (counts < 1).any()
        or (counts > sizes).any()
        or (successes < 0).any()
        or (successes > counts).any()
    ):
        raise ValueError("Require valid integer stratum sizes, queried counts and binary successes")
    noncensus = int(np.sum(counts < sizes))
    lower_total, upper_total = 0, 0
    for k, n, size in zip(successes, counts, sizes, strict=True):
        if n == size:
            lo = hi = k / size
        else:
            lo, hi = checked_binary_interval(int(k), int(n), int(size), alpha / noncensus)
        # Add feasible integer totals before division to preserve census boundaries.
        lower_total += int(round(lo * size))
        upper_total += int(round(hi * size))
    return float(lower_total / sizes.sum()), float(upper_total / sizes.sum())
