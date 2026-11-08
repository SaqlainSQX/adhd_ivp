"""Run the registered L public query-plan stage, then its separate oracle evaluation."""

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from gaze_audit.exact_intervals import stratified_binary_interval
from gaze_audit.followups import evaluate_plans
from gaze_audit.frame_study import make_design, save_queries, summarize_draws
from gaze_audit.frames import FrameOracle
from gaze_audit.strengthening import replay_rng, sampled_components, verify_estimates

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/uco-transfer-l-v1.json"


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def plan(cfg, out):
    assert not out.exists(), "Preserve old plans/results; register a new output version"
    for p, expected in cfg["input_sha256"].items():
        if Path(p).name != "oracle.csv":
            assert sha(ROOT / p) == expected, p
    cache = ROOT / cfg["score_cache"]
    provenance = json.loads((cache / "inference-provenance.json").read_text())
    assert provenance["complete"] and not provenance["oracle_opened"]
    scores = []
    for clip in provenance["clips"]:
        path = cache / clip["file"]
        assert sha(path) == clip["sha256"]
        table = pd.read_csv(path)
        assert len(table) == clip["rows"]
        scores.append(table)
    scores = pd.concat(scores, ignore_index=True)
    public = pd.read_csv(ROOT / "data/processed/uco-eligible-k4-v2/eligible-pairs.csv")
    assert len(scores) == len(public) == cfg["population_size"]
    assert scores.record_id.is_unique and set(scores.record_id) == set(public.record_id)
    scores = scores.set_index("record_id").loc[public.record_id].reset_index()
    q = scores.q.to_numpy(float)
    assert np.isfinite(q).all() and ((q >= 0) & (q <= 1)).all()
    assert np.allclose(
        q, scores[["direction_a_to_b", "direction_b_to_a"]].min(axis=1), rtol=0, atol=1e-15
    )
    out.mkdir(parents=True)
    scores.to_csv(out / "scores-population-order.csv", index=False)
    groups = np.searchsorted(cfg["k4_training"]["cuts"], q, side="left")
    manifest = []
    for bi, budget in enumerate(cfg["budgets"]):
        for design, strata, sd, alpha, stream in [
            ("K4", groups, cfg["k4_training"]["sd"], cfg["alpha"], 61),
            ("uniform", np.zeros(len(q), int), [1.0], 0.0, 62),
        ]:
            pops, counts = make_design(strata, sd, budget, alpha)
            path = out / f"queries-{design}-b{budget}.npz"
            checksum = save_queries(path, pops, counts, cfg["draws"], cfg["seed_start"], bi, stream)
            manifest.append(
                {
                    "design": design,
                    "budget_index": bi,
                    "budget": budget,
                    "stream": stream,
                    "file": path.name,
                    "sha256": checksum,
                    "populations": [list(p) for p in pops],
                    "counts": counts.tolist(),
                }
            )
    write(out / "query-manifest.json", manifest)
    write(
        out / "registration.json",
        {
            "stage": "L-queries-frozen-before-oracle-evaluation",
            "utc": datetime.now(timezone.utc).isoformat(),
            "config_sha256": sha(CONFIG),
            "protocol_sha256": sha(ROOT / cfg["protocol"]),
            "implementation_sha256": sha(Path(__file__)),
            "inference_provenance_sha256": sha(cache / "inference-provenance.json"),
            "score_table_sha256": sha(out / "scores-population-order.csv"),
            "manifest_sha256": sha(out / "query-manifest.json"),
            "oracle_opened": False,
        },
    )
    write(
        out / "status.json",
        {
            "state": "plans_complete",
            "query_files": 8,
            "planned_method_draws": 12000,
            "oracle_opened": False,
        },
    )
    print("Verified 5219 cached scores; all eight public query files frozen before oracle readout.")


def evaluate(cfg, out):
    assert not (out / "result.json").exists()
    reg = json.loads((out / "registration.json").read_text())
    assert (
        sha(CONFIG) == reg["config_sha256"] and sha(Path(__file__)) == reg["implementation_sha256"]
    )
    assert sha(out / "query-manifest.json") == reg["manifest_sha256"]
    assert sha(out / "scores-population-order.csv") == reg["score_table_sha256"]
    manifest = json.loads((out / "query-manifest.json").read_text())
    for row in manifest:
        assert sha(out / row["file"]) == row["sha256"]
    table = pd.read_csv(out / "scores-population-order.csv")
    ids, q = tuple(table.record_id), table.q.to_numpy(float)
    oracle_path = ROOT / "data/processed/uco-eligible-k4-v2/oracle.csv"
    assert (
        sha(oracle_path)
        == cfg["input_sha256"][str(oracle_path.relative_to(ROOT)).replace("\\", "/")]
    )
    with oracle_path.open() as handle:
        references = {r["record_id"]: int(r["label"]) for r in csv.DictReader(handle)}
    oracle = FrameOracle(references, ids)
    y = np.array([references[k] for k in ids], float)
    truth = float(y.mean())
    summaries, records, checks = {}, [], []
    for entry in manifest:
        pops = tuple(tuple(p) for p in entry["populations"])
        counts = np.array(entry["counts"])
        for method in ["K4", "power-score"] if entry["design"] == "K4" else ["uniform"]:
            weight = cfg["methods"][method]["weight"]
            data, selections = evaluate_plans(
                ids, q * weight, pops, counts, out / entry["file"], oracle
            )
            replay_rng(
                selections, pops, counts, cfg["seed_start"], entry["budget_index"], entry["stream"]
            )
            point, components, strata, positive = sampled_components(
                selections, pops, counts, q * weight, y
            )
            check = verify_estimates(data, point, components)
            sizes = list(map(len, pops))
            endpoints = np.array([stratified_binary_interval(k, counts, sizes) for k in positive])
            totals = np.rint(endpoints * len(y)).astype(int)
            summary = summarize_draws(data, truth)
            summary["intervals"].pop("bounded", None)
            summary["intervals"]["exact_binary_reference"] = {
                "coverage": float(np.mean((totals[:, 0] <= y.sum()) & (y.sum() <= totals[:, 1]))),
                "mean_width_pp": float(np.mean(totals[:, 1] - totals[:, 0]) / len(y) * 100),
            }
            summary["exact_design_variance"] = sum(
                s["exact_design_variance_component"] for s in strata
            )
            summary["mean_estimated_variance"] = float(data.variance.mean())
            summary["strata"] = strata
            key = f"{method}-b{entry['budget']}"
            summaries[key] = summary
            checks.append({"method": method, "budget": entry["budget"], **check})
            records.append(
                data.assign(
                    method=method,
                    budget=entry["budget"],
                    exact_lower_total=totals[:, 0],
                    exact_upper_total=totals[:, 1],
                )
            )
            write(
                out / "status.json",
                {
                    "state": "evaluating",
                    "completed_method_cells": len(checks),
                    "planned_method_cells": 12,
                },
            )
            print(f"Completed {key}; independent point/variance replay passed", flush=True)
    data = pd.concat(records, ignore_index=True)
    data.to_csv(out / "draw-results.csv", index=False)
    ratios = {}
    for bi, budget in enumerate(cfg["budgets"]):
        errors = {
            m: data[(data.method == m) & (data.budget == budget)]
            .sort_values("draw")
            .prevalence.to_numpy()
            - truth
            for m in cfg["methods"]
        }
        for top, bottom in [("power-score", "K4"), ("K4", "uniform"), ("power-score", "uniform")]:
            rng = np.random.default_rng(cfg["bootstrap_seed_start"] + bi)
            ix = rng.integers(cfg["draws"], size=(cfg["bootstrap_resamples"], cfg["draws"]))
            ratio = float(np.sqrt(np.mean(errors[top] ** 2) / np.mean(errors[bottom] ** 2)))
            boot = np.sqrt(
                np.mean(errors[top][ix] ** 2, axis=1) / np.mean(errors[bottom][ix] ** 2, axis=1)
            )
            ratios[f"{top}/{bottom}-b{budget}"] = {
                "rmse_ratio": ratio,
                "draw_bootstrap_95pct": np.quantile(boot, [0.025, 0.975]).tolist(),
                "seed": cfg["bootstrap_seed_start"] + bi,
                "same_queries": top == "power-score" and bottom == "K4",
            }
    write(
        out / "independent-validation.json",
        {"complete": True, "method_draws": len(data), "checks": checks, "RNG_cost_replay": True},
    )
    write(
        out / "result.json",
        {
            "complete": True,
            "reference_prevalence": truth,
            "population_size": len(y),
            "method_draws": len(data),
            "results": summaries,
            "comparisons": ratios,
            "registration_sha256": sha(out / "registration.json"),
            "query_manifest_sha256": sha(out / "query-manifest.json"),
        },
    )
    write(
        out / "status.json",
        {
            "state": "evaluation_complete_independent_interval_review_pending",
            "method_draws": len(data),
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["plan", "evaluate"])
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text())
    (plan if args.stage == "plan" else evaluate)(config, ROOT / config["output"])
