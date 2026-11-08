"""Finite-population observation-flip moments and fixed-design audit calculations."""

import itertools

import numpy as np


def analytical_moments(y, phi, populations, counts, eta):
    y, phi = np.asarray(y, float), np.asarray(phi, float)
    if not 0 <= eta < 0.5:
        raise ValueError("Use a registered binary flip probability below one half")
    variance = 0.0
    for pop, count in zip(populations, counts, strict=True):
        size = len(pop)
        weight = size / len(y)
        if count < size:
            variance += (
                weight**2
                * (1 - count / size)
                / count
                * np.var((1 - 2 * eta) * y[pop] - phi[pop], ddof=1)
            )
        variance += eta * (1 - eta) * weight**2 / count
    bias = eta * (1 - 2 * float(y.mean()))
    return {"bias": bias, "variance": float(variance), "MSE": float(variance + bias**2)}


def fixed_estimates(y, phi, selections, populations, counts, uniforms, eta):
    selected_y = np.asarray(y)[selections]
    flips = uniforms[np.arange(len(selections))[:, None], selections] < eta
    observed = np.where(flips, 1 - selected_y, selected_y)
    point, variance = np.full(len(selections), np.mean(phi)), np.zeros(len(selections))
    boundaries = np.r_[0, np.cumsum(counts)]
    successes = []
    for h, (pop, count) in enumerate(zip(populations, counts, strict=True)):
        block = slice(boundaries[h], boundaries[h + 1])
        residual = observed[:, block] - phi[selections[:, block]]
        size = len(pop)
        point += size / len(y) * residual.mean(axis=1)
        if count < size:
            variance += (
                (size / len(y)) ** 2 * (1 - count / size) / count * residual.var(axis=1, ddof=1)
            )
        successes.append(observed[:, block].sum(axis=1).astype(int))
    return point, variance, np.stack(successes, axis=1), flips.sum(axis=1)


def exhaustive_toy_check(settings):
    y, q = np.asarray(settings["y"], float), np.asarray(settings["q"], float)
    checks, maximum = 0, 0.0
    for design in settings["designs"]:
        pops = [np.asarray(p) for p in design["populations"]]
        counts = design["counts"]
        choices = list(
            itertools.product(
                *[list(itertools.combinations(p, n)) for p, n in zip(pops, counts, strict=True)]
            )
        )
        for eta in settings["etas"]:
            for weight in settings["weights"]:
                phi = q * weight
                estimates, probabilities = [], []
                for bit_tuple in itertools.product((0, 1), repeat=len(y)):
                    bits = np.array(bit_tuple)
                    probability = eta ** int(bits.sum()) * (1 - eta) ** int(len(y) - bits.sum())
                    noisy = np.where(bits, 1 - y, y)
                    for choice in choices:
                        point = phi.mean() + sum(
                            len(p) / len(y) * np.mean(noisy[list(s)] - phi[list(s)])
                            for p, s in zip(pops, choice, strict=True)
                        )
                        estimates.append(point)
                        probabilities.append(probability / len(choices))
                estimates, probabilities = np.asarray(estimates), np.asarray(probabilities)
                mean = probabilities @ estimates
                variance = probabilities @ ((estimates - mean) ** 2)
                expected = analytical_moments(y, phi, pops, counts, eta)
                error = max(
                    abs(mean - y.mean() - expected["bias"]), abs(variance - expected["variance"])
                )
                maximum = max(maximum, float(error))
                if error > 1e-12:
                    raise ArithmeticError("Exhaustive synthetic bias/variance identity failed")
                checks += 1
    return {
        "complete": True,
        "moment_cases": checks,
        "max_absolute_difference": maximum,
        "census_observation_noise_included": True,
    }
