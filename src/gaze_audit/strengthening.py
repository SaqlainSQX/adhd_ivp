"""Registered simple-policy controls and uncertainty diagnostics on frozen caches."""

import json
import math
import platform
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t

from .followups import choose_alpha, evaluate_plans, load_frozen_policy, load_main
from .frame_study import file_hash, make_design, read_references, save_queries, summarize_draws
from .frames import FrameOracle, integer_budget

Z95 = 1.959963984540054


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


@dataclass
class FeaturePolicy:
    feature: str
    cut_points: np.ndarray
    residual_sd: np.ndarray

    def strata(self, table):
        return np.searchsorted(self.cut_points, table[self.feature].to_numpy(), side="left")

    def as_dict(self):
        return {
            "feature": self.feature,
            "cut_points": self.cut_points.tolist(),
            "residual_sd": self.residual_sd.tolist(),
            "learner": "none; public training-feature quartiles",
        }


def fit_feature_policy(table, y, feature):
    scores = table[feature].to_numpy(float)
    residual = np.asarray(y, dtype=float) - table.f_q.to_numpy(float)
    if len(scores) < 2 or not np.isfinite(scores).all() or residual.shape != scores.shape:
        raise ValueError("Require finite public scores and matching training references")
    cuts = np.unique(np.quantile(scores, [0.25, 0.5, 0.75]))
    cuts = cuts[cuts < scores.max()]
    groups = np.searchsorted(cuts, scores, side="left")
    global_var = float(np.var(residual, ddof=1))
    sd = []
    for h in range(len(cuts) + 1):
        values = residual[groups == h]
        df = max(len(values) - 1, 0)
        within = float(np.var(values, ddof=1)) if df else 0.0
        sd.append(max(float(np.sqrt((df * within + 20 * global_var) / (df + 20))), 1e-6))
    return FeaturePolicy(feature, cuts, np.array(sd))


def satterthwaite_df(components, counts):
    components = np.asarray(components, dtype=float)
    counts = np.asarray(counts, dtype=float)
    denominator = np.sum(components**2 / np.maximum(counts - 1, 1), axis=-1)
    total = components.sum(axis=-1)
    return np.divide(total**2, denominator, out=np.full_like(total, np.inf), where=denominator > 0)


def calibration_multiplier(points, variances, truth):
    errors = np.abs(np.asarray(points) - truth)
    standard_error = np.sqrt(variances)
    scores = np.divide(
        errors, standard_error, out=np.full_like(errors, np.inf), where=standard_error > 0
    )
    scores[(standard_error == 0) & (errors <= 1e-14)] = 0
    rank = min(len(scores), math.ceil(0.95 * (len(scores) + 1)))
    selected = float(np.sort(scores)[rank - 1])
    return {
        "multiplier": max(Z95, selected) if np.isfinite(selected) else None,
        "rank_one_based": rank,
        "draws": len(scores),
        "zero_se_nonzero_error_draws": int(np.sum((standard_error == 0) & (errors > 1e-14))),
        "status": "finite" if np.isfinite(selected) else "unbounded",
    }


def replay_rng(samples, populations, counts, seed_start, budget_index, stream):
    if samples.shape[1] != sum(counts) or (np.diff(np.sort(samples, axis=1), axis=1) == 0).any():
        raise ValueError("Incorrect budget or duplicate queries")
    for draw, saved in enumerate(samples):
        rng = np.random.default_rng(
            np.random.SeedSequence([seed_start + draw, budget_index, stream])
        )
        expected = np.concatenate(
            [
                rng.choice(p, size=int(n), replace=False)
                for p, n in zip(populations, counts, strict=True)
            ]
        )
        if not np.array_equal(saved, expected):
            raise ValueError("Saved query RNG does not reproduce")


def sampled_components(samples, populations, counts, q, y):
    """Evaluation-only independent recomputation, never used to choose a policy."""
    point = np.full(len(samples), float(np.mean(q)))
    components, strata, positive_counts = [], [], []
    boundaries = np.r_[0, np.cumsum(counts)]
    for h, population in enumerate(populations):
        population = np.asarray(population)
        positions = samples[:, boundaries[h] : boundaries[h + 1]]
        if not np.isin(positions, population).all():
            raise ValueError("Query lies outside its frozen stratum")
        nh, count = len(population), int(counts[h])
        sampled = y[positions] - q[positions]
        point += nh / len(q) * sampled.mean(axis=1)
        factor = (nh / len(q)) ** 2 * (1 - count / nh) / count
        estimated = factor * sampled.var(axis=1, ddof=1) if count < nh else np.zeros(len(samples))
        true_var = float(np.var(y[population] - q[population], ddof=1)) if nh > 1 else 0.0
        positives = y[positions].sum(axis=1)
        positive_counts.append(positives)
        components.append(estimated)
        strata.append(
            {
                "stratum": h,
                "population_size": nh,
                "queries": count,
                "census": count == nh,
                "positive_references": int(y[population].sum()),
                "true_residual_variance": true_var,
                "exact_design_variance_component": factor * true_var,
                "mean_estimated_variance_component": float(estimated.mean()),
                "zero_sampled_positive_rate": float(np.mean(positives == 0)),
                "sampled_positive_quantiles": np.quantile(
                    positives, [0, 0.05, 0.5, 0.95, 1]
                ).tolist(),
            }
        )
    return point, np.stack(components, axis=1), strata, np.stack(positive_counts, axis=1)


def verify_estimates(data, point, components):
    variance = components.sum(axis=1)
    a = float(np.max(np.abs(data.prevalence.to_numpy() - point)))
    b = float(np.max(np.abs(data.variance.to_numpy() - variance)))
    if a > 1e-12 or b > 1e-12:
        raise ValueError("Independent point/variance recomputation failed")
    return {
        "status": "passed",
        "draws": len(data),
        "max_point_difference": a,
        "max_variance_difference": b,
    }


def ratio_summary(numerator, denominator, config):
    rng = np.random.default_rng(config["bootstrap_seed"])
    index = rng.integers(len(numerator), size=(config["bootstrap_resamples"], len(numerator)))
    top, bottom = np.asarray(numerator) ** 2, np.asarray(denominator) ** 2
    ratios = np.sqrt(top[index].mean(axis=1) / bottom[index].mean(axis=1))
    return {
        "rmse_ratio": float(np.sqrt(top.mean() / bottom.mean())),
        "draw_bootstrap_95pct": np.quantile(ratios, [0.025, 0.975]).tolist(),
        "seed": config["bootstrap_seed"],
        "resamples": config["bootstrap_resamples"],
        "scope": "Monte Carlo uncertainty on fixed corpus; streams differ across controls",
    }


def prepare(config_path, stage):
    config_path = Path(config_path)
    config = json.loads(config_path.read_text())
    main, processed = Path(config["main_run"]), Path(config["processed"])
    output = Path(config["output"]) / stage
    if output.exists():
        raise ValueError("Preserve existing outputs; use a new versioned config/output")
    lock, result, tables, hashes = load_main(main, processed)
    output.mkdir(parents=True)
    registration = {
        "stage": stage,
        "designation": "exploratory extension after inspected main outcomes",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "config": config,
        "config_sha256": file_hash(config_path),
        "protocol_sha256": file_hash(Path(config["protocol"])),
        "implementation_sha256": file_hash(Path(__file__)),
        "estimator_implementation_sha256": file_hash(Path(__file__).parent / "frames.py"),
        "main_result_sha256": file_hash(main / "evaluation/result.json"),
        "main_policy_lock_sha256": file_hash(main / "development/policy-lock.json"),
        "feature_hashes": hashes,
        "runtime": {
            "python": platform.python_version(),
            **{p: version(p) for p in ["numpy", "pandas", "scipy", "scikit-learn"]},
        },
    }
    write_json(output / "registration.json", registration)
    return config, main, processed, output, lock, result, tables, registration


def assert_main_unchanged(main, registration):
    for field, path in [
        ("main_result_sha256", "evaluation/result.json"),
        ("main_policy_lock_sha256", "development/policy-lock.json"),
    ]:
        if file_hash(main / path) != registration[field]:
            raise ValueError("The original main evidence changed")


def run_baselines(config_path):
    started = time.monotonic()
    config, main, processed, output, lock, result, tables, registration = prepare(
        config_path, "B1-simple-controls"
    )
    public = tables["static"]
    train = public[public.split.eq("train")].reset_index(drop=True)
    val = public[public.split.eq("validation")].reset_index(drop=True)
    test = public[public.split.eq("test")].reset_index(drop=True)
    train_refs = read_references(processed, tuple(train.record_id))
    train_y = np.array([train_refs[k] for k in train.record_id])
    policies = {
        name: fit_feature_policy(train, train_y, feature)
        for name, feature in [("q-quartiles", "f_q"), ("entropy-quartiles", "f_q_entropy")]
    }
    validation_plans, candidates = [], []
    val_ids = tuple(val.record_id)
    for name, policy in policies.items():
        for alpha in config["alphas"]:
            pop, counts = make_design(
                policy.strata(val), policy.residual_sd, integer_budget(0.1, len(val)), alpha
            )
            path = output / f"validation-{name}-alpha{alpha:g}.npz"
            sha = save_queries(
                path,
                pop,
                counts,
                config["simple_validation_draws"],
                config["simple_validation_seed_start"],
                1,
                config["simple_streams"][name],
            )
            validation_plans.append((name, alpha, pop, counts, path, sha))
    refs = read_references(processed, val_ids)
    truth = float(np.mean(list(refs.values())))
    oracle = FrameOracle(refs, val_ids)
    for name, alpha, pop, counts, path, sha in validation_plans:
        draws, _ = evaluate_plans(val_ids, val.f_q.to_numpy(), pop, counts, path, oracle)
        candidates.append(
            {
                "policy": name,
                "alpha": float(alpha),
                "validation_mse": float(np.mean((draws.prevalence - truth) ** 2)),
                "query_file": path.name,
                "query_sha256": sha,
                "budget": int(sum(counts)),
                "draws": len(draws),
            }
        )
    chosen = {
        name: choose_alpha([row for row in candidates if row["policy"] == name])
        for name in policies
    }
    policy_lock = {
        "policies": {name: policy.as_dict() for name, policy in policies.items()},
        "candidates": candidates,
        "selected": chosen,
        "selection_uses_test_outcomes": False,
        "training_rows": len(train),
        "validation_rows": len(val),
        "all_validation_plans_saved_before_selection_queries": True,
    }
    write_json(output / "policy-lock.json", policy_lock)
    test_plans, manifest = [], []
    ids = tuple(test.record_id)
    test[["record_id", "source_id"]].to_csv(output / "population_index.csv", index=False)
    for bi, fraction in enumerate(config["fractions"]):
        budget = integer_budget(fraction, len(test))
        for name, policy in policies.items():
            pop, counts = make_design(
                policy.strata(test), policy.residual_sd, budget, chosen[name]["alpha"]
            )
            path = output / f"test-{name}-b{budget}.npz"
            sha = save_queries(
                path,
                pop,
                counts,
                config["test_draws"],
                config["test_seed_start"],
                bi,
                config["simple_streams"][name],
            )
            manifest.append(
                {
                    "policy": name,
                    "fraction": fraction,
                    "budget_index": bi,
                    "budget": budget,
                    "counts": counts.tolist(),
                    "sizes": list(map(len, pop)),
                    "file": path.name,
                    "sha256": sha,
                }
            )
            test_plans.append((name, bi, budget, pop, counts, path))
    write_json(output / "query-manifest.json", manifest)
    refs = read_references(processed, ids)
    oracle, q = FrameOracle(refs, ids), test.f_q.to_numpy(float)
    y = np.array([refs[k] for k in ids], dtype=float)
    truth = float(y.mean())
    all_draws, summaries, checks = [], {}, []
    main_draws = pd.read_csv(main / "evaluation/draw-results.csv")
    comparisons = {}
    for name, bi, budget, pop, counts, path in test_plans:
        data, samples = evaluate_plans(ids, q, pop, counts, path, oracle)
        replay_rng(
            samples, pop, counts, config["test_seed_start"], bi, config["simple_streams"][name]
        )
        point, comp, _, _ = sampled_components(samples, pop, counts, q, y)
        check = verify_estimates(data, point, comp)
        key = f"{name}-b{budget}"
        checks.append({"policy": name, "budget": budget, **check})
        summaries[key] = summarize_draws(data, truth)
        for comparator in ["M2", "M3", "M4"]:
            baseline = main_draws[
                (main_draws.method == comparator) & (main_draws.budget == budget)
            ].sort_values("draw")
            comparisons[f"{comparator}/{key}"] = ratio_summary(
                baseline.prevalence.to_numpy() - truth, data.prevalence.to_numpy() - truth, config
            )
        all_draws.append(data.assign(policy=name, budget=budget))
        print(
            f"B1 {name} B={budget}: RMSE={summaries[key]['rmse_pp']:.6f} pp; "
            "independent checks passed",
            flush=True,
        )
    pd.concat(all_draws, ignore_index=True).to_csv(output / "draw-results.csv", index=False)
    assert_main_unchanged(main, registration)
    report = {
        "complete": True,
        "designation": "exploratory",
        "reference_prevalence": truth,
        "population_size": len(ids),
        "sampled_method_runs": sum(len(d) for d in all_draws),
        "draws_per_policy_budget": config["test_draws"],
        "selected_alphas": {name: row["alpha"] for name, row in chosen.items()},
        "results": summaries,
        "comparisons": comparisons,
        "independent_checks": checks,
        "main_result_unchanged": True,
        "policy_lock_sha256": file_hash(output / "policy-lock.json"),
        "registration_sha256": file_hash(output / "registration.json"),
        "elapsed_seconds": time.monotonic() - started,
    }
    write_json(output / "result.json", report)
    return report


def interval_summary(point, radius, truth):
    covered = np.abs(point - truth) <= radius
    coverage = float(np.mean(covered))
    return {
        "coverage": coverage,
        "coverage_mcse": float(np.sqrt(coverage * (1 - coverage) / len(point))),
        "mean_width_pp": float(np.mean(radius) * 200) if np.isfinite(radius).all() else None,
        "median_width_pp": float(np.median(radius) * 200) if np.isfinite(radius).all() else None,
        "unbounded_rate": float(np.mean(~np.isfinite(radius))),
    }


def run_coverage(config_path):
    started = time.monotonic()
    config, main, processed, output, lock, result, tables, registration = prepare(
        config_path, "B2-coverage"
    )
    policies = {
        method: load_frozen_policy(main, lock[field]["feature_set"], lock)
        for method, field in [("M3", "selected_static"), ("M4", "selected_temporal")]
    }
    val_tables = {
        name: table[table.split.eq("validation")].reset_index(drop=True)
        for name, table in tables.items()
    }
    test_tables = {
        name: table[table.split.eq("test")].reset_index(drop=True) for name, table in tables.items()
    }
    val, test = val_tables["static"], test_tables["static"]
    val_ids, ids = tuple(val.record_id), tuple(test.record_id)
    plans, manifest = [], []
    for method, policy in policies.items():
        chosen = lock["selected_static" if method == "M3" else "selected_temporal"]
        groups = policy.strata(val_tables[chosen["feature_set"]])
        for bi, fraction in enumerate(config["fractions"]):
            budget = integer_budget(fraction, len(val))
            pop, counts = make_design(groups, policy.residual_sd, budget, chosen["alpha"])
            path = output / f"validation-{method}-b{budget}.npz"
            sha = save_queries(
                path,
                pop,
                counts,
                config["coverage_validation_draws"],
                config["coverage_validation_seed_start"],
                bi,
                config["coverage_streams"][method],
            )
            manifest.append(
                {
                    "method": method,
                    "budget_index": bi,
                    "budget": budget,
                    "fraction": fraction,
                    "file": path.name,
                    "sha256": sha,
                }
            )
            plans.append((method, bi, pop, counts, path))
    write_json(output / "validation-query-manifest.json", manifest)
    refs = read_references(processed, val_ids)
    oracle, val_y = FrameOracle(refs, val_ids), np.array([refs[k] for k in val_ids], dtype=float)
    calibration, val_checks, val_rows = {}, [], []
    for method, bi, pop, counts, path in plans:
        data, samples = evaluate_plans(val_ids, val.f_q.to_numpy(), pop, counts, path, oracle)
        replay_rng(
            samples,
            pop,
            counts,
            config["coverage_validation_seed_start"],
            bi,
            config["coverage_streams"][method],
        )
        point, comp, _, _ = sampled_components(samples, pop, counts, val.f_q.to_numpy(), val_y)
        val_checks.append(
            {"method": method, "budget_index": bi, **verify_estimates(data, point, comp)}
        )
        calibration[f"{method}-fraction{config['fractions'][bi]}"] = calibration_multiplier(
            data.prevalence.to_numpy(), data.variance.to_numpy(), float(val_y.mean())
        )
        val_rows.append(data.assign(method=method, fraction=config["fractions"][bi]))
        print(
            f"B2 validation {method} fraction={config['fractions'][bi]}: "
            "calibration frozen candidate",
            flush=True,
        )
    pd.concat(val_rows, ignore_index=True).to_csv(
        output / "validation-draw-results.csv", index=False
    )
    write_json(
        output / "interval-lock.json",
        {
            "calibration": calibration,
            "test_outcomes_used": False,
            "policy_lock_sha256": registration["main_policy_lock_sha256"],
            "warning": "Empirical reused-development calibration; "
            "no transfer or distribution-free guarantee",
            "validation_checks": val_checks,
        },
    )
    # New full-test diagnostic calculations begin only after every multiplier is locked.
    refs = read_references(processed, ids)
    y, q = np.array([refs[k] for k in ids], dtype=float), test.f_q.to_numpy(float)
    truth = float(y.mean())
    main_draws = pd.read_csv(main / "evaluation/draw-results.csv")
    query_manifest = json.loads((main / "evaluation/query-manifest.json").read_text())
    summaries, checks, diagnostic_rows = {}, [], []
    for method, policy in policies.items():
        chosen = lock["selected_static" if method == "M3" else "selected_temporal"]
        groups = policy.strata(test_tables[chosen["feature_set"]])
        for bi, fraction in enumerate(config["fractions"]):
            budget = integer_budget(fraction, len(test))
            pop, counts = make_design(groups, policy.residual_sd, budget, chosen["alpha"])
            entry = next(
                e for e in query_manifest if e["design"] == method and e["budget"] == budget
            )
            path = main / "evaluation" / entry["file"]
            if file_hash(path) != entry["sha256"]:
                raise ValueError("Original query file changed")
            samples = np.load(path)["selected"]
            replay_rng(samples, pop, counts, 200000, bi, config["coverage_streams"][method])
            point, comp, strata, positive_counts = sampled_components(samples, pop, counts, q, y)
            data = main_draws[
                (main_draws.method == method) & (main_draws.budget == budget)
            ].sort_values("draw")
            checks.append(
                {"method": method, "budget": budget, **verify_estimates(data, point, comp)}
            )
            variance = comp.sum(axis=1)
            exact_var = sum(s["exact_design_variance_component"] for s in strata)
            df = satterthwaite_df(comp, counts)
            se, errors = np.sqrt(variance), point - truth
            c = calibration[f"{method}-fraction{fraction}"]["multiplier"]
            calibrated_radius = c * se if c is not None else np.full(len(se), np.inf)
            intervals = {
                "normal": interval_summary(point, Z95 * se, truth),
                "student_t": interval_summary(point, t.ppf(0.975, df) * se, truth),
                "validation_calibrated": interval_summary(point, calibrated_radius, truth),
                "exact_variance_normal_DIAGNOSTIC_ONLY": interval_summary(
                    point, np.full(len(se), Z95 * np.sqrt(exact_var)), truth
                ),
                "bounded": result["results"][f"{method}-b{budget}"]["intervals"]["bounded"],
            }
            standardized = np.divide(errors, se, out=np.zeros_like(errors), where=se > 0)
            conditioning = []
            for h, positive in enumerate(positive_counts.T):
                for label, mask in [
                    ("zero", positive == 0),
                    ("one_to_four", (positive >= 1) & (positive <= 4)),
                    ("five_or_more", positive >= 5),
                ]:
                    if mask.any():
                        conditioning.append(
                            {
                                "stratum": h,
                                "sampled_positives": label,
                                "draws": int(mask.sum()),
                                "normal_coverage": float(
                                    np.mean(np.abs(errors[mask]) <= Z95 * se[mask])
                                ),
                                "mean_estimated_variance_over_exact": float(
                                    np.mean(variance[mask]) / exact_var
                                )
                                if exact_var
                                else None,
                            }
                        )
            summaries[f"{method}-b{budget}"] = {
                "method": method,
                "budget": budget,
                "fraction": fraction,
                "draws": len(point),
                "exact_design_variance": exact_var,
                "empirical_sampling_variance": float(np.var(point, ddof=1)),
                "mean_estimated_variance": float(variance.mean()),
                "mean_variance_over_exact": float(variance.mean() / exact_var)
                if exact_var
                else None,
                "variance_ratio_quantiles_05_50_95": np.quantile(
                    variance / exact_var, [0.05, 0.5, 0.95]
                ).tolist()
                if exact_var
                else None,
                "standardized_error_quantiles_025_50_975": np.quantile(
                    standardized, [0.025, 0.5, 0.975]
                ).tolist(),
                "absolute_standardized_q95": float(np.quantile(np.abs(standardized), 0.95)),
                "effective_df_quantiles_05_50_95": np.quantile(df, [0.05, 0.5, 0.95]).tolist(),
                "calibration": calibration[f"{method}-fraction{fraction}"],
                "intervals": intervals,
                "strata": strata,
                "conditional_diagnostics": conditioning,
            }
            diagnostic_rows.append(
                pd.DataFrame(
                    {
                        "method": method,
                        "budget": budget,
                        "draw": np.arange(len(point)),
                        "error_pp": errors * 100,
                        "estimated_variance": variance,
                        "exact_variance": exact_var,
                        "standardized_error": standardized,
                        "effective_df": df,
                    }
                )
            )
            print(
                f"B2 test {method} B={budget}: normal={intervals['normal']['coverage']:.3f}; "
                f"t={intervals['student_t']['coverage']:.3f}; "
                f"calibrated={intervals['validation_calibrated']['coverage']:.3f}",
                flush=True,
            )
    pd.concat(diagnostic_rows, ignore_index=True).to_csv(
        output / "diagnostic-draws.csv", index=False
    )
    assert_main_unchanged(main, registration)
    report = {
        "complete": True,
        "designation": "exploratory interval diagnostics",
        "validation_draws_recomputed": sum(c["draws"] for c in val_checks),
        "test_draws_recomputed": sum(c["draws"] for c in checks),
        "reference_prevalence": truth,
        "results": summaries,
        "independent_test_checks": checks,
        "main_result_unchanged": True,
        "interval_lock_sha256": file_hash(output / "interval-lock.json"),
        "registration_sha256": file_hash(output / "registration.json"),
        "elapsed_seconds": time.monotonic() - started,
    }
    write_json(output / "result.json", report)
    return report
