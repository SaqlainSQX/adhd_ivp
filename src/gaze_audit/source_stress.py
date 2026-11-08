"""Frozen-query, known-size domain estimation and source sensitivity."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .followups import load_main
from .frame_study import file_hash, make_design, read_references
from .strengthening import ratio_summary, replay_rng, write_json


def domain_draws(q, y, mask, populations, counts, samples):
    q, y, mask = np.asarray(q), np.asarray(y), np.asarray(mask, dtype=bool)
    size = int(mask.sum())
    if not size:
        raise ValueError("Empty domain")
    residual = (y - q) * mask
    point = np.full(len(samples), q[mask].sum() / size)
    variance, queries = np.zeros(len(samples)), np.zeros(len(samples), dtype=int)
    exact, offset = 0.0, 0
    for pop, n in zip(populations, counts, strict=True):
        positions = samples[:, offset : offset + n]
        r = residual[positions]
        nh = len(pop)
        point += nh / size * r.mean(axis=1)
        factor = (nh / size) ** 2 * (1 - n / nh) / n
        if n < nh:
            variance += factor * r.var(axis=1, ddof=1)
            exact += factor * residual[list(pop)].var(ddof=1)
        queries += mask[positions].sum(axis=1)
        offset += n
    return point, variance, float(exact), queries


def run(config_path):
    started = time.monotonic()
    config_path = Path(config_path)
    cfg = json.loads(config_path.read_text())
    root, out = Path(cfg["input"]), Path(cfg["output"])
    if out.exists():
        raise ValueError("Preserve previous run; use a new version")
    assert file_hash(root / "result.json") == cfg["input_result_sha256"]
    check = json.loads((root / "independent-validation.json").read_text())
    assert check["status"] == "passed" and check["result_sha256"] == cfg["input_result_sha256"]
    _, _, tables, hashes = load_main(Path(cfg["main"]), Path(cfg["processed"]))
    table = tables["static"][tables["static"].split.eq("test")].reset_index(drop=True)
    out.mkdir(parents=True)
    registration = dict(
        config=cfg,
        config_sha256=file_hash(config_path),
        protocol_sha256=file_hash(Path(cfg["protocol"])),
        implementation_sha256=file_hash(Path(__file__)),
        started_utc=datetime.now(timezone.utc).isoformat(),
        feature_hashes=hashes,
        input_draws_sha256=file_hash(root / "draw-results.csv"),
        input_queries_sha256=file_hash(root / "query-manifest.json"),
    )
    write_json(out / "registration.json", registration)
    refs = read_references(Path(cfg["processed"]), tuple(table.record_id))
    y = np.array([refs[k] for k in table.record_id], float)
    q = table.f_q.to_numpy(float)
    aliases = {source: f"S{i + 1:02d}" for i, source in enumerate(sorted(table.source_id.unique()))}
    write_json(out / "source-alias-map.json", {str(k): v for k, v in aliases.items()})
    sources = table.source_id.map(aliases).to_numpy()
    domains = [("all", "all", np.ones(len(table), bool))]
    for alias in aliases.values():
        mask = sources == alias
        domains += [("source", alias, mask), ("leave-out", alias, ~mask)]
    policy = json.loads((root / "K4-training.json").read_text())
    groups = np.searchsorted(policy["cuts"], q, side="left")
    full = pd.read_csv(root / "draw-results.csv")
    summaries, raw, checks = {}, {}, []
    for row in json.loads((root / "query-manifest.json").read_text()):
        if row["policy"] not in cfg["policies"]:
            continue
        name, budget = row["policy"], row["budget"]
        path = root / row["file"]
        assert file_hash(path) == row["sha256"]
        samples = np.load(path)["selected"]
        pop, counts = make_design(groups, np.array(policy["sd"]), budget, row["alpha"])
        replay_rng(samples, pop, counts, 200000, row["budget_index"], row["stream"])
        # Independent inverse-inclusion weights, not the domain helper's mean loop.
        weights = np.zeros(len(table))
        for p, n in zip(pop, counts, strict=True):
            weights[list(p)] = len(p) / n
        sampled_weighted = (y[samples] - row["weight"] * q[samples]) * weights[samples]
        totals = {}
        for kind, alias, mask in domains:
            size = int(mask.sum())
            point, var, exact, queries = domain_draws(
                q * row["weight"], y, mask, pop, counts, samples
            )
            independent = (
                row["weight"] * q[mask].sum() + (sampled_weighted * mask[samples]).sum(axis=1)
            ) / size
            assert np.allclose(point, independent, rtol=0, atol=1e-12)
            independent_var = np.zeros(len(samples))
            offset = 0
            for p, n in zip(pop, counts, strict=True):
                positions = samples[:, offset : offset + n]
                r = (y[positions] - row["weight"] * q[positions]) * mask[positions]
                if n < len(p):
                    centered = (np.sum(r * r, axis=1) - np.sum(r, axis=1) ** 2 / n) / (n - 1)
                    independent_var += (len(p) / size) ** 2 * (1 - n / len(p)) * centered / n
                offset += n
            assert np.allclose(var, independent_var, rtol=0, atol=1e-12)
            totals[(kind, alias)] = point * size
            truth = float(y[mask].mean())
            err = point - truth
            low, high = (
                point - 1.959963984540054 * np.sqrt(var),
                point + 1.959963984540054 * np.sqrt(var),
            )
            summary = dict(
                size=size,
                positives=int(y[mask].sum()),
                truth=truth,
                rmse_pp=float(np.sqrt(np.mean(err**2)) * 100),
                bias_pp=float(err.mean() * 100),
                mae_pp=float(np.abs(err).mean() * 100),
                exact_design_rmse_pp=float(np.sqrt(exact) * 100),
                normal_coverage=float(np.mean((low <= truth) & (high >= truth))),
                normal_width_pp=float(np.mean(high - low) * 100),
                mean_queries=float(queries.mean()),
                zero_query_rate=float(np.mean(queries == 0)),
                zero_variance_rate=float(np.mean(var == 0)),
            )
            summaries[f"{name}-b{budget}-{kind}-{alias}"] = summary
            raw[(name, budget, kind, alias)] = pd.DataFrame(
                dict(
                    draw=np.arange(len(samples)),
                    policy=name,
                    budget=budget,
                    kind=kind,
                    source=alias,
                    prevalence=point,
                    variance=var,
                    queries=queries,
                    truth=truth,
                )
            )
        actual = full[(full.policy == name) & (full.budget == budget)].sort_values("draw")
        assert np.allclose(totals[("all", "all")] / len(y), actual.prevalence, rtol=0, atol=1e-12)
        assert np.allclose(
            sum(totals[("source", a)] for a in aliases.values()),
            totals[("all", "all")],
            rtol=0,
            atol=1e-10,
        )
        for alias in aliases.values():
            assert np.allclose(
                totals[("source", alias)] + totals[("leave-out", alias)],
                totals[("all", "all")],
                rtol=0,
                atol=1e-10,
            )
        checks.append(
            dict(
                policy=name,
                budget=budget,
                domains=len(domains),
                draws=len(samples),
                status="passed",
            )
        )
        print(f"{name} B{budget}: all21 domains checked", flush=True)
    comparisons = {}
    for budget in cfg["budgets"]:
        for kind, alias, _ in domains:
            a = raw[("power-score", budget, kind, alias)]
            b = raw[("K4", budget, kind, alias)]
            ae, be = (
                a.prevalence.to_numpy() - a.truth.to_numpy(),
                b.prevalence.to_numpy() - b.truth.to_numpy(),
            )
            if np.mean(be**2) == 0:
                value = dict(
                    rmse_ratio=None, status="both-zero" if np.mean(ae**2) == 0 else "zero-baseline"
                )
            else:
                value = ratio_summary(ae, be, cfg)
                value["scope"] = (
                    "Fixed-corpus paired saved-draw Monte Carlo uncertainty; no source resampling"
                )
            comparisons[f"b{budget}-{kind}-{alias}"] = value
    pd.concat(raw.values(), ignore_index=True).to_csv(out / "domain-draw-results.csv", index=False)
    result = dict(
        complete=True,
        designation=cfg["designation"],
        summaries=summaries,
        comparisons=comparisons,
        domain_method_draws=sum(len(x) for x in raw.values()),
        new_queries=0,
        policy_changes=False,
        checks=checks,
        elapsed_seconds=time.monotonic() - started,
        registration_sha256=file_hash(out / "registration.json"),
    )
    assert file_hash(Path(__file__)) == registration["implementation_sha256"]
    assert file_hash(root / "result.json") == cfg["input_result_sha256"]
    write_json(out / "result.json", result)
    write_json(
        out / "status.json",
        dict(state="completed", domain_method_draws=result["domain_method_draws"]),
    )
    return result
