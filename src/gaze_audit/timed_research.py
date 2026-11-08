"""Registered development-only power weights and score-strata ablation."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .exact_intervals import stratified_binary_interval
from .extra_experiments import centered_moments, frozen_inputs
from .followups import evaluate_plans, load_main
from .frame_study import file_hash, make_design, read_references, save_queries, summarize_draws
from .frames import FrameOracle, integer_budget
from .strengthening import (
    FeaturePolicy,
    ratio_summary,
    replay_rng,
    sampled_components,
    verify_estimates,
    write_json,
)


def choose(candidates, field, reverse=False):
    minimum = min(c["validation_mse"] for c in candidates)
    tied = [c for c in candidates if c["validation_mse"] <= minimum * 1.01]
    return sorted(tied, key=lambda c: c[field], reverse=reverse)[0]


def run(config_path):
    started = time.monotonic()
    config_path = Path(config_path)
    cfg = json.loads(config_path.read_text())
    main, simple, processed = frozen_inputs(cfg)
    out = Path(cfg["output"])
    if out.exists():
        raise ValueError("Preserve existing run, use a new output version")
    _, _, tables, hashes = load_main(main, processed)
    out.mkdir(parents=True)
    registration = dict(
        config=cfg,
        config_sha256=file_hash(config_path),
        protocol_sha256=file_hash(Path(cfg["protocol"])),
        implementation_sha256=file_hash(Path(__file__)),
        feature_hashes=hashes,
        started_utc=datetime.now(timezone.utc).isoformat(),
    )
    write_json(out / "registration.json", registration)
    parts = {
        s: tables["static"][tables["static"].split.eq(s)].reset_index(drop=True)
        for s in ["train", "validation", "test"]
    }
    train = parts["train"]
    refs = read_references(processed, tuple(train.record_id))
    y = np.array([refs[k] for k in train.record_id])
    policies = {}
    for k in cfg["strata_counts"]:
        q = train.f_q.to_numpy(float)
        cuts = np.unique(np.quantile(q, np.arange(1, k) / k))
        cuts = cuts[cuts < q.max()]
        groups = np.searchsorted(cuts, q, side="left")
        sd, moments = centered_moments(y - q, groups, len(cuts) + 1)
        policies[f"K{k}"] = FeaturePolicy("f_q", cuts, sd)
        write_json(
            out / f"K{k}-training.json", dict(cuts=cuts.tolist(), sd=sd.tolist(), moments=moments)
        )
    original_lock = json.loads((simple / "policy-lock.json").read_text())
    original = original_lock["policies"]["q-quartiles"]
    assert np.allclose(policies["K4"].cut_points, original["cut_points"], rtol=0, atol=1e-12)
    assert np.allclose(policies["K4"].residual_sd, original["residual_sd"], rtol=0, atol=1e-12)
    frozen_alpha = original_lock["selected"]["q-quartiles"]["alpha"]
    val = parts["validation"]
    val_plans = []
    for name, policy in policies.items():
        for alpha in cfg["alphas"]:
            pop, counts = make_design(
                policy.strata(val), policy.residual_sd, integer_budget(0.1, len(val)), alpha
            )
            path = out / f"validation-{name}-a{alpha:g}.npz"
            sha = save_queries(path, pop, counts, cfg["validation_draws"], 100000, 1, 21)
            val_plans.append((name, alpha, pop, counts, path, sha))
    pop, counts = make_design(
        np.zeros(len(val), dtype=int), np.ones(1), integer_budget(0.1, len(val)), 0
    )
    path = out / "validation-uniform.npz"
    sha = save_queries(path, pop, counts, cfg["validation_draws"], 100000, 1, 1)
    val_plans.append(("uniform", 0, pop, counts, path, sha))
    # All development query streams exist before validation references are opened.
    val_refs = read_references(processed, tuple(val.record_id))
    vy = np.array([val_refs[k] for k in val.record_id], float)
    vq, truth = val.f_q.to_numpy(float), float(vy.mean())
    alpha_candidates, lambda_candidates = [], []
    for name, alpha, pop, counts, path, sha in val_plans:
        sample = np.load(path)["selected"]
        point, _, _, _ = sampled_components(sample, pop, counts, vq, vy)
        row = dict(
            policy=name,
            alpha=float(alpha),
            validation_mse=float(np.mean((point - truth) ** 2)),
            file=path.name,
            sha256=sha,
            counts=counts.tolist(),
        )
        if name != "uniform":
            alpha_candidates.append(row)
        if name == "uniform" or (name == "K4" and alpha == frozen_alpha):
            for weight in cfg["lambdas"]:
                point, _, _, _ = sampled_components(sample, pop, counts, vq * weight, vy)
                lambda_candidates.append(
                    dict(
                        row,
                        weight=float(weight),
                        validation_mse=float(np.mean((point - truth) ** 2)),
                    )
                )
    selected_alpha = {
        name: choose([c for c in alpha_candidates if c["policy"] == name], "alpha")
        for name in policies
    }
    # Numeric K tie order, rather than lexical K16 before K2.
    best = min(c["validation_mse"] for c in selected_alpha.values())
    selected_k = min(
        (c for c in selected_alpha.values() if c["validation_mse"] <= best * 1.01),
        key=lambda c: (int(c["policy"][1:]), c["alpha"]),
    )
    selected_lambda = {
        name: choose([c for c in lambda_candidates if c["policy"] == name], "weight", True)
        for name in ["uniform", "K4"]
    }
    lock = dict(
        alpha_candidates=alpha_candidates,
        lambda_candidates=lambda_candidates,
        selected_alpha=selected_alpha,
        selected_k=selected_k,
        selected_lambda=selected_lambda,
        frozen_q_alpha=frozen_alpha,
        test_used_for_selection=False,
        all_validation_plans_saved_before_references=True,
    )
    write_json(out / "policy-lock.json", lock)
    test = parts["test"]
    plans, manifest = [], []
    for bi, fraction in enumerate(cfg["fractions"]):
        budget = integer_budget(fraction, len(test))
        designs = [
            (name, p.strata(test), p.residual_sd, selected_alpha[name]["alpha"], 1.0, 21)
            for name, p in policies.items()
        ]
        designs += [
            (
                "power-score",
                policies["K4"].strata(test),
                policies["K4"].residual_sd,
                frozen_alpha,
                selected_lambda["K4"]["weight"],
                21,
            ),
            (
                "power-uniform",
                np.zeros(len(test), int),
                np.ones(1),
                0,
                selected_lambda["uniform"]["weight"],
                1,
            ),
        ]
        for name, groups, sd, alpha, weight, stream in designs:
            pop, counts = make_design(groups, sd, budget, alpha)
            path = out / f"queries-{name}-b{budget}.npz"
            sha = save_queries(path, pop, counts, cfg["test_draws"], 200000, bi, stream)
            row = dict(
                policy=name,
                budget=budget,
                budget_index=bi,
                stream=stream,
                weight=weight,
                alpha=alpha,
                file=path.name,
                sha256=sha,
                sizes=list(map(len, pop)),
                counts=counts.tolist(),
            )
            manifest.append(row)
            plans.append((row, pop, counts, path))
    write_json(out / "query-manifest.json", manifest)
    test[["record_id", "source_id"]].to_csv(out / "population_index.csv", index=False)
    refs = read_references(processed, tuple(test.record_id))
    ids = tuple(test.record_id)
    oracle = FrameOracle(refs, ids)
    y, q = np.array([refs[k] for k in ids], float), test.f_q.to_numpy(float)
    truth = float(y.mean())
    rows, summaries, checks = [], {}, []
    for row, pop, counts, path in plans:
        name, budget, weight = row["policy"], row["budget"], row["weight"]
        data, samples = evaluate_plans(ids, q * weight, pop, counts, path, oracle)
        replay_rng(samples, pop, counts, 200000, row["budget_index"], row["stream"])
        point, components, _, positive = sampled_components(samples, pop, counts, q * weight, y)
        check = verify_estimates(data, point, components)
        endpoints = np.array(
            [stratified_binary_interval(k, counts, list(map(len, pop))) for k in positive]
        )
        lower, upper = (
            np.rint(endpoints[:, 0] * len(y)).astype(int),
            np.rint(endpoints[:, 1] * len(y)).astype(int),
        )
        summary = summarize_draws(data, truth)
        summary["intervals"]["exact_binary_reference"] = dict(
            coverage=float(np.mean((lower <= y.sum()) & (upper >= y.sum()))),
            mean_width_pp=float(np.mean(upper - lower) / len(y) * 100),
            point_outside_rate=float(
                np.mean((point < endpoints[:, 0]) | (point > endpoints[:, 1]))
            ),
            centers_on_residual_estimate=False,
        )
        summaries[f"{name}-b{budget}"] = summary
        checks.append(dict(policy=name, budget=budget, **check))
        rows.append(data.assign(policy=name, budget=budget, lower_total=lower, upper_total=upper))
        print(
            f"{name} B{budget}: RMSE {summary['rmse_pp']:.6f} pp, "
            f"normal coverage {summary['intervals']['normal']['coverage']:.3f}",
            flush=True,
        )
        write_json(
            out / "status.json", dict(state="running", completed=len(rows), planned=len(plans))
        )
    data = pd.concat(rows, ignore_index=True)
    data.to_csv(out / "draw-results.csv", index=False)
    comparisons = {}
    main_draws = pd.read_csv(main / "evaluation/draw-results.csv")
    for budget in sorted(data.budget.unique()):
        base = data[(data.policy == "K4") & (data.budget == budget)].prevalence.to_numpy() - truth
        for name in ["K2", "K8", "K16", "power-score", "power-uniform"]:
            err = (
                data[(data.policy == name) & (data.budget == budget)].prevalence.to_numpy() - truth
            )
            comparisons[f"{name}-b{budget}/K4"] = ratio_summary(err, base, cfg)
        err = (
            data[(data.policy == "power-uniform") & (data.budget == budget)].prevalence.to_numpy()
            - truth
        )
        base = (
            main_draws[(main_draws.method == "M2") & (main_draws.budget == budget)]
            .sort_values("draw")
            .prevalence.to_numpy()
            - truth
        )
        comparisons[f"power-uniform-b{budget}/M2"] = ratio_summary(err, base, cfg)
    frozen_inputs(cfg)
    assert file_hash(Path(__file__)) == registration["implementation_sha256"]
    result = dict(
        complete=True,
        designation=cfg["designation"],
        reference_prevalence=truth,
        sampled_method_runs=len(data),
        results=summaries,
        comparisons=comparisons,
        selected_k=selected_k["policy"],
        selected_lambdas={k: v["weight"] for k, v in selected_lambda.items()},
        independent_checks=checks,
        elapsed_seconds=time.monotonic() - started,
        policy_lock_sha256=file_hash(out / "policy-lock.json"),
        registration_sha256=file_hash(out / "registration.json"),
        main_inputs_unchanged=True,
    )
    write_json(out / "result.json", result)
    write_json(out / "status.json", dict(state="completed", sampled_method_runs=len(data)))
    return result
