from itertools import combinations, product

import numpy as np

from gaze_audit.block_guidance import block_estimate, exact_variance, expected_design


def test_stratified_random_counts_preserve_expected_cost_and_design_moments():
    costs = np.array([1, 1, 1, 2, 1, 3, 2])
    q = np.array([0.1, 0.2, 0.4, 0.4, 0.2, 0.9, 0.4])
    y = np.array([0, 1, 0, 1, 0, 2, 1])
    groups = np.array([0, 0, 0, 1, 1, 1, 1])
    pop, target, means = expected_design(groups, np.array([0.2, 0.7]), costs, 8.1, 0.5)
    assert np.isclose(target @ means, 8.1, atol=1e-12)
    lotteries = []
    for t in target:
        lo = int(np.floor(t))
        frac = t - lo
        lotteries.append([(lo, 1 - frac), (lo + 1, frac)] if frac > 0 else [(lo, 1.0)])
    mean, second, variance, expected_cost, probability = 0.0, 0.0, 0.0, 0.0, 0.0
    for outcome in product(*lotteries):
        counts = [v[0] for v in outcome]
        mass = float(np.prod([v[1] for v in outcome]))
        choices = [list(combinations(p, n)) for p, n in zip(pop, counts, strict=True)]
        for sample in product(*choices):
            selected = np.array(sum(sample, ()))
            p = mass / np.prod([len(c) for c in choices])
            e = block_estimate(q, y, costs, pop, selected, counts)
            probability += p
            mean += p * e["prevalence"]
            second += p * e["prevalence"] ** 2
            variance += p * e["variance"]
            expected_cost += p * e["labels"]
    assert np.isclose(probability, 1, atol=1e-12)
    assert np.isclose(mean, y.sum() / costs.sum(), atol=1e-12)
    assert np.isclose(expected_cost, 8.1, atol=1e-12)
    assert np.isclose(second - mean**2, variance, atol=1e-12)
    assert np.isclose(variance, exact_variance(pop, target, y - q, costs.sum()), atol=1e-12)


def test_census_has_no_variance_or_bounded_radius():
    q = np.array([0.1, 0.5, 0.2])
    y = np.array([0, 1, 1])
    costs = np.array([1, 2, 1])
    e = block_estimate(q, y, costs, [np.array([0, 1]), np.array([2])], np.arange(3), [2, 1])
    assert e["variance"] == 0 and np.isclose(e["prevalence"], 0.5)
    assert e["bounded_low"] == e["bounded_high"] == e["prevalence"]
