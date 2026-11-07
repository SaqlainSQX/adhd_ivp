"""Post-hoc descriptive tail analysis; never select or modify an auditing policy."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from gaze_audit.followups import load_frozen_policy, load_main
from gaze_audit.frame_study import file_hash, make_design, read_references
from gaze_audit.strengthening import write_json

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--main", type=Path, default=Path("outputs/experiments/course-20261107-v1"))
parser.add_argument("--processed", type=Path, default=Path("data/processed/vsgaze-17357752-v1"))
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
if args.output.exists():
    parser.error("Preserve existing diagnostics; choose a new output")
lock, result, tables, _ = load_main(args.main, args.processed)
test = {k: t[t.split.eq("test")].reset_index(drop=True) for k, t in tables.items()}
ids = tuple(test["static"].record_id)
refs = read_references(args.processed, ids)
y, q = np.array([refs[k] for k in ids]), test["static"].f_q.to_numpy()
draws = pd.read_csv(args.main / "evaluation/draw-results.csv")
manifest = json.loads((args.main / "evaluation/query-manifest.json").read_text())
rows = []
for method, field in [("M3", "selected_static"), ("M4", "selected_temporal")]:
    chosen = lock[field]
    policy = load_frozen_policy(args.main, chosen["feature_set"], lock)
    groups = policy.strata(test[chosen["feature_set"]])
    for budget in [1032, 2063]:
        populations, counts = make_design(groups, policy.residual_sd, budget, chosen["alpha"])
        entry = next(e for e in manifest if e["design"] == method and e["budget"] == budget)
        path = args.main / "evaluation" / entry["file"]
        if file_hash(path) != entry["sha256"]:
            raise ValueError("Saved query hash changed")
        selected = np.load(path)["selected"]
        data = draws[(draws.method == method) & (draws.budget == budget)].sort_values("draw")
        covered = (data.normal_low <= result["reference_prevalence"]) & (
            data.normal_high >= result["reference_prevalence"]
        )
        edges = np.r_[0, np.cumsum(counts)]
        for h, population in enumerate(populations):
            positions = np.asarray(population)
            residual = y[positions] - q[positions]
            centered = residual - residual.mean()
            squares = centered**2
            tail_mask = np.zeros(len(ids), dtype=bool)
            tail_mask[positions] = np.abs(centered) > 0.5
            tail_found = tail_mask[selected[:, edges[h] : edges[h + 1]]].sum(axis=1)
            conditions = []
            for label, mask in [
                ("zero", tail_found == 0),
                ("one", tail_found == 1),
                ("two_or_more", tail_found >= 2),
            ]:
                if mask.any():
                    conditions.append(
                        {
                            "tail_queries": label,
                            "draws": int(mask.sum()),
                            "normal_coverage": float(covered.to_numpy()[mask].mean()),
                            "mean_estimated_variance": float(data.variance.to_numpy()[mask].mean()),
                        }
                    )
            rows.append(
                {
                    "method": method,
                    "budget": budget,
                    "stratum": h,
                    "population": len(population),
                    "queries": int(counts[h]),
                    "census": bool(len(population) == counts[h]),
                    "negative_residual_below_minus_half": int((residual < -0.5).sum()),
                    "positive_residual_above_half": int((residual > 0.5).sum()),
                    "centered_absolute_residual_above_half": int(tail_mask.sum()),
                    "variance_fraction_largest_10_residuals": float(
                        np.sort(squares)[-10:].sum() / squares.sum()
                    )
                    if squares.sum()
                    else 0.0,
                    "zero_tail_query_rate": float((tail_found == 0).mean()),
                    "conditional_diagnostics": conditions,
                }
            )
args.output.parent.mkdir(parents=True, exist_ok=True)
write_json(
    args.output,
    {
        "designation": "post-hoc descriptive explanation; "
        "threshold not used for selection or deployable intervals",
        "threshold": "abs(residual - full-test stratum mean) > 0.5",
        "main_result_sha256": file_hash(args.main / "evaluation/result.json"),
        "rows": rows,
    },
)
print(args.output)
