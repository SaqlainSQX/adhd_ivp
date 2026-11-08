from itertools import combinations, product

import numpy as np

from gaze_audit.source_stress import domain_draws


def test_known_size_domains_unbiased_variance_and_complement_identity():
    q = np.array([0.05, 0.8, 0.2, 0.9, 0.3, 0.7]) * 0.5
    y = np.array([0, 1, 1, 0, 0, 1])
    pop = [(0, 1, 2), (3, 4, 5)]
    counts = np.array([2, 2])
    samples = np.array([sum(s, ()) for s in product(*(list(combinations(p, 2)) for p in pop))])
    mask = np.array([1, 0, 0, 1, 1, 0], bool)
    p, v, exact, _ = domain_draws(q, y, mask, pop, counts, samples)
    outside, _, _, _ = domain_draws(q, y, ~mask, pop, counts, samples)
    full, _, _, _ = domain_draws(q, y, np.ones(6, bool), pop, counts, samples)
    assert np.isclose(p.mean(), y[mask].mean(), atol=1e-14)
    assert np.isclose(p.var(), v.mean(), atol=1e-14)
    assert np.isclose(p.var(), exact, atol=1e-14)
    assert np.allclose(p * mask.sum() + outside * (~mask).sum(), full * len(y), atol=1e-14)
