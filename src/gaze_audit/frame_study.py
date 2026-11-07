"""Frozen development selection and locked fixed-corpus frame comparisons."""

import hashlib
import json
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .frame_policy import fit_frame_policy
from .frames import (
    FrameOracle,
    FrameStratum,
    allocate_counts,
    estimate_frames,
    hypergeometric_interval,
    integer_budget,
)


def file_hash(path):
    sha = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def load_feature_population(directory):
    manifest = json.loads((directory / "manifest.json").read_text())
    if not manifest["complete"]:
        raise ValueError("Incomplete feature build")
    tables, hashes = {}, {}
    for name, entry in manifest["feature_files"].items():
        path = directory / entry["filename"]
        hashes[name] = file_hash(path)
        if hashes[name] != entry["sha256"]:
            raise ValueError("Feature hash changed")
        table = pd.read_csv(path)
        if table.record_id.duplicated().any():
            raise ValueError("Duplicate feature identities")
        columns = [c for c in table if c.startswith("f_")]
        if columns != entry["feature_columns"]:
            raise ValueError("Feature-column contract changed")
        tables[name] = table[table.eligible_anchor == 1].reset_index(drop=True)
    if set(tables) != {"static", "temporal-w5", "temporal-w11"}:
        raise ValueError("Require the three prespecified feature sets")
    static = tables["static"]
    if static.groupby("source_id").split.nunique().max() != 1:
        raise ValueError("Source leaks across splits")
    for name, table in tables.items():
        if set(table.record_id) != set(static.record_id):
            raise ValueError("Feature populations differ")
        tables[name] = table.set_index("record_id").loc[static.record_id].reset_index()
        if not np.array_equal(tables[name].f_q, static.f_q):
            raise ValueError("Methods must use the same frozen q")
    return tables, hashes


def read_references(processed, ids):
    reference = pd.read_csv(processed / "oracle/oracle_labels.csv")
    reference = reference[reference.record_id.isin(ids)]
    if reference.record_id.duplicated().any() or set(reference.record_id) != set(ids):
        raise ValueError("Reference/eligible ID mismatch")
    values = dict(zip(reference.record_id, reference.label, strict=True))
    if not all(y in (0, 1) for y in values.values()):
        raise ValueError("Nonbinary oracle values")
    return values


def make_design(strata, sd, budget, mix):
    present = np.unique(strata)
    populations = tuple(tuple(map(int, np.flatnonzero(strata == h))) for h in present)
    counts = allocate_counts([len(p) for p in populations], np.asarray(sd)[present], budget, mix)
    return populations, counts


def save_queries(path, populations, counts, draws, seed_start, budget_index, stream):
    size = sum(counts)
    selected = np.empty((draws, size), dtype=np.int32)
    for draw in range(draws):
        rng = np.random.default_rng(
            np.random.SeedSequence([seed_start + draw, budget_index, stream])
        )
        selected[draw] = np.concatenate(
            [
                rng.choice(pop, size=int(count), replace=False)
                for pop, count in zip(populations, counts, strict=True)
            ]
        )
    np.savez_compressed(path, selected=selected, counts=counts)
    return file_hash(path)


def reconstruct_plan(populations, counts, selected):
    boundaries = np.r_[0, np.cumsum(counts)]
    return tuple(
        FrameStratum(pop, tuple(map(int, selected[boundaries[h] : boundaries[h + 1]])))
        for h, pop in enumerate(populations)
    )


def develop(tables, hashes, processed, output, draws=100):
    if output.exists():
        raise ValueError("Policy locks are immutable; choose a new development directory")
    output.mkdir(parents=True)
    mask_train = tables["static"].split.eq("train").to_numpy()
    mask_val = tables["static"].split.eq("validation").to_numpy()
    train_ids = tuple(tables["static"].loc[mask_train, "record_id"])
    val_ids = tuple(tables["static"].loc[mask_val, "record_id"])
    if not train_ids or not val_ids:
        raise ValueError("Training and validation populations must be nonempty")
    labels = read_references(processed, train_ids)
    y_train = np.array([labels[key] for key in train_ids])
    source_folds = pd.read_csv(processed / "development_folds.csv").set_index("source_id").fold
    candidates, models, designs = [], {}, {}
    for name, table in tables.items():
        training = table.loc[mask_train].reset_index(drop=True)
        validation = table.loc[mask_val].reset_index(drop=True)
        folds = training.source_id.map(source_folds).to_numpy()
        policy, diagnostics, oof = fit_frame_policy(training, y_train, folds)
        models[name] = policy
        joblib.dump(policy, output / f"{name}-policy.joblib")
        np.save(output / f"{name}-oof-scores.npy", oof)
        (output / f"{name}-development.json").write_text(json.dumps(diagnostics, indent=2))
        strata = policy.strata(validation)
        budget = integer_budget(0.1, len(val_ids))
        for alpha in [0.0, 0.5, 1.0]:
            key = f"{name}-alpha{alpha:g}"
            populations, counts = make_design(strata, policy.residual_sd, budget, alpha)
            path = output / f"queries-{key}.npz"
            query_hash = save_queries(
                path, populations, counts, draws, 100000, 1, 3 if name == "static" else 4
            )
            designs[key] = (populations, counts)
            candidates.append(
                {
                    "candidate": key,
                    "feature_set": name,
                    "alpha": alpha,
                    "temporal_window": None
                    if name == "static"
                    else int(name[-1:])
                    if name.endswith("5")
                    else 11,
                    "budget": budget,
                    "draws": draws,
                    "query_file": path.name,
                    "query_sha256": query_hash,
                    "stratum_sizes": list(map(len, populations)),
                    "stratum_counts": counts.tolist(),
                }
            )
        print(f"Fitted {name} with source-held-out development scores", flush=True)
    # All nine validation designs exist before selection queries are revealed.
    labels_val = read_references(processed, val_ids)
    oracle = FrameOracle(labels_val, val_ids)
    truth = float(np.mean(list(labels_val.values())))
    q = tables["static"].loc[mask_val, "f_q"].to_numpy()
    for candidate in candidates:
        indices = np.load(output / candidate["query_file"])["selected"]
        populations, counts = designs[candidate["candidate"]]
        error = []
        for selection in indices:
            queried = oracle.query(tuple(val_ids[i] for i in selection))
            plan = reconstruct_plan(populations, counts, selection)
            result = estimate_frames(val_ids, q, plan, queried)
            error.append(result.prevalence - truth)
        candidate["validation_mse"] = float(np.mean(np.asarray(error) ** 2))

    def choose(temporal):
        subset = [r for r in candidates if (r["feature_set"] != "static") == temporal]
        best = min(row["validation_mse"] for row in subset)
        tied = [r for r in subset if r["validation_mse"] <= best * 1.01]
        return min(tied, key=lambda r: (r["alpha"], r["temporal_window"] or 0))

    static, temporal = choose(False), choose(True)
    lock = {
        "stage": "E03",
        "complete": True,
        "designation": "exploratory",
        "feature_hashes": hashes,
        "all_validation_plans_saved_before_selection_queries": True,
        "selection_draws": draws,
        "selection_fraction": 0.1,
        "tie_rule": "within 1% MSE, smaller alpha then smaller temporal window",
        "development_unique_labels": {"train": len(train_ids), "validation": len(val_ids)},
        "test_references_used_for_selection": False,
        "oracle_file_sha256": file_hash(processed / "oracle/oracle_labels.csv"),
        "candidates": candidates,
        "selected_static": static,
        "selected_temporal": temporal,
        "model_hashes": {name: file_hash(output / f"{name}-policy.joblib") for name in models},
    }
    (output / "policy-lock.json").write_text(json.dumps(lock, indent=2) + "\n")
    return lock


def summarize_draws(data, truth):
    errors = data.prevalence - truth
    result = {
        "bias_pp": float(errors.mean() * 100),
        "mae_pp": float(errors.abs().mean() * 100),
        "rmse_pp": float(np.sqrt(np.mean(errors**2)) * 100),
        "mean_labels": float(data.labels_revealed.mean()),
        "zero_variance_rate": float(data.variance.eq(0).mean()),
        "zero_positive_rate": float(data.positives_revealed.eq(0).mean()),
        "failed_draw_rate": 0.0,
        "intervals": {},
    }
    for interval in ["normal", "bounded", "hypergeometric"]:
        if f"{interval}_low" not in data or data[f"{interval}_low"].isna().all():
            continue
        low, high = data[f"{interval}_low"], data[f"{interval}_high"]
        result["intervals"][interval] = {
            "coverage": float(((low <= truth) & (truth <= high)).mean()),
            "mean_width_pp": float((high - low).mean() * 100),
            "median_width_pp": float((high - low).median() * 100),
        }
    return result


def evaluate(tables, hashes, processed, development, output, draws=1000):
    if output.exists():
        raise ValueError("Choose a new evaluation directory")
    lock_path = development / "policy-lock.json"
    lock = json.loads(lock_path.read_text())
    if not lock["complete"] or lock["feature_hashes"] != hashes:
        raise ValueError("Policy lock and feature population disagree")
    policies = {}
    for method, field in [("M3", "selected_static"), ("M4", "selected_temporal")]:
        name = lock[field]["feature_set"]
        path = development / f"{name}-policy.joblib"
        if file_hash(path) != lock["model_hashes"][name]:
            raise ValueError("Frozen policy model hash changed")
        policies[method] = joblib.load(path)
    mask = tables["static"].split.eq("test").to_numpy()
    test = {name: table.loc[mask].reset_index(drop=True) for name, table in tables.items()}
    ids = tuple(test["static"].record_id)
    if not ids:
        raise ValueError("No test population")
    q = test["static"].f_q.to_numpy(float)
    q_contextual = policies["M4"].contextual_surrogate(
        test[lock["selected_temporal"]["feature_set"]]
    )
    size = len(ids)
    source_codes, source_ids = pd.factorize(test["static"].source_id, sort=True)
    source_sizes = np.bincount(source_codes)
    surrogates = {"M1": np.zeros(size), "M2": q, "M3": q, "M4": q, "M5": q_contextual}
    source_prediction_totals = {
        method: np.bincount(source_codes, weights=values) for method, values in surrogates.items()
    }
    output.mkdir(parents=True)
    test["static"][["record_id", "source_id"]].to_csv(
        output / "population_index.csv", index_label="row_index"
    )
    designs, query_records = {}, []
    for budget_index, fraction in enumerate([0.05, 0.1, 0.2, 0.4]):
        budget = integer_budget(fraction, size)
        for method, stream in [("uniform", 1), ("M3", 3), ("M4", 4)]:
            if method == "uniform":
                populations, counts = (tuple(range(size)),), np.array([budget])
            else:
                selected = lock["selected_static" if method == "M3" else "selected_temporal"]
                policy = policies[method]
                strata = policy.strata(test[selected["feature_set"]])
                populations, counts = make_design(
                    strata, policy.residual_sd, budget, selected["alpha"]
                )
            path = output / f"queries-{method}-b{budget}.npz"
            sha = save_queries(path, populations, counts, draws, 200000, budget_index, stream)
            designs[(budget, method)] = (populations, counts)
            query_records.append(
                {
                    "budget": budget,
                    "fraction": fraction,
                    "design": method,
                    "file": path.name,
                    "sha256": sha,
                    "stratum_sizes": list(map(len, populations)),
                    "stratum_counts": counts.tolist(),
                }
            )
    # All test plans are fixed and saved before revealing any evaluation query.
    (output / "query-manifest.json").write_text(json.dumps(query_records, indent=2))
    labels = read_references(processed, ids)
    oracle = FrameOracle(labels, ids)
    truth = float(np.mean(list(labels.values())))
    source_reference_totals = np.bincount(source_codes, weights=[labels[key] for key in ids])
    exact_interval = lru_cache(maxsize=None)(hypergeometric_interval)
    rows, source_rows = [], []
    for record in query_records:
        budget, design = record["budget"], record["design"]
        populations, counts = designs[(budget, design)]
        samples = np.load(output / record["file"])["selected"]
        for draw, selection in enumerate(samples):
            queried = oracle.query(tuple(ids[i] for i in selection))
            plan = reconstruct_plan(populations, counts, selection)
            methods = ["M1", "M2", "M5"] if design == "uniform" else [design]
            for method in methods:
                surrogate = surrogates[method]
                estimate = estimate_frames(ids, surrogate, plan, queried)
                row = {
                    "method": method,
                    "budget": budget,
                    "fraction": record["fraction"],
                    "draw": draw,
                    **estimate.as_dict(),
                }
                if method == "M1":
                    low, high = exact_interval(estimate.positives_revealed, budget, size)
                    row.update({"hypergeometric_low": low, "hypergeometric_high": high})
                rows.append(row)
                if record["fraction"] == 0.1:
                    domain_totals = source_prediction_totals[method].copy()
                    for stratum in plan:
                        selected = np.asarray(stratum.selected, dtype=int)
                        residual = (
                            np.array([queried[ids[i]] for i in selected]) - surrogate[selected]
                        )
                        domain_totals += np.bincount(
                            source_codes[selected],
                            weights=(len(stratum.population) / len(selected) * residual),
                            minlength=len(source_ids),
                        )
                    if abs(domain_totals.sum() / size - estimate.prevalence) > 1e-10:
                        raise ArithmeticError(
                            "Source-domain totals do not reconstruct global estimate"
                        )
                    realized = np.bincount(source_codes[selection], minlength=len(source_ids))
                    for source, source_id in enumerate(source_ids):
                        outside_size = size - source_sizes[source]
                        outside_truth = (
                            ((truth * size - source_reference_totals[source]) / outside_size)
                            if outside_size
                            else None
                        )
                        outside_estimate = (
                            ((estimate.prevalence * size - domain_totals[source]) / outside_size)
                            if outside_size
                            else None
                        )
                        source_rows.append(
                            {
                                "method": method,
                                "draw": draw,
                                "budget": budget,
                                "source_id": source_id,
                                "source_population_size": int(source_sizes[source]),
                                "source_queries": int(realized[source]),
                                "source_prevalence_estimate": float(
                                    domain_totals[source] / source_sizes[source]
                                ),
                                "source_reference_prevalence": float(
                                    source_reference_totals[source] / source_sizes[source]
                                ),
                                "leave_source_out_estimate": outside_estimate,
                                "leave_source_out_reference": outside_truth,
                            }
                        )
        print(f"Evaluated {design}, B={budget}, {draws} draws", flush=True)
    data = pd.DataFrame(rows)
    data.to_csv(output / "draw-results.csv", index=False)
    domain = pd.DataFrame(source_rows)
    domain.to_csv(output / "primary-budget-source-domains.csv", index=False)
    source_sensitivity = []
    for source_id, group in domain.groupby("source_id"):
        values = {}
        for method, subset in group.groupby("method"):
            source_error = subset.source_prevalence_estimate - subset.source_reference_prevalence
            outside_error = subset.leave_source_out_estimate - subset.leave_source_out_reference
            values[method] = {
                "source_rmse_pp": float(np.sqrt(np.mean(source_error**2)) * 100),
                "leave_source_out_rmse_pp": float(np.sqrt(np.mean(outside_error**2)) * 100)
                if not outside_error.isna().all()
                else None,
                "mean_source_queries": float(subset.source_queries.mean()),
            }
        denominator = values["M3"]["leave_source_out_rmse_pp"]
        numerator = values["M4"]["leave_source_out_rmse_pp"]
        source_sensitivity.append(
            {
                "source_id": source_id,
                "methods": values,
                "leave_source_out_M4_over_M3": numerator / denominator if denominator else None,
            }
        )
    results = {
        f"{method}-b{budget}": summarize_draws(group, truth)
        for (method, budget), group in data.groupby(["method", "budget"])
    }
    comparisons = []
    for budget_index, fraction in enumerate([0.05, 0.1, 0.2, 0.4]):
        budget = integer_budget(fraction, size)
        main = data[data.budget == budget].pivot(
            index="draw", columns="method", values="prevalence"
        )
        squared = (main - truth) ** 2
        rng = np.random.default_rng(400000 + budget_index)
        bootstrap = rng.integers(draws, size=(2000, draws))
        for comparator in ["M3", "M2", "M5"]:
            numerator = squared.M4.to_numpy()
            denominator = squared[comparator].to_numpy()
            base = denominator.mean()
            ratios = np.sqrt(
                numerator[bootstrap].mean(axis=1)
                / np.maximum(denominator[bootstrap].mean(axis=1), 1e-30)
            )
            comparisons.append(
                {
                    "budget": budget,
                    "fraction": fraction,
                    "comparison": f"M4/{comparator}",
                    "rmse_ratio": float(np.sqrt(numerator.mean() / base)) if base else None,
                    "paired_draw_bootstrap_95pct": np.quantile(ratios, [0.025, 0.975]).tolist(),
                    "scope": "Monte Carlo uncertainty on this fixed corpus",
                }
            )
    report = {
        "stages": ["E04", "E05"],
        "complete": True,
        "designation": "exploratory",
        "test_population_size": size,
        "test_source_count": test["static"].source_id.nunique(),
        "reference_prevalence": truth,
        "model_only_mean": float(q.mean()),
        "model_only_bias_pp": float((q.mean() - truth) * 100),
        "draws_per_method_budget": draws,
        "sampled_method_runs": len(rows),
        "feature_hashes": hashes,
        "policy_lock_sha256": file_hash(lock_path),
        "oracle_file_sha256": file_hash(processed / "oracle/oracle_labels.csv"),
        "all_query_plans_saved_before_oracle": True,
        "uniform_queries_reused_by": ["M1", "M2", "M5"],
        "results": results,
        "comparisons": comparisons,
        "primary_source_sensitivity": source_sensitivity,
        "source_sensitivity_scope": (
            "Source-domain and leave-source-out-domain estimates under the original full-corpus "
            "query design; removed-source queries are still charged. "
            "No refitting or new-source guarantee."
        ),
        "novelty_or_positive_result_assumed": False,
    }
    (output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    return report
