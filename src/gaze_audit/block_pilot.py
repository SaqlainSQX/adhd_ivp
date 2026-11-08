"""Uniform contiguous-block difference estimation at matched expected cost."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .followups import load_main
from .frame_study import file_hash, read_references
from .strengthening import ratio_summary, write_json


def partition(table, length):
    if length < 1 or len(table) == 0 or table.record_id.duplicated().any():
        raise ValueError("Require unique nonempty public records and positive length")
    keys = ["source_id", "clip_id", "person_a", "person_b"]
    frame = "clip_frame_index_1based"
    work = table[keys + [frame]].copy()
    work["position"] = np.arange(len(work))
    if work.duplicated(keys + [frame]).any():
        raise ValueError("Duplicate pair-frame geometry")
    work = work.sort_values(keys + [frame]).reset_index(drop=True)
    newrun = (
        work[keys].ne(work[keys].shift()).any(axis=1).to_numpy()
        | work[frame].diff().ne(1).to_numpy()
    )
    runstart = np.maximum.accumulate(np.where(newrun, np.arange(len(work)), 0))
    begin = newrun | ((np.arange(len(work)) - runstart) % length == 0)
    starts = np.flatnonzero(begin)
    canonical = np.cumsum(begin) - 1
    first = np.minimum.reduceat(work.position.to_numpy(), starts)
    order = np.argsort(first)
    inverse = np.empty(len(order), int)
    inverse[order] = np.arange(len(order))
    mapping = np.empty(len(work), int)
    mapping[work.position.to_numpy()] = inverse[canonical]
    costs = np.diff(np.r_[starts, len(work)])[order]
    assert np.array_equal(np.bincount(mapping), costs)
    assert costs.sum() == len(work) and costs.min() > 0 and costs.max() <= length
    stats = dict(
        blocks=len(costs),
        frames=len(work),
        contiguous_runs=int(newrun.sum()),
        mean_block_size=float(costs.mean()),
        partial_block_rate=float(np.mean(costs < length)),
        size_histogram={str(k): int(np.sum(costs == k)) for k in np.unique(costs)},
    )
    return mapping, costs, stats


def estimate_block_sample(q_total, residual_totals, selected, population_frames):
    count, size = len(selected), len(residual_totals)
    if count < 2 and count < size:
        raise ValueError("Noncensus needs at least two blocks")
    residual = np.asarray(residual_totals)[selected]
    point = (q_total + size / count * residual.sum()) / population_frames
    variance = (
        (size / population_frames) ** 2 * (1 - count / size) * residual.var(ddof=1) / count
        if count < size
        else 0.0
    )
    return float(point), float(variance)


def run(config_path):
    started = time.monotonic()
    config_path = Path(config_path)
    cfg = json.loads(config_path.read_text())
    main, out = Path(cfg["main"]), Path(cfg["output"])
    if out.exists():
        raise ValueError("Preserve prior outputs; use a new versioned run")
    assert file_hash(main / "evaluation/result.json") == cfg["main_result_sha256"]
    _, _, tables, hashes = load_main(main, Path(cfg["processed"]))
    out.mkdir(parents=True)
    reg = dict(
        config=cfg,
        config_sha256=file_hash(config_path),
        protocol_sha256=file_hash(Path(cfg["protocol"])),
        implementation_sha256=file_hash(Path(__file__)),
        feature_hashes=hashes,
        started_utc=datetime.now(timezone.utc).isoformat(),
    )
    write_json(out / "registration.json", reg)
    inventory, partitions = {}, {}
    for split in ["train", "validation", "test"]:
        table = tables["static"][tables["static"].split.eq(split)].reset_index(drop=True)
        for length in cfg["lengths"]:
            mapping, costs, stats = partition(table, length)
            inventory[f"{split}-L{length}"] = stats
            if split == "test":
                partitions[length] = (mapping, costs)
                np.savez_compressed(out / f"partition-L{length}.npz", mapping=mapping, costs=costs)
    write_json(out / "public-block-inventory.json", dict(labels_used=False, inventory=inventory))
    test = tables["static"][tables["static"].split.eq("test")].reset_index(drop=True)
    plans = []
    for length, (_mapping, costs) in partitions.items():
        size = len(costs)
        for bi, budget in enumerate(cfg["budgets"]):
            target = budget * size / len(test)
            lower = int(np.floor(target))
            fraction = float(target - lower)
            if lower < 2 and lower < size:
                raise ValueError("Expected budget cannot support block variance")
            selections = np.full((cfg["draws"], int(np.ceil(target))), -1, dtype=np.int32)
            counts = np.zeros(cfg["draws"], dtype=np.int32)
            stream = 1 if length == 1 else 41 + length
            for draw in range(cfg["draws"]):
                rng = np.random.default_rng(np.random.SeedSequence([200000 + draw, bi, stream]))
                n = lower + int(rng.random() < fraction) if fraction > 0 else lower
                selections[draw, :n] = rng.choice(size, size=n, replace=False)
                counts[draw] = n
            path = out / f"queries-L{length}-b{budget}.npz"
            np.savez_compressed(path, selected=selections, counts=counts)
            plans.append(
                dict(
                    length=length,
                    budget=budget,
                    budget_index=bi,
                    stream=stream,
                    target_blocks=target,
                    file=path.name,
                    sha256=file_hash(path),
                )
            )
    write_json(
        out / "query-lock.json",
        dict(new_sampling=True, plans=plans, all_saved_before_references=True),
    )
    refs = read_references(Path(cfg["processed"]), tuple(test.record_id))
    y = np.array([refs[k] for k in test.record_id], float)
    q = test.f_q.to_numpy(float)
    truth = float(y.mean())
    main_draws = pd.read_csv(main / "evaluation/draw-results.csv")
    rows, summaries, errors, checks = [], {}, {}, []
    for entry in plans:
        length, budget = entry["length"], entry["budget"]
        mapping, costs = partitions[length]
        size = len(costs)
        yb, qb = np.bincount(mapping, weights=y), np.bincount(mapping, weights=q)
        saved = np.load(out / entry["file"])
        sample, counts = saved["selected"], saved["counts"]
        realized = np.array([costs[s[:n]].sum() for s, n in zip(sample, counts, strict=True)])
        for weight in cfg["weights"]:
            residual = yb - weight * qb
            # Independently form residual block totals from original frame rows.
            order = np.argsort(mapping, kind="stable")
            starts = np.r_[0, np.cumsum(costs)[:-1]]
            independent_residual = np.add.reduceat((y - weight * q)[order], starts)
            assert np.allclose(residual, independent_residual, rtol=0, atol=1e-12)
            points, variances = [], []
            for draw, (selection, n) in enumerate(zip(sample, counts, strict=True)):
                selected = selection[:n]
                rng = np.random.default_rng(
                    np.random.SeedSequence([200000 + draw, entry["budget_index"], entry["stream"]])
                )
                low = int(np.floor(entry["target_blocks"]))
                fraction = entry["target_blocks"] - low
                expected_n = low + int(rng.random() < fraction) if fraction > 0 else low
                assert expected_n == n and np.array_equal(
                    selected, rng.choice(size, size=int(n), replace=False)
                )
                point, var = estimate_block_sample(weight * q.sum(), residual, selected, len(y))
                independent = independent_residual[selected]
                other_point = weight * q.mean() + size / len(y) * independent.mean()
                other_var = (
                    (size / len(y)) ** 2
                    * (1 - n / size)
                    * (np.sum(independent**2) - independent.sum() ** 2 / n)
                    / (n - 1)
                    / n
                    if n < size
                    else 0.0
                )
                assert abs(point - other_point) < 1e-12 and abs(var - other_var) < 1e-12
                points.append(point)
                variances.append(var)
            points, variances = np.array(points), np.array(variances)
            if length == 1 and weight == 1:
                baseline = main_draws[
                    (main_draws.method == "M2") & (main_draws.budget == budget)
                ].sort_values("draw")
                assert np.allclose(points, baseline.prevalence, rtol=0, atol=1e-12)
                original = np.load(main / f"evaluation/queries-uniform-b{budget}.npz")["selected"]
                assert np.array_equal(original, sample)
            target = entry["target_blocks"]
            low = int(np.floor(target))
            fraction = target - low
            factor = (1 - fraction) * (1 / low - 1 / size) + fraction * (1 / (low + 1) - 1 / size)
            exact = (size / len(y)) ** 2 * factor * float(residual.var(ddof=1))
            err = points - truth
            half = 1.959963984540054 * np.sqrt(variances)
            key = f"L{length}-w{weight:g}-b{budget}"
            summary = dict(
                rmse_pp=float(np.sqrt(np.mean(err**2)) * 100),
                bias_pp=float(err.mean() * 100),
                mae_pp=float(np.abs(err).mean() * 100),
                normal_coverage=float(np.mean(np.abs(err) <= half)),
                normal_width_pp=float(2 * half.mean() * 100),
                zero_variance_rate=float(np.mean(variances == 0)),
                expected_labels=float(target * costs.mean()),
                mean_labels=float(realized.mean()),
                realized_label_quantiles=np.quantile(realized, [0, 0.05, 0.5, 0.95, 1]).tolist(),
                excess_nominal_budget_rate=float(np.mean(realized > budget)),
                mean_queried_blocks=float(counts.mean()),
                exact_design_rmse_pp=float(np.sqrt(max(exact, 0)) * 100),
            )
            summaries[key], errors[key] = summary, err
            rows.append(
                pd.DataFrame(
                    dict(
                        length=length,
                        weight=weight,
                        budget=budget,
                        draw=np.arange(1000),
                        prevalence=points,
                        variance=variances,
                        labels=realized,
                        blocks=counts,
                    )
                )
            )
            checks.append(dict(setting=key, cases=1000, status="passed"))
            print(
                f"{key}: RMSE{summary['rmse_pp']:.5f}pp, labels mean{realized.mean():.2f}",
                flush=True,
            )
    pd.concat(rows, ignore_index=True).to_csv(out / "draw-results.csv", index=False)
    comparison = ratio_summary(errors["L5-w1-b1032"], errors["L1-w1-b1032"], cfg)
    comparison["scope"] = (
        "Fixed corpus and independently seeded lengths; not source-generalization uncertainty"
    )
    assert file_hash(Path(__file__)) == reg["implementation_sha256"]
    write_json(
        out / "result.json",
        dict(
            complete=True,
            designation=cfg["designation"],
            results=summaries,
            primary=comparison,
            method_draws=32000,
            checks=checks,
            reference_prevalence=truth,
            original_M2_reproduced=True,
            elapsed_seconds=time.monotonic() - started,
            registration_sha256=file_hash(out / "registration.json"),
        ),
    )
    write_json(
        out / "status.json",
        dict(
            state="completed",
            method_draws=32000,
            next="saved-output verification and report, then G2 registration",
        ),
    )
