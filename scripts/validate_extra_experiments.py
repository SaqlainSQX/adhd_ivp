"""Independent round-C query, estimator, interval, selection and cost verification."""

import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from gaze_audit.exact_intervals import stratified_binary_interval
from gaze_audit.followups import load_main
from gaze_audit.frame_study import file_hash, make_design, read_references
from gaze_audit.strengthening import FeaturePolicy, write_json

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--config", type=Path, default=Path("configs/extra-experiments-c-v1.json"))
args = parser.parse_args()
config = json.loads(args.config.read_text())
main, simple, processed, root = [
    Path(config[k]) for k in ["main_run", "simple_run", "processed", "output"]
]
destination = root / "independent-validation.json"
if destination.exists():
    parser.error("Preserve previous verification evidence")
_, main_result, tables, _ = load_main(main, processed)
val = {k: t[t.split.eq("validation")].reset_index(drop=True) for k, t in tables.items()}
test = {k: t[t.split.eq("test")].reset_index(drop=True) for k, t in tables.items()}
train = tables["static"][tables["static"].split.eq("train")].reset_index(drop=True)
ids, val_ids = tuple(test["static"].record_id), tuple(val["static"].record_id)
refs, val_refs = read_references(processed, ids), read_references(processed, val_ids)
y, q = np.array([refs[k] for k in ids]), test["static"].f_q.to_numpy()
val_y, val_q = np.array([val_refs[k] for k in val_ids]), val["static"].f_q.to_numpy()
truth, val_truth = float(y.mean()), float(val_y.mean())
checks, validation_checks, training_checks = [], [], []


def independent_samples(
    path, expected_sha, populations, counts, seed_start, budget_index, stream, surrogate, labels
):
    if file_hash(path) != expected_sha:
        raise ValueError("Saved query hash changed")
    saved = np.load(path)
    samples = saved["selected"]
    if not np.array_equal(saved["counts"], counts) or samples.shape[1] != sum(counts):
        raise ValueError("Saved allocation or exact budget changed")
    if (np.diff(np.sort(samples, axis=1), axis=1) == 0).any():
        raise ValueError("Repeated query within a draw")
    for draw, row in enumerate(samples):
        rng = np.random.default_rng(
            np.random.SeedSequence([seed_start + draw, budget_index, stream])
        )
        expected = np.concatenate(
            [
                rng.choice(p, size=int(n), replace=False)
                for p, n in zip(populations, counts, strict=True)
            ]
        )
        if not np.array_equal(row, expected):
            raise ValueError("Independent RNG replay failed")
    point, variance = np.full(len(samples), surrogate.mean()), np.zeros(len(samples))
    radius = 0.0
    edges = np.r_[0, np.cumsum(counts)]
    successes = []
    for h, population in enumerate(populations):
        position = samples[:, edges[h] : edges[h + 1]]
        if not np.isin(position, population).all():
            raise ValueError("Query outside the frozen stratum")
        n, size = int(counts[h]), len(population)
        residuals = labels[position] - surrogate[position]
        point += size / len(labels) * residuals.mean(axis=1)
        successes.append(labels[position].sum(axis=1))
        if n < size:
            variance += (
                (size / len(labels)) ** 2 * (1 - n / size) * residuals.var(axis=1, ddof=1) / n
            )
            public_q = surrogate[list(population)]
            residual_range = float((1 - public_q).max() + public_q.max())
            radius += (
                size
                / len(labels)
                * residual_range
                * np.sqrt(np.log(2 * len(populations) / 0.05) / (2 * n))
            )
    return point, variance, np.stack(successes, axis=1), radius


for stage in ["C1-ridge", "C2-label-cost", "C3-squared-rf"]:
    folder = root / stage
    report = json.loads((folder / "result.json").read_text())
    registration = json.loads((folder / "registration.json").read_text())
    lock_path = folder / "policy-lock.json"
    lock = json.loads(lock_path.read_text())
    if (
        not report["complete"]
        or file_hash(lock_path) != report["policy_lock_sha256"]
        or file_hash(folder / "registration.json") != report["registration_sha256"]
    ):
        raise ValueError("Registered experiment evidence changed or incomplete")
    if registration["implementation_sha256"] != file_hash(
        Path("src/gaze_audit/extra_experiments.py")
    ):
        raise ValueError("Registered implementation changed")
    policies = {}
    for name, artifact in lock["models"].items():
        if "model_file" in artifact:
            path = folder / artifact["model_file"]
            if file_hash(path) != artifact["model_sha256"]:
                raise ValueError("Fitted model hash changed")
            policies[name] = joblib.load(path)
        else:
            path = folder / artifact["policy_file"]
            if file_hash(path) != artifact["policy_sha256"]:
                raise ValueError("Score-moment policy hash changed")
            spec = json.loads(path.read_text())
            policies[name] = FeaturePolicy(
                spec["feature"], np.array(spec["cut_points"]), np.array(spec["residual_sd"])
            )
    if stage == "C2-label-cost":
        seen = set()
        for entry in json.loads((folder / "training-query-manifest.json").read_text()):
            path = folder / entry["file"]
            if file_hash(path) != entry["sha256"]:
                raise ValueError("Training-label subset changed")
            actual = set(pd.read_csv(path).record_id)
            expected = set()
            for source, group in train.groupby("source_id", sort=True):
                ordered = np.sort(group.record_id.to_numpy())
                source_seed = int(hashlib.sha256(str(source).encode()).hexdigest()[:8], 16)
                rng = np.random.default_rng(np.random.SeedSequence([710000, source_seed]))
                count = max(1, int(np.floor(entry["fraction"] * len(ordered) + 0.5)))
                expected.update(ordered[rng.permutation(len(ordered))][:count])
            if actual != expected or not seen <= actual or len(actual) != entry["selected_labels"]:
                raise ValueError("Source-nested training selection is not reproducible")
            seen = actual
            training_checks.append(
                {"policy": entry["policy"], "training_labels": len(actual), "status": "passed"}
            )
    # Recompute every validation candidate from saved plans before checking its selection.
    for candidate in lock["candidates"]:
        name = candidate["policy"]
        policy, feature = policies[name], lock["feature_sets"][name]
        groups = policy.strata(val[feature])
        populations, counts = make_design(
            groups, policy.residual_sd, candidate["budget"], candidate["alpha"]
        )
        stream = config["streams"]["cost-curve" if stage == "C2-label-cost" else name]
        point, _, _, _ = independent_samples(
            folder / candidate["query_file"],
            candidate["query_sha256"],
            populations,
            counts,
            100000,
            1,
            stream,
            val_q,
            val_y,
        )
        mse = float(np.mean((point - val_truth) ** 2))
        if abs(mse - candidate["validation_mse"]) > 1e-12:
            raise ValueError("Independent validation candidate MSE mismatch")
        validation_checks.append({"policy": name, "alpha": candidate["alpha"], "draws": len(point)})
    for name in policies:
        candidates = [c for c in lock["candidates"] if c["policy"] == name]
        best = min(c["validation_mse"] for c in candidates)
        chosen = min(
            (c for c in candidates if c["validation_mse"] <= best * 1.01), key=lambda c: c["alpha"]
        )
        if lock["selected"][name] != chosen:
            raise ValueError("Validation-only alpha selection does not reproduce")
    draws = pd.read_csv(folder / "draw-results.csv")
    manifest = json.loads((folder / "query-manifest.json").read_text())
    for entry in manifest:
        name, budget = entry["policy"], entry["budget"]
        policy = policies[name]
        feature = lock["feature_sets"][name]
        populations, counts = make_design(
            policy.strata(test[feature]),
            policy.residual_sd,
            budget,
            lock["selected"][name]["alpha"],
        )
        if counts.tolist() != entry["counts"] or list(map(len, populations)) != entry["sizes"]:
            raise ValueError("Saved test allocation differs from policy lock")
        point, variance, successes, radius = independent_samples(
            folder / entry["file"],
            entry["sha256"],
            populations,
            counts,
            200000,
            entry["budget_index"],
            entry["stream"],
            q,
            y,
        )
        data = draws[(draws.policy == name) & (draws.budget == budget)].sort_values("draw")
        if len(data) != 1000 or not data.labels_revealed.eq(budget).all():
            raise ValueError("Incomplete draw grid or wrong label cost")
        if not np.allclose(point, data.prevalence, rtol=0, atol=1e-12) or not np.allclose(
            variance, data.variance, rtol=0, atol=1e-12
        ):
            raise ValueError("Independent point/variance recomputation failed")
        half = 1.959963984540054 * np.sqrt(variance)
        for expected, column in [
            (point - half, "normal_low"),
            (point + half, "normal_high"),
            (np.maximum(0, point - radius), "bounded_low"),
            (np.minimum(1, point + radius), "bounded_high"),
        ]:
            if not np.allclose(expected, data[column], rtol=0, atol=1e-12):
                raise ValueError("Independent original interval recomputation failed")
        endpoints = np.array(
            [stratified_binary_interval(k, counts, list(map(len, populations))) for k in successes]
        )
        lower_total, upper_total = (
            np.rint(endpoints[:, 0] * len(ids)).astype(int),
            np.rint(endpoints[:, 1] * len(ids)).astype(int),
        )
        if not np.array_equal(lower_total, data.lower_total) or not np.array_equal(
            upper_total, data.upper_total
        ):
            raise ValueError("Exact binary reference totals changed")
        summary = report["results"][f"{name}-b{budget}"]
        rmse = float(np.sqrt(np.mean((point - truth) ** 2)) * 100)
        if abs(rmse - summary["rmse_pp"]) > 1e-10:
            raise ValueError("Independent RMSE summary failed")
        normal_covered = np.abs(point - truth) <= half
        if abs(normal_covered.mean() - summary["intervals"]["normal"]["coverage"]) > 1e-12:
            raise ValueError("Independent normal coverage mismatch")
        exact_covered = (lower_total <= int(y.sum())) & (upper_total >= int(y.sum()))
        exact = summary["intervals"]["exact_binary_reference"]
        if (
            abs(exact_covered.mean() - exact["coverage"]) > 1e-12
            or abs(np.mean(endpoints[:, 1] - endpoints[:, 0]) * 100 - exact["mean_width_pp"])
            > 1e-10
        ):
            raise ValueError("Exact binary reference aggregate mismatch")
        checks.append(
            {"stage": stage, "policy": name, "budget": budget, "draws": len(data), "rmse_pp": rmse}
        )
    print(
        f"Independently validated {stage}: {report['sampled_method_runs']} test evaluations",
        flush=True,
    )
paths = {
    "main_result": main / "evaluation/result.json",
    "main_policy_lock": main / "development/policy-lock.json",
    "simple_result": simple / "result.json",
    "simple_policy_lock": simple / "policy-lock.json",
    "source_folds": processed / "development_folds.csv",
}
if any(file_hash(path) != config["frozen_hashes"][name] for name, path in paths.items()):
    raise ValueError("An accepted frozen baseline input changed")
write_json(
    destination,
    {
        "status": "passed",
        "complete": True,
        "test_evaluations_recomputed": sum(c["draws"] for c in checks),
        "validation_evaluations_recomputed": sum(c["draws"] for c in validation_checks),
        "test_checks": checks,
        "validation_checks": validation_checks,
        "source_nested_training_checks": training_checks,
        "frozen_baselines_unchanged": True,
        "validator_sha256": file_hash(Path(__file__)),
    },
)
print(destination)
