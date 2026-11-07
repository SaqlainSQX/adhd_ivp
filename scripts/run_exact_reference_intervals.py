"""Evaluate the separately registered exact binary reference without changing point estimates."""

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from gaze_audit.exact_intervals import checked_binary_interval, stratified_binary_interval
from gaze_audit.followups import load_main
from gaze_audit.frame_study import file_hash, read_references
from gaze_audit.strengthening import write_json

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--root", type=Path, default=Path("outputs/experiments/strengthening-20261107-v1")
)
parser.add_argument("--output", type=Path)
parser.add_argument("--main", type=Path, default=Path("outputs/experiments/course-20261107-v1"))
parser.add_argument("--processed", type=Path, default=Path("data/processed/vsgaze-17357752-v1"))
args = parser.parse_args()
started = time.monotonic()
output = args.output or args.root / "B2b-exact-reference"
if output.exists():
    parser.error("Preserve existing output and use a new versioned root")
lock, main_result, tables, _ = load_main(args.main, args.processed)
ids = tuple(tables["static"].loc[tables["static"].split.eq("test"), "record_id"])
simple_root = args.root / "B1-simple-controls"
simple_result = json.loads((simple_root / "result.json").read_text())
output.mkdir(parents=True)
write_json(
    output / "registration.json",
    {
        "designation": "exploratory exact binary reference; registered after B1/B2",
        "protocol_sha256": file_hash(Path("docs/EXACT_INTERVAL_EXTENSION.md")),
        "implementation_sha256": file_hash(Path("src/gaze_audit/exact_intervals.py")),
        "runner_sha256": file_hash(Path(__file__)),
        "main_result_sha256": file_hash(args.main / "evaluation/result.json"),
        "simple_result_sha256": file_hash(simple_root / "result.json"),
        "alpha": 0.05,
        "alpha_allocation": "equal among non-census strata",
        "point_estimate_modified": False,
        "interval_uses_q": False,
    },
)
refs = read_references(args.processed, ids)
y = np.array([refs[k] for k in ids])
truth = float(y.mean())
all_rows, summaries = [], {}
for name, folder, result, manifest in [
    (
        "main",
        args.main / "evaluation",
        main_result,
        json.loads((args.main / "evaluation/query-manifest.json").read_text()),
    ),
    (
        "simple",
        simple_root,
        simple_result,
        json.loads((simple_root / "query-manifest.json").read_text()),
    ),
]:
    draws = pd.read_csv(folder / "draw-results.csv")
    for entry in manifest:
        method = entry["design"] if name == "main" else entry["policy"]
        if method == "uniform":
            continue
        path = folder / entry["file"]
        if file_hash(path) != entry["sha256"]:
            raise ValueError("Frozen query hash changed")
        samples = np.load(path)["selected"]
        counts = np.array(entry["stratum_counts"] if name == "main" else entry["counts"])
        sizes = np.array(entry["stratum_sizes"] if name == "main" else entry["sizes"])
        boundaries = np.r_[0, np.cumsum(counts)]
        success_counts = np.stack(
            [
                y[samples[:, boundaries[h] : boundaries[h + 1]]].sum(axis=1)
                for h in range(len(counts))
            ],
            axis=1,
        )
        if samples.shape != (1000, entry["budget"]) or counts.sum() != entry["budget"]:
            raise ValueError("Incorrect saved draw count or exact budget")
        endpoints = np.array([stratified_binary_interval(k, counts, sizes) for k in success_counts])
        current = draws[
            (draws.method == method if name == "main" else draws.policy == method)
            & (draws.budget == entry["budget"])
        ].sort_values("draw")
        low, high = endpoints[:, 0], endpoints[:, 1]
        lower_total = np.rint(low * len(ids)).astype(int)
        upper_total = np.rint(high * len(ids)).astype(int)
        covered = (lower_total <= int(y.sum())) & (upper_total >= int(y.sum()))
        coverage = float(covered.mean())
        outside = (current.prevalence.to_numpy() < low) | (current.prevalence.to_numpy() > high)
        key = f"{method}-b{entry['budget']}"
        summaries[key] = {
            "coverage": coverage,
            "coverage_mcse": float(np.sqrt(coverage * (1 - coverage) / len(covered))),
            "mean_width_pp": float(np.mean(high - low) * 100),
            "median_width_pp": float(np.median(high - low) * 100),
            "original_point_outside_interval_rate": float(outside.mean()),
            "draws": len(covered),
            "budget": entry["budget"],
            "normal": result["results"][key]["intervals"]["normal"],
            "bounded": result["results"][key]["intervals"]["bounded"],
        }
        all_rows.append(
            pd.DataFrame(
                {
                    "method": method,
                    "budget": entry["budget"],
                    "draw": np.arange(len(covered)),
                    "exact_binary_low": low,
                    "exact_binary_high": high,
                    "lower_total": lower_total,
                    "upper_total": upper_total,
                    "original_point_outside": outside,
                }
            )
        )
        print(
            f"B2b {method} B={entry['budget']}: coverage={coverage:.3f}, "
            f"mean width={summaries[key]['mean_width_pp']:.4f} pp",
            flush=True,
        )
data = pd.concat(all_rows, ignore_index=True)
data.to_csv(output / "interval-draws.csv", index=False)
saved = pd.read_csv(output / "interval-draws.csv")
for (method, budget), group in saved.groupby(["method", "budget"]):
    summary = summaries[f"{method}-b{budget}"]
    coverage = ((group.lower_total <= int(y.sum())) & (group.upper_total >= int(y.sum()))).mean()
    width = (group.exact_binary_high - group.exact_binary_low).mean() * 100
    if abs(coverage - summary["coverage"]) > 1e-12 or abs(width - summary["mean_width_pp"]) > 1e-10:
        raise ValueError("Saved interval aggregates did not reproduce")
write_json(
    output / "result.json",
    {
        "complete": True,
        "designation": "exploratory exact stratified binary reference",
        "point_estimates_unchanged": True,
        "interval_center_is_not_residual_point_estimate": True,
        "existing_draws_evaluated": len(saved),
        "reference_prevalence": truth,
        "alpha": 0.05,
        "results": summaries,
        "independent_checks": {
            "endpoint_integer_tail_conditions_and_neighbors": "passed",
            "saved_csv_coverage_and_width": "passed",
            "unique_inversions_checked": checked_binary_interval.cache_info().misses,
        },
        "elapsed_seconds": time.monotonic() - started,
    },
)
