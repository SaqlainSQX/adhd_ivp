"""Execute the registered R bounded directional-label-error decomposition."""

import hashlib
import json
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd
from run_query_noise_v2 import load_dataset

from gaze_audit.directional_noise import estimates, exhaustive_check, moments
from gaze_audit.exact_intervals import stratified_binary_interval

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/directional-noise-r-v1"
CONFIG = ROOT / "configs/directional-noise-r-v1.json"


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def cell(q, y, design, uniforms, weight, case):
    point, variance, successes, flips = estimates(
        y, q * weight, design, uniforms, case["a"], case["b"]
    )
    endpoints = np.array(
        [
            stratified_binary_interval(k, design["counts"], list(map(len, design["populations"])))
            for k in successes
        ]
    )
    totals = np.rint(endpoints * len(y)).astype(int)
    z = NormalDist().inv_cdf(0.975)
    return pd.DataFrame(
        {
            "draw": np.arange(len(point)),
            "point": point,
            "variance": variance,
            "normal_low": point - z * np.sqrt(variance),
            "normal_high": point + z * np.sqrt(variance),
            "binary_low_total": totals[:, 0],
            "binary_high_total": totals[:, 1],
            "flipped_labels": flips,
        }
    )


def run():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=False)
    for name, expected in cfg["input_sha256"].items():
        if sha(ROOT / name) != expected:
            raise ValueError(f"Frozen R input changed: {name}")
    write(
        OUT / "registration.json",
        {
            "config": cfg,
            "config_sha256": sha(CONFIG),
            "implementation_sha256": sha(Path(__file__)),
            "kernel_sha256": sha(ROOT / "src/gaze_audit/directional_noise.py"),
        },
    )
    write(OUT / "toy-validation.json", exhaustive_check(cfg["toy"], cfg["cases"]))
    datasets = {name: load_dataset(name) for name in cfg["datasets"]}
    clean_q = pd.read_csv(ROOT / "outputs/query-noise-q-v2/draw-results.csv")
    controls = []
    # Gate every clean control before any directional-noise readout.
    for name, (q, y, _budget, designs, _) in datasets.items():
        for method, design in designs.items():
            current = cell(
                q, y, design, np.ones((1000, len(y))), cfg["weights"][method], cfg["cases"][0]
            )
            old = clean_q[
                (clean_q.dataset == name) & (clean_q.method == method) & (clean_q.eta == 0)
            ].sort_values("draw")
            for field in current.columns:
                if not np.allclose(current[field], old[field], rtol=0, atol=1e-12):
                    raise ArithmeticError(f"R clean control differs: {name}/{method}/{field}")
            controls.append({"dataset": name, "method": method, "draws": 1000})
    write(OUT / "clean-baseline-validation.json", {"complete": True, "checks": controls})
    records, rows, hashes = [], [], {}
    for name, (q, y, budget, designs, _) in datasets.items():
        code = cfg["datasets"][name]
        uniforms = np.stack(
            [
                np.random.default_rng(np.random.SeedSequence([810000 + d, 1, code, 92])).random(
                    len(y)
                )
                for d in range(cfg["draws"])
            ]
        )
        hashes[name] = hashlib.sha256(uniforms.tobytes()).hexdigest()
        for case in cfg["cases"]:
            for method, design in designs.items():
                table = cell(q, y, design, uniforms, cfg["weights"][method], case)
                error = table.point.to_numpy() - y.mean()
                row = {
                    "dataset": name,
                    "method": method,
                    "case": case["name"],
                    "a": case["a"],
                    "b": case["b"],
                    "budget": budget,
                    "bias_pp": float(error.mean() * 100),
                    "rmse_pp": float(np.sqrt(np.mean(error**2)) * 100),
                    "normal_coverage": float(
                        ((table.normal_low <= y.mean()) & (y.mean() <= table.normal_high)).mean()
                    ),
                    "normal_width_pp": float((table.normal_high - table.normal_low).mean() * 100),
                    "naive_binary_clean_target_coverage": float(
                        (
                            (table.binary_low_total <= y.sum())
                            & (y.sum() <= table.binary_high_total)
                        ).mean()
                    ),
                    "naive_binary_width_pp": float(
                        (table.binary_high_total - table.binary_low_total).mean() / len(y) * 100
                    ),
                    "mean_label_flips": float(table.flipped_labels.mean()),
                    "analytical": moments(
                        y,
                        q * cfg["weights"][method],
                        design["populations"],
                        design["counts"],
                        case["a"],
                        case["b"],
                    ),
                }
                rows.append(row)
                for field in ["dataset", "method", "case", "budget"]:
                    table[field] = row[field]
                records.append(table)
                write(
                    OUT / "status.json",
                    {"state": "running", "cells": len(rows), "planned_cells": 18},
                )
                print(f"Completed {name}/{method}/{case['name']}", flush=True)
    pd.concat(records, ignore_index=True).to_csv(OUT / "draw-results.csv", index=False)
    write(
        OUT / "result.json",
        {
            "complete": True,
            "method_case_draws": 18000,
            "designation": "exploratory synthetic directional sensitivity",
            "noise_uniform_sha256": hashes,
            "rows": rows,
            "new_queries_or_weights": False,
        },
    )
    write(
        OUT / "status.json",
        {"state": "computed_independent_replay_pending", "method_case_draws": 18000},
    )


if __name__ == "__main__":
    try:
        run()
    except Exception as error:
        if OUT.exists():
            write(OUT / "failure.json", {"type": type(error).__name__, "message": str(error)})
        raise
