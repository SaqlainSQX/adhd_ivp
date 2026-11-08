"""Separate all-draw verification of the registered D round."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from gaze_audit.exact_intervals import stratified_binary_interval
from gaze_audit.extra_experiments import frozen_inputs
from gaze_audit.followups import load_main
from gaze_audit.frame_study import file_hash, make_design, read_references
from gaze_audit.strengthening import write_json

cfg_path = Path("configs/timed-research-d-v1.json")
cfg = json.loads(cfg_path.read_text())
main, simple, processed = frozen_inputs(cfg)
root = Path(cfg["output"])
if (root / "independent-validation.json").exists():
    raise ValueError("Preserve previous verification")
registration = json.loads((root / "registration.json").read_text())
assert registration["config_sha256"] == file_hash(cfg_path)
assert registration["protocol_sha256"] == file_hash(Path(cfg["protocol"]))
assert registration["implementation_sha256"] == file_hash(Path("src/gaze_audit/timed_research.py"))
result = json.loads((root / "result.json").read_text())
assert result["complete"] and result["policy_lock_sha256"] == file_hash(root / "policy-lock.json")
lock = json.loads((root / "policy-lock.json").read_text())
_, _, tables, _ = load_main(main, processed)
parts = {
    s: tables["static"][tables["static"].split.eq(s)].reset_index(drop=True)
    for s in ["train", "validation", "test"]
}
labels = {}
for s, table in parts.items():
    refs = read_references(processed, tuple(table.record_id))
    labels[s] = np.array([refs[k] for k in table.record_id], float)
policies = {}
training_checks = []
for k in cfg["strata_counts"]:
    policy = json.loads((root / f"K{k}-training.json").read_text())
    q = parts["train"].f_q.to_numpy(float)
    cuts = np.unique(np.quantile(q, np.arange(1, k) / k))
    cuts = cuts[cuts < q.max()]
    assert np.array_equal(cuts, policy["cuts"])
    groups = np.searchsorted(cuts, q, side="left")
    residual = labels["train"] - q
    global_var = residual.var(ddof=1)
    sd = []
    for h in range(len(cuts) + 1):
        values = residual[groups == h]
        df = max(len(values) - 1, 0)
        within = values.var(ddof=1) if df else 0.0
        sd.append(max(np.sqrt((df * within + 20 * global_var) / (df + 20)), 1e-6))
    assert np.allclose(sd, policy["sd"], rtol=0, atol=1e-14)
    policies[f"K{k}"] = (cuts, np.array(sd))
    training_checks.append(dict(policy=f"K{k}", status="passed"))


def design(name, split, budget, alpha):
    table = parts[split]
    if name == "uniform" or name == "power-uniform":
        groups, sd = np.zeros(len(table), int), np.ones(1)
    else:
        cuts, sd = policies["K4" if name == "power-score" else name]
        groups = np.searchsorted(cuts, table.f_q.to_numpy(), side="left")
    return make_design(groups, sd, budget, alpha)


def recompute(path, sha, pop, counts, split, weight, bi, stream):
    assert file_hash(path) == sha
    saved = np.load(path)
    samples = saved["selected"]
    assert np.array_equal(saved["counts"], counts)
    assert samples.shape == (1000, int(sum(counts)))
    assert not (np.diff(np.sort(samples, axis=1), axis=1) == 0).any()
    start = 100000 if split == "validation" else 200000
    for d, row in enumerate(samples):
        rng = np.random.default_rng(np.random.SeedSequence([start + d, bi, stream]))
        expected = np.concatenate(
            [rng.choice(p, size=int(n), replace=False) for p, n in zip(pop, counts, strict=True)]
        )
        assert np.array_equal(row, expected)
    q = parts[split].f_q.to_numpy(float) * weight
    y = labels[split]
    point, variance = np.full(1000, q.mean()), np.zeros(1000)
    radius, offset, positives = 0.0, 0, []
    for p, n in zip(pop, counts, strict=True):
        positions = samples[:, offset : offset + n]
        assert np.isin(positions, p).all()
        r = y[positions] - q[positions]
        size = len(p)
        point += size / len(y) * r.mean(axis=1)
        positives.append(y[positions].sum(axis=1))
        if n < size:
            variance += (size / len(y)) ** 2 * (1 - n / size) * r.var(axis=1, ddof=1) / n
            scores = q[list(p)]
            radius += (
                size
                / len(y)
                * (1 - scores.min() + scores.max())
                * np.sqrt(np.log(2 * len(pop) / 0.05) / (2 * n))
            )
        offset += n
    return point, variance, radius, np.stack(positives, axis=1)


validation_checks = []
for candidate in lock["alpha_candidates"] + lock["lambda_candidates"]:
    name = candidate["policy"]
    pop, counts = design(name, "validation", 2514, candidate["alpha"])
    p, _, _, _ = recompute(
        root / candidate["file"],
        candidate["sha256"],
        pop,
        counts,
        "validation",
        candidate.get("weight", 1.0),
        1,
        1 if name == "uniform" else 21,
    )
    mse = float(np.mean((p - labels["validation"].mean()) ** 2))
    assert abs(mse - candidate["validation_mse"]) < 1e-16
    validation_checks.append(
        dict(
            policy=name,
            alpha=candidate["alpha"],
            weight=candidate.get("weight", 1.0),
            status="passed",
        )
    )
for name, chosen in lock["selected_alpha"].items():
    candidates = [c for c in lock["alpha_candidates"] if c["policy"] == name]
    best = min(c["validation_mse"] for c in candidates)
    expected = min(
        (c for c in candidates if c["validation_mse"] <= best * 1.01), key=lambda c: c["alpha"]
    )
    assert chosen == expected
for name, chosen in lock["selected_lambda"].items():
    candidates = [c for c in lock["lambda_candidates"] if c["policy"] == name]
    best = min(c["validation_mse"] for c in candidates)
    expected = max(
        (c for c in candidates if c["validation_mse"] <= best * 1.01), key=lambda c: c["weight"]
    )
    assert chosen == expected
best = min(c["validation_mse"] for c in lock["selected_alpha"].values())
assert lock["selected_k"] == min(
    (c for c in lock["selected_alpha"].values() if c["validation_mse"] <= best * 1.01),
    key=lambda c: (int(c["policy"][1:]), c["alpha"]),
)
data = pd.read_csv(root / "draw-results.csv")
checks = []
for row in json.loads((root / "query-manifest.json").read_text()):
    name, budget = row["policy"], row["budget"]
    pop, counts = design(name, "test", budget, row["alpha"])
    assert list(map(len, pop)) == row["sizes"] and counts.tolist() == row["counts"]
    assert sum(counts) == budget
    point, var, radius, positive = recompute(
        root / row["file"],
        row["sha256"],
        pop,
        counts,
        "test",
        row["weight"],
        row["budget_index"],
        row["stream"],
    )
    subset = data[(data.policy == name) & (data.budget == budget)].sort_values("draw")
    assert np.array_equal(subset.draw, np.arange(1000))
    for col, expected in [
        ("prevalence", point),
        ("variance", var),
        ("normal_low", point - 1.959963984540054 * np.sqrt(var)),
        ("normal_high", point + 1.959963984540054 * np.sqrt(var)),
        ("bounded_low", np.maximum(0, point - radius)),
        ("bounded_high", np.minimum(1, point + radius)),
    ]:
        assert np.allclose(subset[col], expected, rtol=0, atol=1e-12), col
    endpoints = np.array(
        [stratified_binary_interval(k, counts, list(map(len, pop))) for k in positive]
    )
    integer = np.rint(endpoints * len(labels["test"])).astype(int)
    assert np.array_equal(integer[:, 0], subset.lower_total) and np.array_equal(
        integer[:, 1], subset.upper_total
    )
    summary = result["results"][f"{name}-b{budget}"]
    err = point - labels["test"].mean()
    assert abs(summary["rmse_pp"] - np.sqrt(np.mean(err**2)) * 100) < 1e-10
    normal_cov = float(
        np.mean(
            (subset.normal_low <= labels["test"].mean())
            & (subset.normal_high >= labels["test"].mean())
        )
    )
    assert summary["intervals"]["normal"]["coverage"] == normal_cov
    exact_cov = float(
        np.mean((integer[:, 0] <= labels["test"].sum()) & (integer[:, 1] >= labels["test"].sum()))
    )
    assert summary["intervals"]["exact_binary_reference"]["coverage"] == exact_cov
    checks.append(
        dict(
            policy=name,
            budget=budget,
            draws=len(subset),
            status="passed",
            max_point_difference=float(np.max(np.abs(point - subset.prevalence))),
        )
    )
    print(f"Verified {name} B{budget}: 1000 draws", flush=True)
frozen_inputs(cfg)
write_json(
    root / "independent-validation.json",
    dict(
        status="passed",
        sampled_method_runs=len(data),
        training_checks=training_checks,
        validation_checks=validation_checks,
        checks=checks,
        result_sha256=file_hash(root / "result.json"),
        policy_lock_sha256=file_hash(root / "policy-lock.json"),
    ),
)
