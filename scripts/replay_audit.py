"""Replay a frozen audit and export its public score/feature/query timeline."""

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from gaze_audit.frame_study import (
    file_hash,
    load_feature_population,
    make_design,
    read_references,
    reconstruct_plan,
)
from gaze_audit.frames import FrameOracle, estimate_frames, integer_budget


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--development", type=Path, required=True)
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--processed", type=Path, default=Path("data/processed/vsgaze-17357752-v1"))
    parser.add_argument("--method", choices=["M1", "M2", "M3", "M4", "M5"], default="M4")
    parser.add_argument("--fraction", type=float, choices=[0.05, 0.1, 0.2, 0.4], default=0.1)
    parser.add_argument("--draw", type=int, default=0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new replay directory")
    result = json.loads((args.evaluation / "result.json").read_text())
    lock_path = args.development / "policy-lock.json"
    lock = json.loads(lock_path.read_text())
    tables, hashes = load_feature_population(args.features)
    if result["feature_hashes"] != hashes or file_hash(lock_path) != result["policy_lock_sha256"]:
        raise ValueError("Replay policy/feature version mismatch")
    if file_hash(args.processed / "oracle/oracle_labels.csv") != result["oracle_file_sha256"]:
        raise ValueError("Oracle references changed since evaluation")
    mask = tables["static"].split.eq("test").to_numpy()
    test = {key: value.loc[mask].reset_index(drop=True) for key, value in tables.items()}
    ids = tuple(test["static"].record_id)
    population = pd.read_csv(args.evaluation / "population_index.csv")
    if tuple(population.record_id) != ids:
        raise ValueError("Saved population order changed")
    budget = integer_budget(args.fraction, len(ids))
    design_name = "uniform" if args.method in ["M1", "M2", "M5"] else args.method
    manifest = json.loads((args.evaluation / "query-manifest.json").read_text())
    entry = next(r for r in manifest if r["budget"] == budget and r["design"] == design_name)
    path = args.evaluation / entry["file"]
    if file_hash(path) != entry["sha256"]:
        raise ValueError("Saved query indices changed")
    samples = np.load(path)["selected"]
    if not 0 <= args.draw < len(samples):
        raise ValueError("Draw outside recorded evaluation")
    q = test["static"].f_q.to_numpy(float)
    if args.method in ["M3", "M4", "M5"]:
        field = "selected_static" if args.method == "M3" else "selected_temporal"
        selected_policy = lock[field]
        key = selected_policy["feature_set"]
        policy_path = args.development / f"{key}-policy.joblib"
        if file_hash(policy_path) != lock["model_hashes"][key]:
            raise ValueError("Saved policy changed")
        policy = joblib.load(policy_path)
        if args.method == "M5":
            q = policy.contextual_surrogate(test[key])
    if design_name == "uniform":
        populations, counts, stream = (tuple(range(len(ids))),), np.array([budget]), 1
    else:
        populations, counts = make_design(
            policy.strata(test[key]), policy.residual_sd, budget, selected_policy["alpha"]
        )
        stream = 3 if args.method == "M3" else 4
    rng = np.random.default_rng(
        np.random.SeedSequence(
            [200000 + args.draw, [0.05, 0.1, 0.2, 0.4].index(args.fraction), stream]
        )
    )
    regenerated = np.concatenate(
        [
            rng.choice(p, size=int(n), replace=False)
            for p, n in zip(populations, counts, strict=True)
        ]
    )
    selection = samples[args.draw]
    if not np.array_equal(selection, regenerated):
        raise ValueError("RNG replay differs from saved plan")
    selected_ids = tuple(ids[i] for i in selection)
    labels = read_references(args.processed, selected_ids)
    oracle = FrameOracle(labels, selected_ids)
    queried = oracle.query(selected_ids)
    plan = reconstruct_plan(populations, counts, selection)
    estimate = estimate_frames(ids, np.zeros(len(ids)) if args.method == "M1" else q, plan, queried)
    recorded = pd.read_csv(args.evaluation / "draw-results.csv")
    recorded = recorded[
        (recorded.method == args.method)
        & (recorded.budget == budget)
        & (recorded.draw == args.draw)
    ].iloc[0]
    if abs(estimate.prevalence - recorded.prevalence) > 1e-12:
        raise ValueError("Replay differs from recorded estimate")
    args.output.mkdir(parents=True)
    pd.DataFrame(
        {"record_id": selected_ids, "revealed_label": [queried[k] for k in selected_ids]}
    ).to_csv(args.output / "revealed-queries.csv", index=False)
    temporal_key = lock["selected_temporal"]["feature_set"]
    public = pd.read_csv(args.features / f"features-{temporal_key}.csv")
    chosen = public[public.record_id.isin(selected_ids)]
    keys = ["clip_id", "person_a", "person_b"]
    example = chosen.groupby(keys).size().sort_values(ascending=False, kind="stable").index[0]
    matching = np.logical_and.reduce([public[k].eq(v) for k, v in zip(keys, example, strict=True)])
    timeline = public[matching].copy().sort_values("clip_frame_index_1based")
    timeline["selected_query"] = timeline.record_id.isin(selected_ids).astype(int)
    columns = [
        "record_id",
        "clip_frame_index_1based",
        "f_q",
        "f_t_q_mean",
        "f_t_q_std",
        "selected_query",
    ]
    timeline[columns].to_csv(args.output / "public-query-timeline.csv", index=False)
    report = {
        "complete": True,
        "method": args.method,
        "draw": args.draw,
        "fraction": args.fraction,
        "exact_labels": budget,
        "rng_plan_reproduced": True,
        "estimate_reproduced": True,
        "estimate": estimate.as_dict(),
        "query_file_sha256": entry["sha256"],
        "example": dict(zip(keys, [str(v) for v in example], strict=True)),
        "timeline_includes_reference_values": False,
        "revealed_labels_file": "revealed-queries.csv",
    }
    (args.output / "replay.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
