"""Separate G2 public geometry, training, selection and all-draw verification."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from gaze_audit.block_guidance import expected_design
from gaze_audit.followups import load_frozen_policy, load_main
from gaze_audit.frame_study import file_hash, read_references
from gaze_audit.strengthening import write_json

config_path = Path("configs/block-guidance-g2-v1.json")
cfg = json.loads(config_path.read_text())
main, processed, out = [Path(cfg[k]) for k in ["main", "processed", "output"]]
destination = out / "independent-validation.json"
if destination.exists():
    raise ValueError("Preserve previous verification")
result = json.loads((out / "result.json").read_text())
reg = json.loads((out / "registration.json").read_text())
assert reg["config_sha256"] == file_hash(config_path)
assert reg["protocol_sha256"] == file_hash(Path(cfg["protocol"]))
assert reg["implementation_sha256"] == file_hash(Path("src/gaze_audit/block_guidance.py"))
assert result["complete"] and result["policy_lock_sha256"] == file_hash(out / "policy-lock.json")
lock, _, tables, _ = load_main(main, processed)
parts = {
    s: {k: t[t.split.eq(s)].reset_index(drop=True) for k, t in tables.items()}
    for s in ["train", "validation", "test"]
}
geometry = {}
public_checks = []
for split, part in parts.items():
    table = part["static"]
    frame_q = table.f_q.to_numpy(float)
    predictions = {"Q": frame_q}
    for name, feature in [("S", "static"), ("T", "temporal-w11")]:
        if split == "train":
            path = main / "development" / f"{feature}-oof-scores.npy"
            assert file_hash(path) == reg["oof_files"][str(path)]
            predictions[name] = np.load(path)
        else:
            predictions[name] = load_frozen_policy(main, feature, lock).scores(part[feature])
    refs = read_references(processed, tuple(table.record_id))
    frame_y = np.array([refs[k] for k in table.record_id], float)
    for length in cfg["lengths"]:
        saved = np.load(out / f"public-{split}-L{length}.npz")
        mapping, costs = saved["mapping"], saved["costs"]
        assert len(mapping) == len(table) and np.array_equal(np.bincount(mapping), costs)
        assert costs.min() >= 1 and costs.max() <= length and costs.sum() == len(table)
        if length == 1:
            assert np.array_equal(mapping, np.arange(len(table)))
        order = np.lexsort((table.clip_frame_index_1based.to_numpy(), mapping))
        same = np.diff(mapping[order]) == 0
        assert (np.diff(table.clip_frame_index_1based.to_numpy()[order])[same] == 1).all()
        for key in ["source_id", "clip_id", "person_a", "person_b"]:
            values = table[key].to_numpy()[order]
            assert (values[1:][same] == values[:-1][same]).all()
        qb = np.bincount(mapping, weights=frame_q)
        assert np.allclose(saved["qb"], qb, rtol=0, atol=1e-12)
        scores = {name: np.bincount(mapping, weights=p) for name, p in predictions.items()}
        for name, score in scores.items():
            assert np.allclose(saved[name], score, rtol=0, atol=1e-12)
        residual = np.add.reduceat((frame_y - frame_q)[order], np.r_[0, np.cumsum(costs)[:-1]])
        yb = np.bincount(mapping, weights=frame_y)
        geometry[(split, length)] = dict(
            scores=scores, costs=costs, qb=qb, yb=yb, residual=residual, truth=float(frame_y.mean())
        )
        public_checks.append(dict(split=split, length=length, status="passed"))
policies = json.loads((out / "training-policies.json").read_text())
for key, policy in policies.items():
    text, name = key.split("-")
    length = int(text[1:])
    geom = geometry[("train", length)]
    scores = geom["scores"][name]
    cuts = np.unique(np.quantile(scores, [0.25, 0.5, 0.75]))
    cuts = cuts[cuts < scores.max()]
    assert np.array_equal(cuts, policy["cuts"])
    groups = np.searchsorted(cuts, scores, side="left")
    global_var = geom["residual"].var(ddof=1)
    sd = []
    for h in range(len(cuts) + 1):
        values = geom["residual"][groups == h]
        df = max(len(values) - 1, 0)
        variance = values.var(ddof=1) if df else 0.0
        sd.append(max(np.sqrt((df * variance + 20 * global_var) / (df + 20)), 1e-6))
    assert np.allclose(sd, policy["sd"], rtol=0, atol=1e-12)


def design(split, length, name, budget, alpha):
    geom, policy = geometry[(split, length)], policies[f"L{length}-{name}"]
    groups = np.searchsorted(policy["cuts"], geom["scores"][name], side="left")
    return expected_design(groups, np.array(policy["sd"]), geom["costs"], budget, alpha)


def replay(split, length, name, path, sha, pop, targets, seed, bi, stream):
    assert file_hash(path) == sha
    saved = np.load(path)
    samples, counts = saved["selected"], saved["counts"]
    geom = geometry[(split, length)]
    costs, qb, residual = geom["costs"], geom["qb"], geom["residual"]
    mass = costs.sum()
    for draw, (padded, nrow) in enumerate(zip(samples, counts, strict=True)):
        rng = np.random.default_rng(np.random.SeedSequence([seed + draw, bi, stream]))
        chunks, numbers = [], []
        for p, t in zip(pop, targets, strict=True):
            lo = int(np.floor(t))
            f = t - lo
            n = lo + int(rng.random() < f) if f > 0 else lo
            chunks.append(rng.choice(p, size=n, replace=False))
            numbers.append(n)
        selected = np.concatenate(chunks)
        assert np.array_equal(nrow, numbers) and np.array_equal(padded[: len(selected)], selected)
        assert (padded[len(selected) :] == -1).all()
    points = np.full(len(samples), qb.sum() / mass)
    variance, radius = np.zeros(len(samples)), np.zeros(len(samples))
    realized, positive = np.zeros(len(samples)), np.zeros(len(samples))
    offsets = np.c_[np.zeros(len(samples), int), np.cumsum(counts, axis=1)]
    sizes = np.array([len(p) for p in pop])
    noncensus = np.sum(counts < sizes, axis=1)
    for h, p in enumerate(pop):
        for n in np.unique(counts[:, h]):
            rows = np.flatnonzero(counts[:, h] == n)
            positions = samples[rows[:, None], offsets[rows, h, None] + np.arange(n)[None, :]]
            assert np.isin(positions, p).all()
            observed = residual[positions]
            total = observed.sum(axis=1)
            points[rows] += len(p) / mass * total / n
            realized[rows] += costs[positions].sum(axis=1)
            positive[rows] += geom["yb"][positions].sum(axis=1)
            if n < len(p):
                sample_var = (np.sum(observed**2, axis=1) - total**2 / n) / (n - 1)
                variance[rows] += (len(p) / mass) ** 2 * (1 - n / len(p)) * sample_var / n
                public_range = (costs[p] - qb[p]).max() + qb[p].max()
                radius[rows] += (
                    len(p)
                    / mass
                    * public_range
                    * np.sqrt(np.log(2 * noncensus[rows] / 0.05) / (2 * n))
                )
    return dict(
        prevalence=points,
        variance=variance,
        normal_low=points - 1.959963984540054 * np.sqrt(np.maximum(variance, 0)),
        normal_high=points + 1.959963984540054 * np.sqrt(np.maximum(variance, 0)),
        bounded_low=np.maximum(0, points - radius),
        bounded_high=np.minimum(1, points + radius),
        labels=realized,
        blocks=counts.sum(axis=1),
        positives=positive,
    )


policy_lock = json.loads((out / "policy-lock.json").read_text())
val_checks = []
for candidate in policy_lock["candidates"]:
    length, name, alpha = candidate["length"], candidate["policy"], candidate["alpha"]
    pop, target, mean_cost = design("validation", length, name, 2514, alpha)
    assert np.allclose(target, candidate["targets"], rtol=0, atol=1e-12)
    values = replay(
        "validation",
        length,
        name,
        out / candidate["file"],
        candidate["sha256"],
        pop,
        target,
        100000,
        1,
        700 + 100 * length + cfg["policies"][name],
    )
    mse = np.mean((values["prevalence"] - geometry[("validation", length)]["truth"]) ** 2)
    assert abs(mse - candidate["validation_mse"]) < 1e-16
    val_checks.append(dict(length=length, policy=name, alpha=alpha, status="passed"))
for chosen in policy_lock["selected"].values():
    candidates = [
        c
        for c in policy_lock["candidates"]
        if c["length"] == chosen["length"] and c["policy"] == chosen["policy"]
    ]
    best = min(c["validation_mse"] for c in candidates)
    expected = min(
        (c for c in candidates if c["validation_mse"] <= best * 1.01), key=lambda c: c["alpha"]
    )
    assert expected == chosen
data = pd.read_csv(out / "draw-results.csv")
assert len(data) == 48000
checks = []
for entry in json.loads((out / "query-manifest.json").read_text())["plans"]:
    length, name, budget = entry["length"], entry["policy"], entry["budget"]
    pop, target, mean_cost = design("test", length, name, budget, entry["alpha"])
    assert np.allclose(target, entry["targets"], rtol=0, atol=1e-12)
    assert abs(target @ mean_cost - budget) < 1e-8
    values = replay(
        "test",
        length,
        name,
        out / entry["file"],
        entry["sha256"],
        pop,
        target,
        200000,
        entry["budget_index"],
        entry["stream"],
    )
    subset = data[
        (data.length == length) & (data.policy == name) & (data.budget == budget)
    ].sort_values("draw")
    assert np.array_equal(subset.draw, np.arange(1000))
    for column, expected in values.items():
        assert np.allclose(subset[column], expected, rtol=0, atol=1e-12), column
    s = result["results"][f"L{length}-{name}-b{budget}"]
    truth = geometry[("test", length)]["truth"]
    err = values["prevalence"] - truth
    assert abs(s["rmse_pp"] - np.sqrt(np.mean(err**2)) * 100) < 1e-10
    assert s["normal_coverage"] == float(
        np.mean((subset.normal_low <= truth) & (subset.normal_high >= truth))
    )
    assert s["bounded_coverage"] == float(
        np.mean((subset.bounded_low <= truth) & (subset.bounded_high >= truth))
    )
    assert abs(s["mean_labels"] - np.mean(values["labels"])) < 1e-10
    checks.append(dict(length=length, policy=name, budget=budget, draws=1000, status="passed"))
    print(f"Verified L{length}-{name} B{budget}", flush=True)
for key, c in result["comparisons"].items():
    if key.endswith("-T/S"):
        text, btext, _ = key.split("-")
        length, budget = int(text[1:]), int(btext[1:])
        a = data[(data.length == length) & (data.policy == "T") & (data.budget == budget)]
        b = data[(data.length == length) & (data.policy == "S") & (data.budget == budget)]
    else:
        left, right = key.split("/")
        text, name, btext = left.split("-")
        length, budget = int(text[1:]), int(btext[1:])
        a = data[(data.length == length) & (data.policy == name) & (data.budget == budget)]
        b = data[
            (data.length == (length if right == "Q" else 1))
            & (data.policy == ("Q" if right == "Q" else name))
            & (data.budget == budget)
        ]
    ae = (a.sort_values("draw").prevalence.to_numpy() - result["reference_prevalence"]) ** 2
    be = (b.sort_values("draw").prevalence.to_numpy() - result["reference_prevalence"]) ** 2
    index = np.random.default_rng(400008).integers(1000, size=(2000, 1000))
    ratios = np.sqrt(ae[index].mean(axis=1) / be[index].mean(axis=1))
    assert abs(np.sqrt(ae.mean() / be.mean()) - c["rmse_ratio"]) < 1e-10
    assert np.allclose(
        np.quantile(ratios, [0.025, 0.975]), c["draw_bootstrap_95pct"], rtol=0, atol=1e-10
    )
write_json(
    destination,
    dict(
        status="passed",
        method_draws=len(data),
        validation_candidate_draws=3600,
        public_checks=public_checks,
        validation_checks=val_checks,
        checks=checks,
        bootstrap_comparisons=len(result["comparisons"]),
        result_sha256=file_hash(out / "result.json"),
        policy_lock_sha256=file_hash(out / "policy-lock.json"),
    ),
)
print("G2 all 48000 test and 3600 validation cases passed independent verification.")
