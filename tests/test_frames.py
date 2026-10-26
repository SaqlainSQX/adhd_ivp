import itertools

import numpy as np
import pytest
from scipy.stats import hypergeom

from gaze_audit.frames import (
    FrameOracle,
    FrameStratum,
    allocate_counts,
    draw_frame_plan,
    estimate_frames,
    hypergeometric_interval,
    integer_budget,
)


@pytest.mark.parametrize("groups", [((0, 1, 2, 3, 4, 5),), ((0, 1, 2), (3, 4, 5))])
def test_exhaustive_unbiased_point_and_variance(groups):
    labels = np.array([0, 1, 0, 0, 0, 1])
    q = np.array([0.01, 0.7, 0.8, 0.03, 0.4, 0.2])
    ids = tuple(f"r{i}" for i in range(6))
    samples = [list(itertools.combinations(group, 2)) for group in groups]
    points, variances = [], []
    for selected in itertools.product(*samples):
        plan = tuple(
            FrameStratum(group, held) for group, held in zip(groups, selected, strict=True)
        )
        queried = {ids[i]: int(labels[i]) for held in selected for i in held}
        result = estimate_frames(ids, q, plan, queried)
        points.append(result.prevalence)
        variances.append(result.variance)
    assert np.mean(points) == pytest.approx(labels.mean(), abs=1e-14)
    assert np.mean(variances) == pytest.approx(np.var(points), abs=1e-14)


@pytest.mark.parametrize("label", [0, 1])
def test_census_and_constant_populations(label):
    ids = ("a", "b", "c")
    result = estimate_frames(
        ids, [0.01, 0.3, 0.89], (FrameStratum((0, 1, 2), (2, 0, 1)),), dict.fromkeys(ids, label)
    )
    assert result.prevalence == pytest.approx(label)
    assert result.variance == 0
    assert result.normal_high == pytest.approx(result.normal_low)
    assert result.bounded_high == pytest.approx(result.bounded_low)


def test_allocation_is_exact_capped_and_deterministic():
    for sizes in [[3, 100, 200, 400], [21, 21, 21, 21], [1, 2, 3]]:
        for budget in [sum(min(n, 20) for n in sizes), sum(sizes)]:
            for mix in [0, 0.5, 1]:
                counts = allocate_counts(sizes, [0.001, 0.1, 0.3, 1][: len(sizes)], budget, mix)
                assert counts.sum() == budget
                assert np.all(counts <= sizes)
                assert np.all(counts >= np.minimum(sizes, 20))
    np.testing.assert_array_equal(allocate_counts([100, 100, 100], [1, 1, 1], 62, 0), [21, 21, 20])
    with pytest.raises(ValueError, match="infeasible"):
        allocate_counts([100, 100], [1, 1], 39, 0)
    assert [integer_budget(x, 38847) for x in [0.05, 0.1, 0.2, 0.4]] == [1942, 3885, 7769, 15539]


def test_draw_no_replacement_and_oracle_boundary():
    strata = np.repeat([0, 1], 10)
    counts = [3, 4]
    first = draw_frame_plan(strata, counts, np.random.default_rng(42))
    assert first == draw_frame_plan(strata, counts, np.random.default_rng(42))
    selected = [i for h in first for i in h.selected]
    assert len(selected) == len(set(selected)) == 7
    ids = tuple(map(str, range(20)))
    oracle = FrameOracle(dict.fromkeys(ids, 0), ids)
    queried = oracle.query(tuple(ids[i] for i in selected))
    estimate_frames(ids, np.zeros(20), first, queried)
    with pytest.raises(ValueError, match="exactly"):
        estimate_frames(ids, np.zeros(20), first, {})
    with pytest.raises(ValueError, match="unique"):
        oracle.query(("1", "1"))
    with pytest.raises(ValueError, match="exactly"):
        FrameOracle({"1": 0}, ids)


def test_hypergeometric_interval_exhaustive_coverage_and_census():
    for size in [5, 10]:
        for count in range(1, size + 1):
            for total in range(size + 1):
                coverage = 0.0
                for observed in range(count + 1):
                    low, high = hypergeometric_interval(observed, count, size)
                    if low - 1e-12 <= total / size <= high + 1e-12:
                        coverage += hypergeom.pmf(observed, size, total, count)
                assert coverage >= 0.95 - 1e-12
    assert hypergeometric_interval(3, 10, 10) == (0.3, 0.3)
