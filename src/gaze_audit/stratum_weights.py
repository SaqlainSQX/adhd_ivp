"""Training-only fixed control-variate coefficients for the U experiment."""

import itertools

import numpy as np


def fit_coefficient(q, y):
    q, y = np.asarray(q, float), np.asarray(y, float)
    cq, cy = q - q.mean(), y - y.mean()
    denominator, numerator = float(cq @ cq), float(cq @ cy)
    weight = (
        0.0 if len(q) < 2 or denominator <= 1e-12 else float(np.clip(numerator / denominator, 0, 1))
    )
    return {
        "count": len(q),
        "q_centered_ss": denominator,
        "qy_centered_sum": numerator,
        "coefficient": weight,
    }


def audit(y, phi, populations, counts, selected):
    point, variance = np.full(len(selected), phi.mean()), np.zeros(len(selected))
    exact, offset = 0.0, 0
    for pop, n in zip(populations, counts, strict=True):
        sample = selected[:, offset : offset + n]
        residual = y[sample] - phi[sample]
        w = len(pop) / len(y)
        point += w * residual.mean(axis=1)
        if n < len(pop):
            factor = w * w * (1 - n / len(pop)) / n
            variance += factor * residual.var(axis=1, ddof=1)
            exact += factor * np.var(y[pop] - phi[pop], ddof=1)
        offset += n
    return point, variance, float(exact)


def toy_check():
    y = np.array([0, 0, 1, 0, 1, 1.0])
    q = np.array([0.05, 0.2, 0.6, 0.1, 0.7, 0.9])
    pops = [np.arange(3), np.arange(3, 6)]
    phi = q * np.array([0.2] * 3 + [0.8] * 3)
    maximum = 0.0
    for counts in [[2, 2], [3, 3]]:
        samples = np.array(
            [
                a + b
                for a, b in itertools.product(
                    itertools.combinations(pops[0], counts[0]),
                    itertools.combinations(pops[1], counts[1]),
                )
            ]
        )
        points, variances, exact = audit(y, phi, pops, counts, samples)
        error = max(
            abs(points.mean() - y.mean()), abs(points.var() - exact), abs(variances.mean() - exact)
        )
        maximum = max(maximum, float(error))
        if error > 1e-12:
            raise ArithmeticError("U piecewise-phi enumeration failed")
    for tq, ty, expected in [
        ([0, 1], [0, 1], 1),
        ([0, 1], [1, 0], 0),
        ([0.5, 0.5], [0, 1], 0),
        ([0.5], [1], 0),
    ]:
        if fit_coefficient(tq, ty)["coefficient"] != expected:
            raise ArithmeticError("U coefficient boundary failed")
    return {
        "complete": True,
        "exhaustive_designs": 2,
        "coefficient_boundary_cases": 4,
        "max_moment_difference": maximum,
    }


def bootstrap(top_error, bottom_error, code, budget_index):
    rng = np.random.default_rng(np.random.SeedSequence([820000 + code * 100 + budget_index, 1, 93]))
    indices = rng.integers(len(top_error), size=(2000, len(top_error)))
    a, b = np.asarray(top_error) ** 2, np.asarray(bottom_error) ** 2
    ratios = np.sqrt(a[indices].mean(axis=1) / b[indices].mean(axis=1))
    return {
        "rmse_ratio": float(np.sqrt(a.mean() / b.mean())),
        "paired_bootstrap_95pct": np.quantile(ratios, [0.025, 0.975]).tolist(),
        "resamples": 2000,
        "seed_sequence": [820000 + code * 100 + budget_index, 1, 93],
    }
