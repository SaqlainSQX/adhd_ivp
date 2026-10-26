"""Run exploratory M1 on pre-media annotations; no model-effectiveness claims."""

import argparse
import csv
import hashlib
import json
import time
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from gaze_audit.frames import (
    FrameOracle,
    FrameStratum,
    estimate_frames,
    hypergeometric_interval,
    integer_budget,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed", type=Path, default=Path("data/processed/vsgaze-17357752-v1"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--split", choices=["validation", "test"], default="test")
    parser.add_argument("--draws", type=int, default=1000)
    parser.add_argument("--seed-start", type=int, default=200000)
    args = parser.parse_args()
    if args.draws < 1 or args.output.exists():
        parser.error("Require positive draws and a new output directory")
    started = time.monotonic()
    pairs = pd.read_csv(args.processed / "public/public_pairs.csv")
    population = pairs.loc[(pairs.split == args.split) & (pairs.eligible_anchor == 1)].copy()
    ids = tuple(population.record_id)
    size = len(ids)
    if len(set(ids)) != size or size < 2:
        raise ValueError("Require a unique nonempty eligible population")
    args.output.mkdir(parents=True)
    population[["record_id", "source_id"]].reset_index(drop=True).to_csv(
        args.output / "population_index.csv", index_label="row_index"
    )
    report = {
        "method": "M1-human-uniform",
        "designation": "exploratory",
        "population_status": "pre-media-availability; rerun on final common population",
        "model_predictions_used": False,
        "population_size": size,
        "split": args.split,
        "draws_per_budget": args.draws,
        "seed_start": args.seed_start,
        "method_stream_id": 1,
        "budgets": [],
        "complete": False,
    }
    config_path = args.output / "result.json"
    config_path.write_text(json.dumps(report, indent=2))
    # Save every query plan before opening the oracle reference file.
    for budget_index, fraction in enumerate([0.05, 0.1, 0.2, 0.4]):
        budget = integer_budget(fraction, size)
        selected = np.empty((args.draws, budget), dtype=np.int32)
        for draw in range(args.draws):
            rng = np.random.default_rng(
                np.random.SeedSequence([args.seed_start + draw, budget_index, 1])
            )
            selected[draw] = rng.choice(size, size=budget, replace=False)
        path = args.output / f"query-indices-b{budget}.npz"
        np.savez_compressed(path, selected=selected)
        report["budgets"].append(
            {
                "fraction": fraction,
                "integer_labels": budget,
                "query_plan_file": path.name,
                "query_plan_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
        print(f"Saved {args.draws} query plans at B={budget} before oracle access", flush=True)
    report["all_plans_saved_before_oracle"] = True
    references = pd.read_csv(args.processed / "oracle/oracle_labels.csv")
    labels = references[references.record_id.isin(ids)]
    if len(labels) != size or labels.record_id.duplicated().any():
        raise ValueError("Reference ID mismatch")
    oracle = FrameOracle(dict(zip(labels.record_id, labels.label, strict=True)), ids)
    truth = float(labels.label.mean())  # Evaluator-only, never passed to sampler or estimator.
    report["reference_prevalence"] = truth
    q = np.zeros(size)
    whole = tuple(range(size))
    sources = population.source_id.to_numpy()
    exact_interval = lru_cache(maxsize=None)(hypergeometric_interval)
    rows = []
    for entry in report["budgets"]:
        samples = np.load(args.output / entry["query_plan_file"])["selected"]
        begin = len(rows)
        for draw, indices in enumerate(samples):
            selection = tuple(map(int, indices))
            selected_ids = tuple(ids[i] for i in selection)
            queried = oracle.query(selected_ids)
            result = estimate_frames(ids, q, (FrameStratum(whole, selection),), queried)
            low, high = exact_interval(result.positives_revealed, len(selection), size)
            rows.append(
                {
                    "draw": draw,
                    "budget": len(selection),
                    **result.as_dict(),
                    "hypergeometric_low": low,
                    "hypergeometric_high": high,
                    "source_count": len(set(sources[indices])),
                }
            )
        data = pd.DataFrame(rows[begin:])
        error = data.prevalence - truth
        entry.update(
            {
                "bias_pp": float(error.mean() * 100),
                "mae_pp": float(error.abs().mean() * 100),
                "rmse_pp": float(np.sqrt(np.mean(error**2)) * 100),
                "empirical_variance": float(data.prevalence.var(ddof=1)),
                "mean_estimated_variance": float(data.variance.mean()),
                "known_design_variance": float(
                    (1 - entry["integer_labels"] / size)
                    * labels.label.var(ddof=1)
                    / entry["integer_labels"]
                ),
                "zero_variance_rate": float((data.variance == 0).mean()),
                "zero_positive_rate": float((data.positives_revealed == 0).mean()),
                "failed_draw_rate": 0.0,
                "mean_source_count": float(data.source_count.mean()),
                "intervals": {},
            }
        )
        for interval in ["normal", "bounded", "hypergeometric"]:
            lower, upper = data[f"{interval}_low"], data[f"{interval}_high"]
            entry["intervals"][interval] = {
                "coverage": float(((lower <= truth) & (truth <= upper)).mean()),
                "mean_width_pp": float((upper - lower).mean() * 100),
                "median_width_pp": float((upper - lower).median() * 100),
            }
        print(f"B={entry['integer_labels']}: RMSE={entry['rmse_pp']:.4f} pp", flush=True)
    with (args.output / "draw-results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report.update(
        {
            "complete": True,
            "sampled_method_runs": len(rows),
            "runtime_seconds": time.monotonic() - started,
            "oracle_labels_returned_over_all_draws": oracle.total_queries,
            "query_replay": "Use population_index.csv and saved npz selected row indices",
            "normalized_manifest_sha256": hashlib.sha256(
                (args.processed / "manifest.json").read_bytes()
            ).hexdigest(),
        }
    )
    config_path.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Saved {len(rows)} exploratory draws to {args.output}", flush=True)


if __name__ == "__main__":
    main()
