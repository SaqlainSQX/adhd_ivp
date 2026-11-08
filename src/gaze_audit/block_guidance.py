"""Registered G2 frozen OOF score aggregation and expected-cost block sampling."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .block_pilot import partition
from .extra_experiments import centered_moments
from .followups import choose_alpha, load_frozen_policy, load_main
from .frame_study import file_hash, read_references
from .policy import _continuous_counts
from .strengthening import ratio_summary, write_json


def expected_design(groups, sd, costs, budget, mix):
    groups, costs = np.asarray(groups), np.asarray(costs, float)
    present = np.unique(groups)
    populations = [np.flatnonzero(groups == h) for h in present]
    sizes = np.array([len(p) for p in populations])
    mean_cost = np.array([costs[p].mean() for p in populations])
    uniform = _continuous_counts(sizes.astype(float), sizes, mean_cost, budget)
    active = _continuous_counts(
        sizes * np.asarray(sd)[present] / np.sqrt(mean_cost), sizes, mean_cost, budget
    )
    targets = (1 - mix) * uniform + mix * active
    if abs(targets @ mean_cost - budget) > 1e-8 or np.any(targets < np.minimum(sizes, 2)):
        raise ValueError("Invalid expected-cost allocation")
    return populations, targets, mean_cost


def draw_selections(populations, targets, rng):
    selected, counts = [], []
    for pop, target in zip(populations, targets, strict=True):
        low = int(np.floor(target))
        fraction = float(target - low)
        n = low + int(rng.random() < fraction) if fraction > 0 else low
        selected.extend(rng.choice(pop, size=n, replace=False))
        counts.append(n)
    return np.array(selected, dtype=np.int32), np.array(counts, dtype=np.int32)


def save_plan(path, populations, targets, draws, seed, bi, stream):
    selected = np.full((draws, int(np.ceil(targets).sum())), -1, dtype=np.int32)
    counts = np.zeros((draws, len(targets)), dtype=np.int32)
    for draw in range(draws):
        rng = np.random.default_rng(np.random.SeedSequence([seed + draw, bi, stream]))
        row, n = draw_selections(populations, targets, rng)
        selected[draw, : len(row)], counts[draw] = row, n
    np.savez_compressed(path, selected=selected, counts=counts)
    return file_hash(path)


def block_estimate(qb, yb, costs, populations, selected, counts, alpha=0.05):
    mass = float(np.sum(costs))
    point = float(np.sum(qb) / mass)
    variance, radius = 0.0, 0.0
    noncensus = sum(n < len(p) for p, n in zip(populations, counts, strict=True))
    offset = 0
    for pop, n in zip(populations, counts, strict=True):
        positions = selected[offset : offset + n]
        if len(positions) != n or not np.isin(positions, pop).all():
            raise ValueError("Query outside its frozen stratum")
        residual = yb[positions] - qb[positions]
        size = len(pop)
        point += size / mass * float(residual.mean())
        if n < size:
            if n < 2:
                raise ValueError("Noncensus needs two blocks")
            variance += (size / mass) ** 2 * (1 - n / size) * float(residual.var(ddof=1)) / n
            envelope = float(np.max(costs[pop] - qb[pop]) + np.max(qb[pop]))
            radius += size / mass * envelope * np.sqrt(np.log(2 * noncensus / alpha) / (2 * n))
        offset += n
    if offset != len(selected) or len(np.unique(selected)) != len(selected):
        raise ValueError("Duplicate or extra queries")
    half = 1.959963984540054 * np.sqrt(variance)
    low, high = max(0.0, point - radius), min(1.0, point + radius)
    return dict(
        prevalence=point,
        variance=variance,
        normal_low=float(point - half),
        normal_high=float(point + half),
        bounded_low=float(low),
        bounded_high=float(high),
        bounded_empty=bool(low > high),
        labels=int(costs[selected].sum()),
        blocks=len(selected),
        positives=int(yb[selected].sum()),
    )


def evaluate(path, populations, targets, qb, yb, costs, residual_independent, seed, bi, stream):
    saved = np.load(path)
    rows = []
    max_point, max_var = 0.0, 0.0
    for draw, (padded, counts) in enumerate(zip(saved["selected"], saved["counts"], strict=True)):
        selected = padded[: counts.sum()]
        rng = np.random.default_rng(np.random.SeedSequence([seed + draw, bi, stream]))
        expected, n = draw_selections(populations, targets, rng)
        if not np.array_equal(expected, selected) or not np.array_equal(n, counts):
            raise ValueError("Query RNG replay mismatch")
        result = block_estimate(qb, yb, costs, populations, selected, counts)
        # Different construction: inverse-inclusion block weights and sum/squares.
        weights = np.empty(len(qb))
        independent_var, offset = 0.0, 0
        for pop, n in zip(populations, counts, strict=True):
            weights[pop] = len(pop) / n
            positions = selected[offset : offset + n]
            r = residual_independent[positions]
            if n < len(pop):
                sample_var = (np.sum(r * r) - np.sum(r) ** 2 / n) / (n - 1)
                independent_var += (
                    (len(pop) / costs.sum()) ** 2 * (1 - n / len(pop)) * sample_var / n
                )
            offset += n
        independent_point = (
            qb.sum() + np.dot(weights[selected], residual_independent[selected])
        ) / costs.sum()
        max_point = max(max_point, abs(independent_point - result["prevalence"]))
        max_var = max(max_var, abs(independent_var - result["variance"]))
        if max(max_point, max_var) > 1e-12:
            raise ValueError("Independent point/variance check failed")
        rows.append(dict(draw=draw, **result))
    return pd.DataFrame(rows), dict(
        status="passed",
        draws=len(rows),
        max_point_difference=float(max_point),
        max_variance_difference=float(max_var),
    )


def exact_variance(populations, targets, residual, mass):
    value = 0.0
    for pop, target in zip(populations, targets, strict=True):
        size = len(pop)
        if size == 1:
            continue
        low = int(np.floor(target))
        fraction = target - low
        coefficient = (1 - fraction) * (1 / low - 1 / size) + fraction * (1 / (low + 1) - 1 / size)
        value += (size / mass) ** 2 * coefficient * residual[pop].var(ddof=1)
    return float(value)


def run(config_path):
    started = time.monotonic()
    config_path = Path(config_path)
    cfg = json.loads(config_path.read_text())
    main, processed, pilot, out = [Path(cfg[k]) for k in ["main", "processed", "pilot", "output"]]
    if out.exists():
        raise ValueError("Preserve evidence; use a new versioned output")
    assert file_hash(main / "evaluation/result.json") == cfg["main_result_sha256"]
    assert file_hash(main / "development/policy-lock.json") == cfg["main_policy_lock_sha256"]
    lock, _, tables, hashes = load_main(main, processed)
    assert json.loads((pilot / "result.json").read_text())["complete"]
    source_folds = pd.read_csv(processed / "development_folds.csv").set_index("source_id").fold
    assert (
        file_hash(processed / "development_folds.csv")
        == "68b0f7db3b0ec3fa0069d11a4ca4554031c40e0c48f3c57896e252bd1c566029"
    )
    parts = {
        s: {k: t[t.split.eq(s)].reset_index(drop=True) for k, t in tables.items()}
        for s in ["train", "validation", "test"]
    }
    framescores = {s: {"Q": part["static"].f_q.to_numpy(float)} for s, part in parts.items()}
    frozen = {}
    for name, feature in [("S", "static"), ("T", "temporal-w11")]:
        model = load_frozen_policy(main, feature, lock)
        path = main / "development" / f"{feature}-oof-scores.npy"
        oof = np.load(path)
        assert oof.shape == (len(parts["train"]["static"]),) and np.isfinite(oof).all()
        frozen[str(path)] = file_hash(path)
        framescores["train"][name] = oof
        for s in ["validation", "test"]:
            framescores[s][name] = model.scores(parts[s][feature])
    out.mkdir(parents=True)
    registration = dict(
        config=cfg,
        config_sha256=file_hash(config_path),
        protocol_sha256=file_hash(Path(cfg["protocol"])),
        implementation_sha256=file_hash(Path(__file__)),
        feature_hashes=hashes,
        model_hashes=lock["model_hashes"],
        oof_files=frozen,
        source_folds_sha256=file_hash(processed / "development_folds.csv"),
        pilot_result_sha256=file_hash(pilot / "result.json"),
        started_utc=datetime.now(timezone.utc).isoformat(),
    )
    write_json(out / "registration.json", registration)
    write_json(out / "status.json", dict(state="running", stage="block training summaries"))
    geometry = {}
    for s, part in parts.items():
        frame = part["static"]
        for length in cfg["lengths"]:
            mapping, costs, stats = partition(frame, length)
            if s == "test":
                original = np.load(pilot / f"partition-L{length}.npz")
                assert np.array_equal(mapping, original["mapping"]) and np.array_equal(
                    costs, original["costs"]
                )
            groups_by_block = pd.DataFrame(
                dict(block=mapping, source=frame.source_id, fold=frame.source_id.map(source_folds))
            )
            assert groups_by_block.groupby("block").source.nunique().max() == 1
            if s == "train":
                assert set(groups_by_block.fold) == set(range(5))
                assert groups_by_block.groupby("block").fold.nunique().max() == 1
            scores = {
                name: np.bincount(mapping, weights=values)
                for name, values in framescores[s].items()
            }
            qb = np.bincount(mapping, weights=frame.f_q.to_numpy(float))
            geometry[(s, length)] = dict(
                mapping=mapping, costs=costs, qb=qb, scores=scores, stats=stats
            )
            np.savez_compressed(
                out / f"public-{s}-L{length}.npz", mapping=mapping, costs=costs, qb=qb, **scores
            )
    train = parts["train"]["static"]
    refs = read_references(processed, tuple(train.record_id))
    train_y = np.array([refs[k] for k in train.record_id], float)
    policies = {}
    for length in cfg["lengths"]:
        geom = geometry[("train", length)]
        yb = np.bincount(geom["mapping"], weights=train_y)
        residual = yb - geom["qb"]
        for name, score in geom["scores"].items():
            cuts = np.unique(np.quantile(score, [0.25, 0.5, 0.75]))
            cuts = cuts[cuts < score.max()]
            groups = np.searchsorted(cuts, score, side="left")
            sd, moments = centered_moments(residual, groups, len(cuts) + 1)
            policies[(length, name)] = dict(cuts=cuts.tolist(), sd=sd.tolist(), moments=moments)
            if length == 1 and name in ["S", "T"]:
                original = load_frozen_policy(
                    main, "static" if name == "S" else "temporal-w11", lock
                )
                assert np.allclose(cuts, original.cut_points, rtol=0, atol=1e-12)
                assert np.allclose(sd, original.residual_sd, rtol=0, atol=1e-12)
    write_json(
        out / "training-policies.json",
        {f"L{length}-{name}": policy for (length, name), policy in policies.items()},
    )

    def design(s, length, name, budget, alpha):
        geom, policy = geometry[(s, length)], policies[(length, name)]
        groups = np.searchsorted(policy["cuts"], geom["scores"][name], side="left")
        return expected_design(groups, np.array(policy["sd"]), geom["costs"], budget, alpha)

    candidates, plans = [], []
    for length, name in policies:
        for alpha in cfg["alphas"]:
            pop, target, mean_cost = design(
                "validation", length, name, cfg["validation_budget"], alpha
            )
            stream = 700 + 100 * length + cfg["policies"][name]
            path = out / f"validation-L{length}-{name}-a{alpha:g}.npz"
            sha = save_plan(path, pop, target, cfg["validation_draws"], 100000, 1, stream)
            plans.append((length, name, alpha, pop, target, path, sha, stream))
    val = parts["validation"]["static"]
    refs = read_references(processed, tuple(val.record_id))
    vy = np.array([refs[k] for k in val.record_id], float)
    val_truth = float(vy.mean())
    for length, name, alpha, pop, target, path, sha, stream in plans:
        geom = geometry[("validation", length)]
        yb = np.bincount(geom["mapping"], weights=vy)
        order = np.argsort(geom["mapping"], kind="stable")
        starts = np.r_[0, np.cumsum(geom["costs"])[:-1]]
        independent = np.add.reduceat((vy - val.f_q.to_numpy())[order], starts)
        data, check = evaluate(
            path, pop, target, geom["qb"], yb, geom["costs"], independent, 100000, 1, stream
        )
        candidates.append(
            dict(
                length=length,
                policy=name,
                alpha=float(alpha),
                validation_mse=float(np.mean((data.prevalence - val_truth) ** 2)),
                file=path.name,
                sha256=sha,
                targets=target.tolist(),
                sizes=list(map(len, pop)),
                check=check,
            )
        )
    selected = {
        (length, name): choose_alpha(
            [c for c in candidates if c["length"] == length and c["policy"] == name]
        )
        for length, name in policies
    }
    write_json(
        out / "policy-lock.json",
        dict(
            candidates=candidates,
            selected={
                f"L{length}-{name}": candidate for (length, name), candidate in selected.items()
            },
            test_used=False,
        ),
    )
    manifests, testplans = [], []
    for bi, budget in enumerate(cfg["budgets"]):
        for length, name in policies:
            alpha = selected[(length, name)]["alpha"]
            pop, target, mean_cost = design("test", length, name, budget, alpha)
            path = out / f"queries-L{length}-{name}-b{budget}.npz"
            stream = 700 + 100 * length + cfg["policies"][name]
            sha = save_plan(path, pop, target, 1000, 200000, bi, stream)
            entry = dict(
                length=length,
                policy=name,
                budget=budget,
                budget_index=bi,
                stream=stream,
                alpha=alpha,
                file=path.name,
                sha256=sha,
                targets=target.tolist(),
                sizes=list(map(len, pop)),
                mean_costs=mean_cost.tolist(),
            )
            manifests.append(entry)
            testplans.append((entry, pop, target, path))
    write_json(out / "query-manifest.json", dict(plans=manifests, all_saved_before_references=True))
    test = parts["test"]["static"]
    refs = read_references(processed, tuple(test.record_id))
    ty = np.array([refs[k] for k in test.record_id], float)
    truth = float(ty.mean())
    rows, summaries, checks, errors = [], {}, [], {}
    for entry, pop, target, path in testplans:
        length, name, budget = entry["length"], entry["policy"], entry["budget"]
        geom = geometry[("test", length)]
        yb = np.bincount(geom["mapping"], weights=ty)
        order = np.argsort(geom["mapping"], kind="stable")
        starts = np.r_[0, np.cumsum(geom["costs"])[:-1]]
        independent = np.add.reduceat((ty - test.f_q.to_numpy())[order], starts)
        data, check = evaluate(
            path,
            pop,
            target,
            geom["qb"],
            yb,
            geom["costs"],
            independent,
            200000,
            entry["budget_index"],
            entry["stream"],
        )
        err = data.prevalence.to_numpy() - truth
        summary = dict(
            rmse_pp=float(np.sqrt(np.mean(err**2)) * 100),
            bias_pp=float(err.mean() * 100),
            mae_pp=float(np.abs(err).mean() * 100),
            mean_labels=float(data.labels.mean()),
            expected_labels=float(np.dot(target, entry["mean_costs"])),
            label_quantiles=np.quantile(data.labels, [0, 0.05, 0.5, 0.95, 1]).tolist(),
            excess_budget_rate=float(np.mean(data.labels > budget)),
            mean_blocks=float(data.blocks.mean()),
            zero_variance_rate=float(np.mean(data.variance == 0)),
            normal_coverage=float(
                np.mean((data.normal_low <= truth) & (data.normal_high >= truth))
            ),
            normal_width_pp=float(np.mean(data.normal_high - data.normal_low) * 100),
            bounded_coverage=float(
                np.mean((data.bounded_low <= truth) & (data.bounded_high >= truth))
            ),
            bounded_width_pp=float(np.mean(data.bounded_high - data.bounded_low) * 100),
            bounded_empty_rate=float(data.bounded_empty.mean()),
            exact_design_rmse_pp=float(
                np.sqrt(max(exact_variance(pop, target, yb - geom["qb"], len(ty)), 0)) * 100
            ),
        )
        key = f"L{length}-{name}-b{budget}"
        summaries[key], errors[key] = summary, err
        checks.append(dict(setting=key, **check))
        rows.append(data.assign(length=length, policy=name, budget=budget))
        write_json(
            out / "status.json",
            dict(state="running", stage="test evaluation", completed=len(rows), planned=48),
        )
        print(
            f"{key}: RMSE{summary['rmse_pp']:.5f}pp, "
            f"normal coverage{summary['normal_coverage']:.3f}",
            flush=True,
        )
    data = pd.concat(rows, ignore_index=True)
    data.to_csv(out / "draw-results.csv", index=False)
    comparisons = {}
    for length in cfg["lengths"]:
        for budget in cfg["budgets"]:
            comparisons[f"L{length}-b{budget}-T/S"] = ratio_summary(
                errors[f"L{length}-T-b{budget}"], errors[f"L{length}-S-b{budget}"], cfg
            )
            for name in cfg["policies"]:
                comparisons[f"L{length}-{name}-b{budget}/Q"] = ratio_summary(
                    errors[f"L{length}-{name}-b{budget}"], errors[f"L{length}-Q-b{budget}"], cfg
                )
                comparisons[f"L{length}-{name}-b{budget}/L1"] = ratio_summary(
                    errors[f"L{length}-{name}-b{budget}"], errors[f"L1-{name}-b{budget}"], cfg
                )
    assert file_hash(Path(__file__)) == registration["implementation_sha256"]
    for path, sha in frozen.items():
        assert file_hash(Path(path)) == sha
    assert file_hash(main / "evaluation/result.json") == cfg["main_result_sha256"]
    write_json(
        out / "result.json",
        dict(
            complete=True,
            designation=cfg["designation"],
            results=summaries,
            comparisons=comparisons,
            primary=comparisons["L5-b1032-T/S"],
            method_draws=len(data),
            validation_candidates=len(candidates),
            checks=checks,
            reference_prevalence=truth,
            policy_lock_sha256=file_hash(out / "policy-lock.json"),
            registration_sha256=file_hash(out / "registration.json"),
            elapsed_seconds=time.monotonic() - started,
            no_new_models=True,
        ),
    )
    write_json(
        out / "status.json",
        dict(
            state="completed",
            method_draws=len(data),
            next="independent saved-output and selection verification, figure QA",
        ),
    )
