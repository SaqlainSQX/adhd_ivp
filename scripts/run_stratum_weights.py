"""Run U: training-only coefficients, frozen queries and all registered controls."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd
from run_query_noise_v2 import load_dataset

from gaze_audit.exact_intervals import stratified_binary_interval
from gaze_audit.stratum_weights import audit, bootstrap, fit_coefficient, toy_check
from gaze_audit.strengthening import replay_rng

OUT = Path("outputs/stratum-weights-u-v1")
CONFIG = Path("configs/stratum-weights-u-v1.json")
FEATURES = Path("outputs/experiments/course-20261107-v1/features/features-static.csv")
ORACLE = Path("data/processed/vsgaze-17357752-v1/oracle/oracle_labels.csv")


def write(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def sha(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def training_data():
    features = pd.read_csv(
        FEATURES, usecols=["record_id", "split", "eligible_anchor", "source_id", "f_q"]
    )
    train = features[(features.split == "train") & (features.eligible_anchor == 1)].copy()
    # Only selected training IDs/labels are supplied to coefficient fitting.
    oracle = pd.read_csv(ORACLE, usecols=["record_id", "label"]).set_index("record_id")
    train["label"] = oracle.loc[train.record_id, "label"].to_numpy()
    if train.record_id.duplicated().any() or not train.label.isin([0, 1]).all():
        raise ValueError("U training identity/reference contract failed")
    return train


def run():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=False)
    for path, expected in cfg["input_sha256"].items():
        if sha(path) != expected:
            raise ValueError(f"U frozen input changed: {path}")
    write(
        OUT / "registration.json",
        {
            "config": cfg,
            "config_sha256": sha(CONFIG),
            "implementation_sha256": sha(__file__),
            "kernel_sha256": sha("src/gaze_audit/stratum_weights.py"),
        },
    )
    write(OUT / "toy-validation.json", toy_check())
    train = training_data()
    if len(train) != cfg["training_rows"] or train.source_id.nunique() != cfg["training_sources"]:
        raise ValueError("U registered training population differs")
    cuts = json.loads(
        Path("outputs/experiments/timed-d-20261108-v1/K4-training.json").read_text(encoding="utf-8")
    )["cuts"]
    groups = np.searchsorted(cuts, train.f_q.to_numpy(), side="left")
    fits = [
        fit_coefficient(train.f_q.to_numpy()[groups == h], train.label.to_numpy()[groups == h])
        for h in range(4)
    ]
    fit = {
        "global": fit_coefficient(train.f_q.to_numpy(), train.label.to_numpy()),
        "strata": fits,
        "training_rows": len(train),
        "training_sources": int(train.source_id.nunique()),
        "training_id_sha256": hashlib.sha256(
            "\n".join(sorted(train.record_id)).encode()
        ).hexdigest(),
        "cuts": cuts,
        "fit_saved_utc": datetime.now(timezone.utc).isoformat(),
        "test_or_uco_labels_supplied_to_fit": False,
    }
    write(OUT / "coefficient-lock.json", fit)
    # Evaluation-population access happens only after the training coefficients are saved.
    datasets = {name: load_dataset(name) for name in ["ChildPlay", "UCO"]}
    controls, cached = [], []
    z = NormalDist().inv_cdf(0.975)
    for d in cfg["designs"]:
        name, budget = d["dataset"], d["budget"]
        q, y, _, primary_designs, _ = datasets[name]
        populations = primary_designs["K4"]["populations"]
        selected = np.load(d["query"])["selected"]
        counts = np.array(d["counts"])
        replay_rng(selected, populations, counts, 200000, d["budget_index"], d["stream"])
        old = pd.read_csv(Path(d["base"]) / "draw-results.csv")
        successes, offset = [], 0
        for n in counts:
            successes.append(y[selected[:, offset : offset + n]].sum(axis=1).astype(int))
            offset += n
        binary = np.rint(
            np.array(
                [
                    stratified_binary_interval(k, counts, list(map(len, populations)))
                    for k in np.stack(successes, axis=1)
                ]
            )
            * len(y)
        ).astype(int)
        for method, policy, weight in [("full", "K4", 1), ("half", "power-score", 0.5)]:
            field = "policy" if name == "ChildPlay" else "method"
            base = old[(old[field] == policy) & (old.budget == budget)].sort_values("draw")
            point, var, exact = audit(y, q * weight, populations, counts, selected)
            for values, original in [
                (point, base.prevalence),
                (var, base.variance),
                (point - z * np.sqrt(var), base.normal_low),
                (point + z * np.sqrt(var), base.normal_high),
            ]:
                if not np.allclose(values, original, rtol=0, atol=1e-12):
                    raise ArithmeticError("U frozen full/half point/variance/normal control failed")
            low = base.lower_total if name == "ChildPlay" else base.exact_lower_total
            high = base.upper_total if name == "ChildPlay" else base.exact_upper_total
            if not np.array_equal(binary[:, 0], low) or not np.array_equal(binary[:, 1], high):
                raise ArithmeticError("U frozen binary interval control failed")
            controls.append({"dataset": name, "budget": budget, "method": method, "draws": 1000})
        cached.append((d, q, y, populations, selected, binary))
    write(OUT / "baseline-validation.json", {"complete": True, "checks": controls})
    tables, rows, comparisons = [], [], []
    for d, q, y, pops, selected, binary in cached:
        group = np.searchsorted(cuts, q, side="left")
        coefficients = {
            "full": np.ones(len(q)),
            "half": np.full(len(q), 0.5),
            "global": np.full(len(q), fit["global"]["coefficient"]),
            "stratum": np.array([r["coefficient"] for r in fits])[group],
        }
        errors = {}
        for method, weights in coefficients.items():
            point, var, exact = audit(y, q * weights, pops, d["counts"], selected)
            lo, hi = point - z * np.sqrt(var), point + z * np.sqrt(var)
            err = point - y.mean()
            errors[method] = err
            row = {
                "dataset": d["dataset"],
                "budget": d["budget"],
                "method": method,
                "bias_pp": float(err.mean() * 100),
                "rmse_pp": float(np.sqrt(np.mean(err**2)) * 100),
                "normal_coverage": float(np.mean((lo <= y.mean()) & (y.mean() <= hi))),
                "normal_width_pp": float(np.mean(hi - lo) * 100),
                "exact_design_variance": exact,
                "exact_design_rmse_pp": float(np.sqrt(exact) * 100),
                "mean_estimated_variance": float(var.mean()),
            }
            rows.append(row)
            tables.append(
                pd.DataFrame(
                    {
                        "dataset": d["dataset"],
                        "budget": d["budget"],
                        "method": method,
                        "draw": np.arange(1000),
                        "point": point,
                        "variance": var,
                        "normal_low": lo,
                        "normal_high": hi,
                        "binary_low_total": binary[:, 0],
                        "binary_high_total": binary[:, 1],
                    }
                )
            )
            print(f"Computed {d['dataset']}/{d['budget']}/{method}", flush=True)
        for a, b in cfg["comparisons"]:
            comparisons.append(
                {
                    "dataset": d["dataset"],
                    "budget": d["budget"],
                    "comparison": a + "/" + b,
                    "primary": a == "stratum" and b == "full" and d["budget_index"] == 1,
                    **bootstrap(errors[a], errors[b], d["dataset_code"], d["budget_index"]),
                }
            )
    pd.concat(tables, ignore_index=True).to_csv(OUT / "draw-results.csv", index=False)
    write(
        OUT / "result.json",
        {
            "complete": True,
            "designation": "exploratory training-only coefficient extension",
            "rows": rows,
            "comparisons": comparisons,
            "draw_calculations": 32000,
            "no_test_weight_selection": True,
            "coefficient_lock_sha256": sha(OUT / "coefficient-lock.json"),
        },
    )
    write(OUT / "status.json", {"state": "computed_independent_validation_pending", "draws": 32000})


if __name__ == "__main__":
    try:
        run()
    except Exception as error:
        if OUT.exists():
            write(OUT / "failure.json", {"type": type(error).__name__, "message": str(error)})
        raise
