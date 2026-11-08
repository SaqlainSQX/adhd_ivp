"""Publicly weighted Bonferroni intervals for fixed binary strata."""

import numpy as np

from .exact_intervals import checked_binary_interval


def public_error_allocation(sizes, counts, recipe, alpha=0.05):
    sizes, counts = np.asarray(sizes), np.asarray(counts)
    if (
        sizes.ndim != 1
        or not len(sizes)
        or sizes.shape != counts.shape
        or not 0 < alpha < 1
        or not all(np.isfinite(v).all() and np.equal(v, np.floor(v)).all() for v in [sizes, counts])
        or (counts < 1).any()
        or (sizes < counts).any()
    ):
        raise ValueError("Require valid positive integer population/sample sizes")
    if recipe not in ["equal", "inverse-fraction", "inverse-sqrt-count"]:
        raise ValueError("Unregistered public weighting recipe")
    active = counts < sizes
    raw = np.ones(len(sizes))
    if recipe == "inverse-fraction":
        raw = sizes / counts
    elif recipe == "inverse-sqrt-count":
        raw = sizes / np.sqrt(counts)
    errors = np.zeros(len(sizes))
    if active.any():
        errors[active] = alpha * raw[active] / raw[active].sum()
    return errors


def weighted_binary_totals(successes, counts, sizes, recipe, alpha=0.05):
    errors = public_error_allocation(sizes, counts, recipe, alpha)
    successes, counts, sizes = [np.asarray(v) for v in [successes, counts, sizes]]
    if (
        successes.shape != sizes.shape
        or not np.isfinite(successes).all()
        or not np.equal(successes, np.floor(successes)).all()
        or (successes < 0).any()
        or (successes > counts).any()
    ):
        raise ValueError("Require integer binary successes within queried counts")
    lower, upper = 0, 0
    for k, n, size, error in zip(successes, counts, sizes, errors, strict=True):
        if n == size:
            lo = hi = int(k)
        else:
            a, b = checked_binary_interval(int(k), int(n), int(size), float(error))
            lo, hi = round(a * size), round(b * size)
        lower += lo
        upper += hi
    return int(lower), int(upper)
