"""Registered class-conditional observation errors on fixed audit queries."""

import itertools

import numpy as np


def moments(y, phi, populations, counts, a, b):
    y, phi = np.asarray(y, float), np.asarray(phi, float)
    if not (0 <= a < 0.5 and 0 <= b < 0.5):
        raise ValueError("Invalid registered class-conditional rates")
    mean = a + (1 - a - b) * y
    noise_variance = np.where(y == 0, a * (1 - a), b * (1 - b))
    variance = 0.0
    for pop, n in zip(populations, counts, strict=True):
        size = len(pop)
        sampling = 0 if n == size else (1 - n / size) * np.var(mean[pop] - phi[pop], ddof=1)
        variance += (size / len(y)) ** 2 / n * (sampling + noise_variance[pop].mean())
    bias = a * (1 - y.mean()) - b * y.mean()
    return {"bias": float(bias), "variance": float(variance), "MSE": float(variance + bias**2)}


def estimates(y, phi, design, uniforms, a, b):
    selected = design["selections"]
    clean = y[selected]
    thresholds = np.where(clean == 0, a, b)
    flips = uniforms[np.arange(len(selected))[:, None], selected] < thresholds
    noisy = np.where(flips, 1 - clean, clean)
    point = np.full(len(selected), phi.mean())
    variance = np.zeros(len(selected))
    successes, start = [], 0
    for pop, n in zip(design["populations"], design["counts"], strict=True):
        block = slice(start, start + n)
        residual = noisy[:, block] - phi[selected[:, block]]
        w = len(pop) / len(y)
        point += w * residual.mean(axis=1)
        if n < len(pop):
            variance += w**2 * (1 - n / len(pop)) / n * residual.var(axis=1, ddof=1)
        successes.append(noisy[:, block].sum(axis=1).astype(int))
        start += n
    return point, variance, np.stack(successes, axis=1), flips.sum(axis=1)


def exhaustive_check(toy, cases):
    y, q = np.asarray(toy["y"], float), np.asarray(toy["q"], float)
    maximum, checked = 0.0, 0
    for design in toy["designs"]:
        populations = [np.array(p) for p in design["populations"]]
        counts = design["counts"]
        samples = list(
            itertools.product(
                *[
                    list(itertools.combinations(p, n))
                    for p, n in zip(populations, counts, strict=True)
                ]
            )
        )
        for case in cases:
            a, b = case["a"], case["b"]
            rate = np.where(y == 0, a, b)
            for weight in toy["weights"]:
                phi = weight * q
                points, probabilities = [], []
                for bits in itertools.product((0, 1), repeat=len(y)):
                    bits = np.array(bits)
                    probability = np.prod(np.where(bits, rate, 1 - rate))
                    noisy = np.where(bits, 1 - y, y)
                    for sample in samples:
                        point = phi.mean() + sum(
                            len(p) / len(y) * np.mean(noisy[list(s)] - phi[list(s)])
                            for p, s in zip(populations, sample, strict=True)
                        )
                        points.append(point)
                        probabilities.append(probability / len(samples))
                points, probabilities = np.asarray(points), np.asarray(probabilities)
                mean = probabilities @ points
                variance = probabilities @ ((points - mean) ** 2)
                formula = moments(y, phi, populations, counts, a, b)
                error = max(
                    abs(mean - y.mean() - formula["bias"]), abs(variance - formula["variance"])
                )
                if error > 1e-12:
                    raise ArithmeticError("Directional toy moment identity failed")
                maximum = max(maximum, float(error))
                checked += 1
    return {
        "complete": True,
        "moment_cases": checked,
        "max_absolute_difference": maximum,
        "census_noise_included": True,
    }
