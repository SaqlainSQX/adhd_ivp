"""Registered Q synthetic query-label stress test; old labels/queries stay immutable."""

import hashlib
import json
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

from gaze_audit.exact_intervals import stratified_binary_interval
from gaze_audit.query_noise import analytical_moments, exhaustive_toy_check, fixed_estimates
from gaze_audit.strengthening import replay_rng

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/query-noise-q-v2"
CONFIG = ROOT / "configs/query-noise-q-v2.json"


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def load_dataset(name):
    child = name == "ChildPlay"
    base = ROOT / (
        "outputs/experiments/timed-d-20261108-v1"
        if child
        else "outputs/experiments/uco-transfer-l-v1"
    )
    budget = 1032 if child else 521
    if child:
        ids = pd.read_csv(base / "population_index.csv").record_id
        q = (
            pd.read_csv(
                ROOT / "outputs/experiments/course-20261107-v1/features/features-static.csv",
                usecols=["record_id", "f_q"],
            )
            .set_index("record_id")
            .loc[ids]
            .f_q.to_numpy()
        )
        oracle = ROOT / "data/processed/vsgaze-17357752-v1/oracle/oracle_labels.csv"
    else:
        table = pd.read_csv(base / "scores-population-order.csv")
        ids, q = table.record_id, table.q.to_numpy()
        oracle = ROOT / "data/processed/uco-eligible-k4-v2/oracle.csv"
    y = pd.read_csv(oracle).set_index("record_id").loc[ids].label.to_numpy(float)
    cuts = json.loads(
        (ROOT / "outputs/experiments/timed-d-20261108-v1/K4-training.json").read_text()
    )["cuts"]
    groups = np.searchsorted(cuts, q, side="left")
    k4p = [np.flatnonzero(groups == h) for h in np.unique(groups)]
    manifest = json.loads((base / "query-manifest.json").read_text())
    uniform_name = "power-uniform" if child else "uniform"
    entries = {r.get("policy", r.get("design")): r for r in manifest if r["budget"] == budget}
    designs = {}
    for method, source in [("K4", "K4"), ("power-score", "K4"), ("uniform", uniform_name)]:
        row = entries[source]
        path = base / row["file"]
        if sha(path) != row["sha256"]:
            raise ValueError("Frozen query hash changed")
        selections = np.load(path)["selected"]
        pops = [np.arange(len(y))] if method == "uniform" else k4p
        counts = np.array(row["counts"])
        replay_rng(selections, pops, counts, 200000, 1, row["stream"])
        designs[method] = {"populations": pops, "counts": counts, "selections": selections}
    clean = pd.read_csv(base / "draw-results.csv")
    if child:
        main = pd.read_csv(
            ROOT / "outputs/experiments/course-20261107-v1/evaluation/draw-results.csv"
        )
        baseline = {
            m: clean[(clean.policy == m) & (clean.budget == budget)].sort_values("draw")
            for m in ["K4", "power-score"]
        }
        baseline["uniform"] = (
            main[(main.method == "M2") & (main.budget == budget)].sort_values("draw").copy()
        )
        classical = main[(main.method == "M1") & (main.budget == budget)].sort_values("draw")
        main_queries = np.load(
            ROOT / "outputs/experiments/course-20261107-v1/evaluation/queries-uniform-b1032.npz"
        )["selected"]
        if not np.array_equal(main_queries, designs["uniform"]["selections"]):
            raise ArithmeticError("Main M1/M2 query selections differ from Q")
        if not np.array_equal(classical.positives_revealed, baseline["uniform"].positives_revealed):
            raise ArithmeticError("Main M1/M2 queried binary counts differ")
        for field in ["hypergeometric_low", "hypergeometric_high"]:
            baseline["uniform"][field] = classical[field].to_numpy()
    else:
        baseline = {
            m: clean[(clean.method == m) & (clean.budget == budget)].sort_values("draw")
            for m in designs
        }
    return q, y, budget, designs, baseline


def run():
    cfg = json.loads(CONFIG.read_text())
    OUT.mkdir(parents=True, exist_ok=False)
    for path, expected in cfg["input_sha256"].items():
        if sha(ROOT / path) != expected:
            raise ValueError(f"Frozen Q input changed: {path}")
    write(
        OUT / "registration.json",
        {
            "config": cfg,
            "config_sha256": sha(CONFIG),
            "protocol_sha256": sha(ROOT / "docs/QUERY_NOISE_Q.md"),
            "implementation_sha256": sha(Path(__file__)),
            "kernel_sha256": sha(ROOT / "src/gaze_audit/query_noise.py"),
        },
    )
    toy = exhaustive_toy_check(cfg["toy"])
    write(OUT / "toy-validation.json", toy)
    datasets = {name: load_dataset(name) for name in cfg["datasets"]}
    z = NormalDist().inv_cdf(0.975)
    # Verify every zero-error point/variance/normal/exact interval before nonzero outcomes.
    clean_checks = []
    for name, (q, y, _budget, designs, baselines) in datasets.items():
        for method, d in designs.items():
            weight = cfg["weights"][method]
            point, var, positive, _ = fixed_estimates(
                y,
                q * weight,
                d["selections"],
                d["populations"],
                d["counts"],
                np.ones((1000, len(y))),
                0,
            )
            original = baselines[method]
            if not np.allclose(point, original.prevalence, rtol=0, atol=1e-12) or not np.allclose(
                var, original.variance, rtol=0, atol=1e-12
            ):
                raise ArithmeticError("Q eta0 baseline point/variance mismatch")
            if not np.allclose(point - z * np.sqrt(var), original.normal_low, rtol=0, atol=1e-12):
                raise ArithmeticError("Q eta0 normal interval mismatch")
            endpoints = np.array(
                [
                    stratified_binary_interval(k, d["counts"], list(map(len, d["populations"])))
                    for k in positive
                ]
            )
            totals = np.rint(endpoints * len(y)).astype(int)
            if name == "ChildPlay":
                lo, hi = (
                    (
                        np.rint(original.hypergeometric_low * len(y)),
                        np.rint(original.hypergeometric_high * len(y)),
                    )
                    if method == "uniform"
                    else (original.lower_total, original.upper_total)
                )
            else:
                lo, hi = original.exact_lower_total, original.exact_upper_total
            if not np.array_equal(totals[:, 0], lo) or not np.array_equal(totals[:, 1], hi):
                raise ArithmeticError("Q eta0 exact interval mismatch")
            clean_checks.append({"dataset": name, "method": method, "draws": 1000, "passed": True})
    write(OUT / "clean-baseline-validation.json", {"complete": True, "checks": clean_checks})
    records, summaries, noise_hashes = [], [], {}
    for name, (q, y, budget, designs, _) in datasets.items():
        code = cfg["datasets"][name]
        u = np.stack(
            [
                np.random.default_rng(np.random.SeedSequence([800000 + draw, 1, code, 91])).random(
                    len(y)
                )
                for draw in range(1000)
            ]
        )
        noise_hashes[name] = hashlib.sha256(u.tobytes()).hexdigest()
        for eta in cfg["etas"]:
            for method, d in designs.items():
                phi = q * cfg["weights"][method]
                point, var, positive, flips = fixed_estimates(
                    y, phi, d["selections"], d["populations"], d["counts"], u, eta
                )
                endpoints = np.array(
                    [
                        stratified_binary_interval(k, d["counts"], list(map(len, d["populations"])))
                        for k in positive
                    ]
                )
                totals = np.rint(endpoints * len(y)).astype(int)
                lo, hi = point - z * np.sqrt(var), point + z * np.sqrt(var)
                analytical = analytical_moments(y, phi, d["populations"], d["counts"], eta)
                err = point - y.mean()
                summaries.append(
                    {
                        "dataset": name,
                        "method": method,
                        "eta": eta,
                        "budget": budget,
                        "bias_pp": float(err.mean() * 100),
                        "rmse_pp": float(np.sqrt(np.mean(err**2)) * 100),
                        "normal_coverage": float(np.mean((lo <= y.mean()) & (y.mean() <= hi))),
                        "normal_width_pp": float(np.mean(hi - lo) * 100),
                        "naive_binary_clean_target_coverage": float(
                            np.mean((totals[:, 0] <= y.sum()) & (y.sum() <= totals[:, 1]))
                        ),
                        "naive_binary_width_pp": float(
                            np.mean(totals[:, 1] - totals[:, 0]) / len(y) * 100
                        ),
                        "mean_label_flips": float(flips.mean()),
                        "analytical": analytical,
                    }
                )
                records.append(
                    pd.DataFrame(
                        {
                            "dataset": name,
                            "method": method,
                            "eta": eta,
                            "budget": budget,
                            "draw": np.arange(1000),
                            "point": point,
                            "variance": var,
                            "normal_low": lo,
                            "normal_high": hi,
                            "binary_low_total": totals[:, 0],
                            "binary_high_total": totals[:, 1],
                            "flipped_labels": flips,
                        }
                    )
                )
                write(
                    OUT / "status.json",
                    {"state": "running", "completed_cells": len(summaries), "planned_cells": 24},
                )
                print(f"Completed {name}/{method}/eta{eta:g}", flush=True)
    pd.concat(records, ignore_index=True).to_csv(OUT / "draw-results.csv", index=False)
    write(
        OUT / "result.json",
        {
            "complete": True,
            "designation": "synthetic sensitivity; no real-annotator or held-out claim",
            "method_rate_draws": 24000,
            "noise_uniform_sha256": noise_hashes,
            "rows": summaries,
            "saved_reference_tables_modified": False,
            "new_weights_or_queries": False,
        },
    )
    write(
        OUT / "status.json",
        {"state": "computed_independent_replay_pending", "method_rate_draws": 24000},
    )


if __name__ == "__main__":
    try:
        run()
    except Exception as error:
        if OUT.exists():
            write(OUT / "failure.json", {"type": type(error).__name__, "message": str(error)})
        raise
