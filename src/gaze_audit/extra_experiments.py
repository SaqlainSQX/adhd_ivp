"""Bounded registered alternatives; the accepted course benchmark is immutable."""

import hashlib
import json
import platform
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from .exact_intervals import stratified_binary_interval
from .followups import choose_alpha, evaluate_plans, load_main
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


def comparison_ratio(numerator, denominator, config):
    result = ratio_summary(numerator, denominator, config)
    result["scope"] = (
        "Monte Carlo uncertainty on fixed corpus; aligned draw IDs and registered streams"
    )
    return result


@dataclass
class ExtraPolicy:
    model: object
    feature_columns: tuple[str, ...]
    cut_points: np.ndarray
    residual_sd: np.ndarray
    learner: str
    target: str

    def scores(self, table):
        return self.model.predict(table[list(self.feature_columns)].to_numpy(float))

    def strata(self, table):
        return np.searchsorted(self.cut_points, self.scores(table), side="left")


def centered_moments(residual, groups, count):
    residual, groups = np.asarray(residual, dtype=float), np.asarray(groups)
    global_var = float(np.var(residual, ddof=1))
    sd, rows = [], []
    for h in range(count):
        values = residual[groups == h]
        df = max(len(values) - 1, 0)
        within = float(np.var(values, ddof=1)) if df else 0.0
        value = max(float(np.sqrt((df * within + 20 * global_var) / (df + 20))), 1e-6)
        sd.append(value)
        rows.append(
            {
                "stratum": h,
                "training_labels": len(values),
                "centered_signed_residual_variance": within,
                "shrunk_sd": value,
            }
        )
    return np.asarray(sd), rows


def fresh_model(learner):
    if learner == "ridge":
        return make_pipeline(
            StandardScaler(), Ridge(alpha=1.0, fit_intercept=True, solver="cholesky")
        )
    if learner == "squared-rf":
        return RandomForestRegressor(
            n_estimators=64, max_depth=4, min_samples_leaf=100, random_state=42, n_jobs=1
        )
    raise ValueError("Unregistered learner")


def fit_extra_policy(table, labels, folds, learner, progress=None):
    columns = tuple(c for c in table if c.startswith("f_"))
    x, y, folds = table[list(columns)].to_numpy(float), np.asarray(labels), np.asarray(folds)
    if (
        len(x) < 2
        or not columns
        or not np.isfinite(x).all()
        or not np.isin(y, [0, 1]).all()
        or y.shape != (len(x),)
        or folds.shape != (len(x),)
        or set(folds) != set(range(5))
    ):
        raise ValueError(
            "Require finite features, binary labels and all five original source folds"
        )
    source_folds = pd.DataFrame({"source": table.source_id, "fold": folds})
    if source_folds.groupby("source").fold.nunique().max() != 1:
        raise ValueError("An original source crosses training folds")
    residual = y.astype(float) - table.f_q.to_numpy(float)
    target = residual if learner == "ridge" else residual**2
    oof, history = np.empty(len(x)), []
    started = time.monotonic()
    with threadpool_limits(limits=1):
        for fold in range(5):
            held = folds == fold
            model = fresh_model(learner).fit(x[~held], target[~held])
            oof[held] = model.predict(x[held])
            record = {
                "fold": fold,
                "training_rows": int((~held).sum()),
                "held_rows": int(held.sum()),
                "elapsed_seconds": time.monotonic() - started,
            }
            history.append(record)
            if progress:
                progress(record)
        cuts = np.unique(np.quantile(oof, [0.25, 0.5, 0.75]))
        cuts = cuts[cuts < oof.max()]
        groups = np.searchsorted(cuts, oof, side="left")
        sd, moments = centered_moments(residual, groups, len(cuts) + 1)
        final = fresh_model(learner).fit(x, target)
    policy = ExtraPolicy(
        final,
        columns,
        cuts,
        sd,
        learner,
        "signed residual y-q" if learner == "ridge" else "squared residual (y-q)^2",
    )
    diagnostics = {
        "learner": learner,
        "target": policy.target,
        "feature_columns": list(columns),
        "cuts": cuts.tolist(),
        "residual_sd": sd.tolist(),
        "allocation_moments_use_centered_signed_residuals": True,
        "moments": moments,
        "folds": history,
        "scaling_inside_each_training_fold": learner == "ridge",
        "cpu_threads": 1,
        "fit_elapsed_seconds": time.monotonic() - started,
    }
    return policy, diagnostics, oof


def nested_source_subset(table, fraction, seed=710000):
    if not 0 < fraction <= 1 or table.record_id.duplicated().any():
        raise ValueError("Require a unique public population and fraction in (0,1]")
    selected, counts = set(), []
    for source, group in table.groupby("source_id", sort=True):
        ids = np.sort(group.record_id.to_numpy())
        source_seed = int(hashlib.sha256(str(source).encode("utf-8")).hexdigest()[:8], 16)
        rng = np.random.default_rng(np.random.SeedSequence([seed, source_seed]))
        permutation = ids[rng.permutation(len(ids))]
        count = max(1, int(np.floor(fraction * len(ids) + 0.5)))
        selected.update(permutation[:count])
        counts.append({"source_id": str(source), "public_rows": len(ids), "selected_labels": count})
    return np.flatnonzero(table.record_id.isin(selected)), counts


def frozen_inputs(config):
    main, simple, processed = (
        Path(config["main_run"]),
        Path(config["simple_run"]),
        Path(config["processed"]),
    )
    paths = {
        "main_result": main / "evaluation/result.json",
        "main_policy_lock": main / "development/policy-lock.json",
        "simple_result": simple / "result.json",
        "simple_policy_lock": simple / "policy-lock.json",
        "source_folds": processed / "development_folds.csv",
    }
    for name, path in paths.items():
        if file_hash(path) != config["frozen_hashes"][name]:
            raise ValueError(f"Frozen input changed: {name}")
    return main, simple, processed


def run_stage(config_path, stage):
    if stage not in ["C1-ridge", "C2-label-cost", "C3-squared-rf"]:
        raise ValueError("Unregistered stage")
    started = time.monotonic()
    config_path = Path(config_path)
    config = json.loads(config_path.read_text())
    main, simple, processed = frozen_inputs(config)
    output = Path(config["output"]) / stage
    if output.exists():
        raise ValueError("Preserve previous outputs; choose a new versioned run")
    lock, main_result, tables, hashes = load_main(main, processed)
    output.mkdir(parents=True)
    registration = {
        "stage": stage,
        "designation": config["designation"],
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "config": config,
        "config_sha256": file_hash(config_path),
        "protocol_sha256": file_hash(Path(config["protocol"])),
        "implementation_sha256": file_hash(Path(__file__)),
        "feature_hashes": hashes,
        "exact_interval_implementation_sha256": file_hash(
            Path(__file__).parent / "exact_intervals.py"
        ),
        "runtime": {
            "python": platform.python_version(),
            **{
                p: version(p) for p in ["numpy", "pandas", "scipy", "scikit-learn", "threadpoolctl"]
            },
        },
    }
    write_json(output / "registration.json", registration)
    training = {k: t[t.split.eq("train")].reset_index(drop=True) for k, t in tables.items()}
    validation = {k: t[t.split.eq("validation")].reset_index(drop=True) for k, t in tables.items()}
    testing = {k: t[t.split.eq("test")].reset_index(drop=True) for k, t in tables.items()}
    policies, artifacts, features, costs = {}, {}, {}, {}
    if stage != "C2-label-cost":
        train_ids = tuple(training["static"].record_id)
        refs = read_references(processed, train_ids)
        labels = np.array([refs[k] for k in train_ids])
        source_folds = pd.read_csv(processed / "development_folds.csv").set_index("source_id").fold
        learner = "ridge" if stage == "C1-ridge" else "squared-rf"
        for feature_set in ["static", "temporal-w11"]:
            name = f"{learner}-{feature_set}"

            def progress(row, name=name):
                write_json(
                    output / "fit-progress.json",
                    {"model": name, **row, "updated_utc": datetime.now(timezone.utc).isoformat()},
                )
                print(
                    f"{stage} {name}: fold {row['fold']} "
                    f"completed at {row['elapsed_seconds']:.1f}s",
                    flush=True,
                )

            print(f"Fitting {name}; original five source folds, one CPU thread", flush=True)
            policy, diagnostic, oof = fit_extra_policy(
                training[feature_set],
                labels,
                training[feature_set].source_id.map(source_folds),
                learner,
                progress,
            )
            model_path = output / f"{name}.joblib"
            joblib.dump(policy, model_path)
            np.save(output / f"{name}-oof.npy", oof)
            write_json(output / f"{name}-development.json", diagnostic)
            artifacts[name] = {
                "model_file": model_path.name,
                "model_sha256": file_hash(model_path),
                "development_file": f"{name}-development.json",
                "development_sha256": file_hash(output / f"{name}-development.json"),
            }
            policies[name], features[name], costs[name] = policy, feature_set, len(train_ids)
    else:
        public = training["static"]
        reference = json.loads((simple / "policy-lock.json").read_text())["policies"]["q-quartiles"]
        cuts = np.array(reference["cut_points"])
        subsets, subset_manifest = {}, []
        for fraction in config["training_label_fractions"]:
            name = f"score-labels-{fraction:g}"
            positions, source_counts = nested_source_subset(
                public, fraction, config["training_subset_seed"]
            )
            path = output / f"{name}-training-queries.csv"
            public.iloc[positions][["record_id", "source_id"]].to_csv(path, index=False)
            subsets[name] = positions
            subset_manifest.append(
                {
                    "policy": name,
                    "fraction": fraction,
                    "selected_labels": len(positions),
                    "file": path.name,
                    "sha256": file_hash(path),
                    "source_counts": source_counts,
                }
            )
        write_json(output / "training-query-manifest.json", subset_manifest)
        # Every source-nested training-label selection exists before any is queried.
        for name, positions in subsets.items():
            selected = public.iloc[positions]
            ids = tuple(selected.record_id)
            refs = read_references(processed, ids)
            residual = np.array([refs[k] for k in ids]) - selected.f_q.to_numpy()
            groups = np.searchsorted(cuts, selected.f_q.to_numpy(), side="left")
            sd, moment_rows = centered_moments(residual, groups, len(cuts) + 1)
            if name == "score-labels-1" and not np.allclose(
                sd, reference["residual_sd"], rtol=0, atol=1e-12
            ):
                raise ValueError("Full-label score moments do not reproduce frozen B1")
            policy = FeaturePolicy("f_q", cuts.copy(), sd)
            path = output / f"{name}-policy.json"
            write_json(
                path,
                {
                    **policy.as_dict(),
                    "moments": moment_rows,
                    "training_labels": len(ids),
                    "training_fraction": float(name.rsplit("-", 1)[1]),
                },
            )
            artifacts[name] = {"policy_file": path.name, "policy_sha256": file_hash(path)}
            policies[name], features[name], costs[name] = policy, "static", len(ids)
    candidates, val_plans = [], []
    val_ids = tuple(validation["static"].record_id)
    for name, policy in policies.items():
        stream = config["streams"]["cost-curve" if stage == "C2-label-cost" else name]
        for alpha in config["alphas"]:
            pop, counts = make_design(
                policy.strata(validation[features[name]]),
                policy.residual_sd,
                integer_budget(0.1, len(val_ids)),
                alpha,
            )
            path = output / f"validation-{name}-alpha{alpha:g}.npz"
            sha = save_queries(
                path,
                pop,
                counts,
                config["validation_draws"],
                config["validation_seed_start"],
                1,
                stream,
            )
            val_plans.append((name, alpha, pop, counts, path, sha))
    val_refs = read_references(processed, val_ids)
    val_oracle, val_truth = FrameOracle(val_refs, val_ids), float(np.mean(list(val_refs.values())))
    for name, alpha, pop, counts, path, sha in val_plans:
        data, _ = evaluate_plans(
            val_ids, validation["static"].f_q.to_numpy(), pop, counts, path, val_oracle
        )
        candidates.append(
            {
                "policy": name,
                "alpha": float(alpha),
                "validation_mse": float(np.mean((data.prevalence - val_truth) ** 2)),
                "query_file": path.name,
                "query_sha256": sha,
                "budget": int(sum(counts)),
                "draws": len(data),
            }
        )
    selected = {
        name: choose_alpha([c for c in candidates if c["policy"] == name]) for name in policies
    }
    policy_lock = {
        "stage": stage,
        "models": artifacts,
        "feature_sets": features,
        "candidates": candidates,
        "selected": selected,
        "training_labels": costs,
        "validation_labels_reused": len(val_ids),
        "test_references_used_for_selection": False,
        "all_validation_plans_saved_before_query": True,
    }
    write_json(output / "policy-lock.json", policy_lock)
    ids = tuple(testing["static"].record_id)
    testing["static"][["record_id", "source_id"]].to_csv(
        output / "population_index.csv", index=False
    )
    manifest, designs = [], []
    for bi, fraction in enumerate(config["fractions"]):
        budget = integer_budget(fraction, len(ids))
        for name, policy in policies.items():
            stream = config["streams"]["cost-curve" if stage == "C2-label-cost" else name]
            pop, counts = make_design(
                policy.strata(testing[features[name]]),
                policy.residual_sd,
                budget,
                selected[name]["alpha"],
            )
            path = output / f"queries-{name}-b{budget}.npz"
            sha = save_queries(
                path, pop, counts, config["test_draws"], config["test_seed_start"], bi, stream
            )
            manifest.append(
                {
                    "policy": name,
                    "budget": budget,
                    "budget_index": bi,
                    "fraction": fraction,
                    "stream": stream,
                    "file": path.name,
                    "sha256": sha,
                    "sizes": list(map(len, pop)),
                    "counts": counts.tolist(),
                }
            )
            designs.append((name, budget, bi, stream, pop, counts, path))
    write_json(output / "query-manifest.json", manifest)
    refs = read_references(processed, ids)
    oracle = FrameOracle(refs, ids)
    q, y = testing["static"].f_q.to_numpy(float), np.array([refs[k] for k in ids], dtype=float)
    truth = float(y.mean())
    main_draws = pd.read_csv(main / "evaluation/draw-results.csv")
    simple_draws = pd.read_csv(simple / "draw-results.csv")
    summaries, checks, comparisons, rows = {}, [], {}, []
    for name, budget, bi, stream, pop, counts, path in designs:
        data, samples = evaluate_plans(ids, q, pop, counts, path, oracle)
        replay_rng(samples, pop, counts, config["test_seed_start"], bi, stream)
        point, comp, _, positives = sampled_components(samples, pop, counts, q, y)
        check = verify_estimates(data, point, comp)
        key = f"{name}-b{budget}"
        summary = summarize_draws(data, truth)
        independent_rmse = float(np.sqrt(np.mean((point - truth) ** 2)) * 100)
        if abs(independent_rmse - summary["rmse_pp"]) > 1e-10:
            raise ValueError("Independent RMSE summary mismatch")
        endpoints = np.array(
            [stratified_binary_interval(k, counts, list(map(len, pop))) for k in positives]
        )
        lo, hi = endpoints[:, 0], endpoints[:, 1]
        lower_total, upper_total = (
            np.rint(lo * len(ids)).astype(int),
            np.rint(hi * len(ids)).astype(int),
        )
        coverage = (lower_total <= int(y.sum())) & (upper_total >= int(y.sum()))
        summary["intervals"]["exact_binary_reference"] = {
            "coverage": float(coverage.mean()),
            "mean_width_pp": float(np.mean(hi - lo) * 100),
            "median_width_pp": float(np.median(hi - lo) * 100),
            "point_outside_rate": float(np.mean((data.prevalence < lo) | (data.prevalence > hi))),
            "centers_on_residual_estimate": False,
        }
        data = data.assign(
            policy=name,
            budget=budget,
            exact_binary_low=lo,
            exact_binary_high=hi,
            lower_total=lower_total,
            upper_total=upper_total,
        )
        rows.append(data)
        summaries[key] = summary
        checks.append({"policy": name, "budget": budget, **check})
        for comparator in ["M2", "M3", "M4", "q-quartiles"]:
            base = (
                main_draws[(main_draws.method == comparator) & (main_draws.budget == budget)]
                if comparator != "q-quartiles"
                else simple_draws[
                    (simple_draws.policy == comparator) & (simple_draws.budget == budget)
                ]
            )
            comparisons[f"{key}/{comparator}"] = comparison_ratio(
                data.prevalence.to_numpy() - truth,
                base.sort_values("draw").prevalence.to_numpy() - truth,
                config,
            )
        print(
            f"{stage} {name} B={budget}: RMSE={summary['rmse_pp']:.6f} pp; "
            f"normal coverage={summary['intervals']['normal']['coverage']:.3f}",
            flush=True,
        )
    data = pd.concat(rows, ignore_index=True)
    data.to_csv(output / "draw-results.csv", index=False)
    if stage == "C2-label-cost":
        for budget in [integer_budget(f, len(ids)) for f in config["fractions"]]:
            full = data[(data.policy == "score-labels-1") & (data.budget == budget)].sort_values(
                "draw"
            )
            for name in policies:
                current = data[(data.policy == name) & (data.budget == budget)].sort_values("draw")
                comparisons[f"{name}-b{budget}/full-labels"] = comparison_ratio(
                    current.prevalence.to_numpy() - truth,
                    full.prevalence.to_numpy() - truth,
                    config,
                )
    frozen_inputs(config)
    if file_hash(Path(__file__)) != registration["implementation_sha256"]:
        raise ValueError("Implementation changed during the registered stage")
    report = {
        "complete": True,
        "stage": stage,
        "designation": config["designation"],
        "reference_prevalence": truth,
        "population_size": len(ids),
        "draws_per_policy_budget": config["test_draws"],
        "sampled_method_runs": len(data),
        "results": summaries,
        "comparisons": comparisons,
        "selected_alphas": {name: c["alpha"] for name, c in selected.items()},
        "training_labels": costs,
        "validation_labels_reused": len(val_ids),
        "independent_checks": checks,
        "frozen_baseline_inputs_unchanged": True,
        "registration_sha256": file_hash(output / "registration.json"),
        "policy_lock_sha256": file_hash(output / "policy-lock.json"),
        "elapsed_seconds": time.monotonic() - started,
    }
    write_json(output / "result.json", report)
    return report
