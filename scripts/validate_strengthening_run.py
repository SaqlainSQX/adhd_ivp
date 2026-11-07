"""Independent post-run control/interval recomputation; never modify original evidence."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t

from gaze_audit.followups import load_frozen_policy, load_main
from gaze_audit.frame_study import file_hash, make_design, read_references

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--root", type=Path, default=Path("outputs/experiments/strengthening-20261107-v1")
)
parser.add_argument("--main", type=Path, default=Path("outputs/experiments/course-20261107-v1"))
parser.add_argument("--processed", type=Path, default=Path("data/processed/vsgaze-17357752-v1"))
args = parser.parse_args()
output = args.root / "independent-validation.json"
if output.exists():
    parser.error("Preserve existing validation evidence")
main_lock, main_result, tables, _ = load_main(args.main, args.processed)
test = {key: table[table.split.eq("test")].reset_index(drop=True) for key, table in tables.items()}
ids = tuple(test["static"].record_id)
refs = read_references(args.processed, ids)
y, q = np.array([refs[k] for k in ids]), test["static"].f_q.to_numpy()
truth = float(y.mean())
simple_root, ci_root = args.root / "B1-simple-controls", args.root / "B2-coverage"
simple = json.loads((simple_root / "result.json").read_text())
simple_lock = json.loads((simple_root / "policy-lock.json").read_text())
ci = json.loads((ci_root / "result.json").read_text())
ci_lock = json.loads((ci_root / "interval-lock.json").read_text())
if (
    file_hash(simple_root / "policy-lock.json") != simple["policy_lock_sha256"]
    or file_hash(ci_root / "interval-lock.json") != ci["interval_lock_sha256"]
):
    raise ValueError("Extension lock changed")
main_draws = pd.read_csv(args.main / "evaluation/draw-results.csv")
simple_draws = pd.read_csv(simple_root / "draw-results.csv")
main_queries = json.loads((args.main / "evaluation/query-manifest.json").read_text())
checks = []
for stage, manifest, data in [
    ("B1", json.loads((simple_root / "query-manifest.json").read_text()), simple_draws),
    ("B2", [r for r in main_queries if r["design"] in ["M3", "M4"]], main_draws),
]:
    for entry in manifest:
        method = entry["policy"] if stage == "B1" else entry["design"]
        budget = entry["budget"]
        fraction = entry["fraction"]
        bi = [0.05, 0.1, 0.2, 0.4].index(fraction)
        path = (simple_root if stage == "B1" else args.main / "evaluation") / entry["file"]
        if file_hash(path) != entry["sha256"]:
            raise ValueError("Query hash changed")
        if stage == "B1":
            policy = simple_lock["policies"][method]
            group = np.searchsorted(
                policy["cut_points"], test["static"][policy["feature"]], side="left"
            )
            pop, counts = make_design(
                group, policy["residual_sd"], budget, simple_lock["selected"][method]["alpha"]
            )
            stream = 7 if method == "q-quartiles" else 8
            current = data[(data.policy == method) & (data.budget == budget)].sort_values("draw")
        else:
            chosen = main_lock["selected_static" if method == "M3" else "selected_temporal"]
            policy = load_frozen_policy(args.main, chosen["feature_set"], main_lock)
            pop, counts = make_design(
                policy.strata(test[chosen["feature_set"]]),
                policy.residual_sd,
                budget,
                chosen["alpha"],
            )
            stream = 3 if method == "M3" else 4
            current = data[(data.method == method) & (data.budget == budget)].sort_values("draw")
        selected = np.load(path)["selected"]
        if selected.shape != (1000, budget) or not current.labels_revealed.eq(budget).all():
            raise ValueError("Wrong draw count or charged budget")
        if (np.diff(np.sort(selected, axis=1), axis=1) == 0).any():
            raise ValueError("Repeated query within a draw")
        for draw, row in enumerate(selected):
            rng = np.random.default_rng(np.random.SeedSequence([200000 + draw, bi, stream]))
            expected = np.concatenate(
                [
                    rng.choice(p, size=int(n), replace=False)
                    for p, n in zip(pop, counts, strict=True)
                ]
            )
            if not np.array_equal(row, expected):
                raise ValueError("Query RNG replay failed")
        point, variance, df_denominator = np.full(1000, q.mean()), np.zeros(1000), np.zeros(1000)
        boundaries = np.r_[0, np.cumsum(counts)]
        for h, population in enumerate(pop):
            positions = selected[:, boundaries[h] : boundaries[h + 1]]
            if not np.isin(positions, population).all():
                raise ValueError("Outside frozen stratum")
            nh, n = len(population), counts[h]
            residual = y[positions] - q[positions]
            point += nh / len(ids) * residual.mean(axis=1)
            if n < nh:
                component = (nh / len(ids)) ** 2 * (1 - n / nh) * residual.var(axis=1, ddof=1) / n
                variance += component
                df_denominator += component**2 / (n - 1)
        if not np.allclose(point, current.prevalence, atol=1e-12, rtol=0) or not np.allclose(
            variance, current.variance, atol=1e-12, rtol=0
        ):
            raise ValueError("Independent point/variance check failed")
        if stage == "B1":
            rmse = float(np.sqrt(np.mean((point - truth) ** 2)) * 100)
            if abs(rmse - simple["results"][f"{method}-b{budget}"]["rmse_pp"]) > 1e-10:
                raise ValueError("Independent RMSE check failed")
        else:
            df = np.divide(
                variance**2, df_denominator, out=np.full(1000, np.inf), where=df_denominator > 0
            )
            c = ci_lock["calibration"][f"{method}-fraction{fraction}"]["multiplier"]
            for key, radius in [
                ("student_t", t.ppf(0.975, df) * np.sqrt(variance)),
                (
                    "validation_calibrated",
                    c * np.sqrt(variance) if c is not None else np.full(1000, np.inf),
                ),
            ]:
                summary = ci["results"][f"{method}-b{budget}"]["intervals"][key]
                covered = float(np.mean(np.abs(point - truth) <= radius))
                if abs(covered - summary["coverage"]) > 1e-12:
                    raise ValueError("Independent coverage check failed")
                if (
                    summary["mean_width_pp"] is not None
                    and abs(float(radius.mean() * 200) - summary["mean_width_pp"]) > 1e-9
                ):
                    raise ValueError("Independent interval width check failed")
        checks.append({"stage": stage, "method": method, "budget": budget, "draws": 1000})
validation = pd.read_csv(ci_root / "validation-draw-results.csv")
val_ids = tuple(tables["static"].loc[tables["static"].split.eq("validation"), "record_id"])
val_refs = read_references(args.processed, val_ids)
val_truth = float(np.mean(list(val_refs.values())))
for (method, fraction), group in validation.groupby(["method", "fraction"]):
    errors = np.abs(group.prevalence.to_numpy() - val_truth)
    se = np.sqrt(group.variance.to_numpy())
    scores = np.divide(errors, se, out=np.full(len(errors), np.inf), where=se > 0)
    scores[(se == 0) & (errors <= 1e-14)] = 0
    rank = min(len(scores), int(np.ceil(0.95 * (len(scores) + 1))))
    multiplier = max(1.959963984540054, np.sort(scores)[rank - 1])
    recorded = ci_lock["calibration"][f"{method}-fraction{fraction}"]["multiplier"]
    if np.isfinite(multiplier) and abs(multiplier - recorded) > 1e-10:
        raise ValueError("Validation calibration multiplier changed")
evidence = {
    "status": "passed",
    "complete": True,
    "control_draws_independently_recomputed": 8000,
    "existing_test_interval_draws_recomputed": 8000,
    "validation_multiplier_draws_rechecked": 8000,
    "checks": checks,
    "main_result_unchanged": file_hash(args.main / "evaluation/result.json")
    == "b7dba06392233572b3d1a40a96d0c260f0a42d18d5827cbab35666e46a3aead9",
    "control_result_sha256": file_hash(simple_root / "result.json"),
    "coverage_result_sha256": file_hash(ci_root / "result.json"),
}
if not evidence["main_result_unchanged"]:
    raise ValueError("Original main result changed")
output.write_text(json.dumps(evidence, indent=2) + "\n")
print(
    "Independent controls, query streams, RMSEs, interval coverage/width "
    "and calibration checks passed."
)
