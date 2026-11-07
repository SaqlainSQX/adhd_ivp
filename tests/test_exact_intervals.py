from itertools import combinations, product

import numpy as np
import pytest

from gaze_audit.exact_intervals import stratified_binary_interval


def test_small_two_stratum_population_has_at_least_nominal_design_coverage():
    sizes, counts = [4, 5], [2, 3]
    for positives in product(range(5), range(6)):
        truth = sum(positives) / sum(sizes)
        covered, total = 0, 0
        for a, b in product(combinations(range(4), 2), combinations(range(5), 3)):
            successes = [sum(i < positives[0] for i in a), sum(i < positives[1] for i in b)]
            lo, hi = stratified_binary_interval(successes, counts, sizes)
            covered += lo - 1e-12 <= truth <= hi + 1e-12
            total += 1
        assert covered / total >= 0.95 - 1e-12


def test_census_is_exact_and_zero_success_sample_retains_positive_upper_bound():
    assert stratified_binary_interval([2, 1], [4, 5], [4, 5]) == (1 / 3, 1 / 3)
    low, high = stratified_binary_interval([0, 1], [2, 5], [40, 5])
    assert low == pytest.approx(1 / 45) and high > low


def test_invalid_binary_counts_and_noninteger_sizes_are_rejected():
    for k, n, size in [([3], [2], [4]), ([1], [0], [4]), ([0], [2], [1.5])]:
        with pytest.raises(ValueError, match="integer"):
            stratified_binary_interval(k, n, size)
    lo, hi = stratified_binary_interval(np.array([0, 1]), np.array([2, 3]), np.array([4, 5]))
    assert 0 <= lo <= hi <= 1
