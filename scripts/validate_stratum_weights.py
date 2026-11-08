"""Independent U coefficient, audit, exact-variance and bootstrap recomputation."""

import hashlib
import json
import math
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd
from run_query_noise_v2 import load_dataset
from run_stratum_weights import training_data

from gaze_audit.strengthening import replay_rng

OUT = Path("outputs/stratum-weights-u-v1")


def coefficient(q, y):
    n = len(q)
    mq, my = math.fsum(q) / n, math.fsum(y) / n
    denominator = math.fsum((x - mq) ** 2 for x in q)
    numerator = math.fsum((x - mq) * (v - my) for x, v in zip(q, y, strict=True))
    value = 0 if n < 2 or denominator <= 1e-12 else min(1, max(0, numerator / denominator))
    return value, denominator, numerator


def quantile(values, p):
    values = sorted(values)
    position = (len(values) - 1) * p
    i = math.floor(position)
    return values[i] + (position - i) * (values[min(i + 1, len(values) - 1)] - values[i])


def main():
    cfg = json.loads(Path("configs/stratum-weights-u-v1.json").read_text(encoding="utf-8"))
    fit = json.loads((OUT / "coefficient-lock.json").read_text(encoding="utf-8"))
    result = json.loads((OUT / "result.json").read_text(encoding="utf-8"))
    data = pd.read_csv(OUT / "draw-results.csv")
    for name, expected in cfg["input_sha256"].items():
        with Path(name).open("rb") as handle:
            if hashlib.file_digest(handle, "sha256").hexdigest() != expected:
                raise ValueError("U input hash differs")
    train = training_data()
    if (
        len(train) != 191956
        or train.source_id.nunique() != 40
        or not (train.split == "train").all()
    ):
        raise ValueError("U independent training contract differs")
    cuts = np.asarray(fit["cuts"])
    train_groups = np.digitize(train.f_q.to_numpy(), cuts, right=True)
    recalculated = []
    for h in [None, 0, 1, 2, 3]:
        t = train if h is None else train[train_groups == h]
        weight, ss, cross = coefficient(t.f_q.to_numpy(), t.label.to_numpy())
        saved = fit["global"] if h is None else fit["strata"][h]
        for a, b in [
            (weight, saved["coefficient"]),
            (ss, saved["q_centered_ss"]),
            (cross, saved["qy_centered_sum"]),
        ]:
            if not math.isclose(a, b, rel_tol=1e-11, abs_tol=1e-11):
                raise ArithmeticError("U independent coefficient differs")
        if saved["count"] != len(t):
            raise ValueError("U coefficient count differs")
        recalculated.append(weight)
    datasets = {name: load_dataset(name) for name in ["ChildPlay", "UCO"]}
    z = NormalDist().inv_cdf(0.975)
    max_point, max_var, checked = 0.0, 0.0, 0
    max_bootstrap, comparisons = 0.0, 0
    for d in cfg["designs"]:
        q, y, _, _, _ = datasets[d["dataset"]]
        groups = np.digitize(q, cuts, right=True)
        pops = [np.flatnonzero(groups == h) for h in range(4)]
        selected = np.load(d["query"])["selected"]
        replay_rng(selected, pops, d["counts"], 200000, d["budget_index"], d["stream"])
        if selected.shape != (1000, d["budget"]):
            raise ValueError("U independent query cost differs")
        weights = {
            "full": np.ones(len(q)),
            "half": np.full(len(q), 0.5),
            "global": np.full(len(q), recalculated[0]),
            "stratum": np.asarray(recalculated[1:])[groups],
        }
        errors = {}
        old = pd.read_csv(Path(d["base"]) / "draw-results.csv")
        field = "policy" if d["dataset"] == "ChildPlay" else "method"
        baseline = old[(old[field] == "K4") & (old.budget == d["budget"])].sort_values("draw")
        for method, weight in weights.items():
            phi = q * weight
            point, var, exact, offset = np.full(1000, phi.sum() / len(y)), np.zeros(1000), 0.0, 0
            for pop, n in zip(pops, d["counts"], strict=True):
                r = y[selected[:, offset : offset + n]] - phi[selected[:, offset : offset + n]]
                sums = r.sum(axis=1)
                w = len(pop) / len(y)
                point += w * sums / n
                if n < len(pop):
                    factor = w * w * (1 - n / len(pop)) / n
                    var += factor * ((r * r).sum(axis=1) - sums * sums / n) / (n - 1)
                    pr = y[pop] - phi[pop]
                    centered = pr - pr.mean()
                    exact += factor * float(centered @ centered) / (len(pop) - 1)
                offset += n
            saved = data[
                (data.dataset == d["dataset"])
                & (data.budget == d["budget"])
                & (data.method == method)
            ].sort_values("draw")
            if len(saved) != 1000:
                raise ValueError("U independent draw count differs")
            max_point = max(max_point, float(np.max(abs(point - saved.point))))
            max_var = max(max_var, float(np.max(abs(var - saved.variance))))
            lo, hi = point - z * np.sqrt(var), point + z * np.sqrt(var)
            for values, field in [(lo, "normal_low"), (hi, "normal_high")]:
                if not np.allclose(values, saved[field], rtol=0, atol=1e-12):
                    raise ArithmeticError("U independent normal endpoint differs")
            for field, original in [
                (
                    "binary_low_total",
                    "lower_total" if d["dataset"] == "ChildPlay" else "exact_lower_total",
                ),
                (
                    "binary_high_total",
                    "upper_total" if d["dataset"] == "ChildPlay" else "exact_upper_total",
                ),
            ]:
                if not np.array_equal(saved[field], baseline[original]):
                    raise ArithmeticError("U unchanged binary reference differs")
            error = point - y.mean()
            errors[method] = error
            summary = next(
                r
                for r in result["rows"]
                if r["dataset"] == d["dataset"]
                and r["budget"] == d["budget"]
                and r["method"] == method
            )
            fields = {
                "bias_pp": error.mean() * 100,
                "rmse_pp": np.sqrt(np.mean(error**2)) * 100,
                "normal_coverage": np.mean((lo <= y.mean()) & (y.mean() <= hi)),
                "normal_width_pp": np.mean(hi - lo) * 100,
                "exact_design_variance": exact,
                "exact_design_rmse_pp": np.sqrt(exact) * 100,
                "mean_estimated_variance": var.mean(),
            }
            for key, expected in fields.items():
                if not math.isclose(summary[key], expected, rel_tol=1e-10, abs_tol=1e-12):
                    raise ArithmeticError(f"U independent summary differs: {key}")
            checked += 1000
        rng = np.random.default_rng(
            np.random.SeedSequence([820000 + d["dataset_code"] * 100 + d["budget_index"], 1, 93])
        )
        index = rng.integers(1000, size=(2000, 1000))
        frequencies = np.array([np.bincount(row, minlength=1000) for row in index])
        for a, b in cfg["comparisons"]:
            top, bottom = errors[a] ** 2, errors[b] ** 2
            ratios = np.sqrt((frequencies @ top) / (frequencies @ bottom))
            ci = [quantile(ratios, p) for p in [0.025, 0.975]]
            saved = next(
                r
                for r in result["comparisons"]
                if r["dataset"] == d["dataset"]
                and r["budget"] == d["budget"]
                and r["comparison"] == a + "/" + b
            )
            difference = max(
                abs(x - v) for x, v in zip(ci, saved["paired_bootstrap_95pct"], strict=True)
            )
            max_bootstrap = max(max_bootstrap, difference)
            if (
                difference > 1e-10
                or abs(saved["rmse_ratio"] - np.sqrt(top.mean() / bottom.mean())) > 1e-10
            ):
                raise ArithmeticError("U independent bootstrap differs")
            comparisons += 1
    if checked != 32000 or comparisons != 24 or max_point > 1e-12 or max_var > 1e-12:
        raise ValueError("U independent validation incomplete")
    proof = {
        "complete": True,
        "coefficient_fits_checked": 5,
        "draw_calculations_checked": checked,
        "paired_bootstraps_checked": comparisons,
        "max_point_difference": max_point,
        "max_variance_difference": max_var,
        "max_bootstrap_endpoint_difference": max_bootstrap,
        "independent_methods": (
            "fsum centered fits; residual sum squares; "
            "frequency-weight bootstrap and manual quantiles"
        ),
        "exact_design_variances_and_all_summary_fields_checked": True,
        "training_only_contract_and_query_rng_costs_verified": True,
    }
    (OUT / "independent-validation.json").write_text(
        json.dumps(proof, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    main()
