from itertools import product

import numpy as np
import pytest
from scipy.stats import hypergeom

from gaze_audit.exact_intervals import stratified_binary_interval
from gaze_audit.weighted_intervals import public_error_allocation, weighted_binary_totals


def test_public_weights_ignore_census_and_equal_reproduces_original():
    for recipe in ["equal", "inverse-fraction", "inverse-sqrt-count"]:
        errors = public_error_allocation([10, 30, 4], [5, 6, 4], recipe)
        assert errors[2] == 0 and np.isclose(errors.sum(), 0.05)
    low, high = weighted_binary_totals([1, 2, 4], [5, 6, 4], [10, 30, 4], "equal")
    original = stratified_binary_interval([1, 2, 4], [5, 6, 4], [10, 30, 4])
    assert (low, high) == tuple(round(x * 44) for x in original)
    assert weighted_binary_totals([2, 3], [4, 5], [4, 5], "inverse-fraction") == (5, 5)
    with pytest.raises(ValueError):
        public_error_allocation([3], [0], "equal")


@pytest.mark.parametrize("alpha", [0.05, 0.2, 0.5])
def test_every_small_population_total_has_conservative_coverage(alpha):
    sizes, counts = [6, 7], [3, 3]
    for recipe in ["equal", "inverse-fraction", "inverse-sqrt-count"]:
        endpoints = {
            k: weighted_binary_totals(k, counts, sizes, recipe, alpha)
            for k in product(range(4), repeat=2)
        }
        for totals in product(range(7), range(8)):
            coverage = 0.0
            for success, (low, high) in endpoints.items():
                prob = hypergeom.pmf(success[0], 6, totals[0], 3) * hypergeom.pmf(
                    success[1], 7, totals[1], 3
                )
                if low <= sum(totals) <= high:
                    coverage += prob
            assert coverage >= 1 - alpha - 1e-12
