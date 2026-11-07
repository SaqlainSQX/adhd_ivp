"""Registered exploratory interpretation checks; never replace the locked main result."""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .frame_policy import fit_frame_policy
from .frame_study import (
    file_hash,
    load_feature_population,
    make_design,
    read_references,
    reconstruct_plan,
    save_queries,
    summarize_draws,
)
from .frames import FrameOracle, estimate_frames, integer_budget

DROP_ORDERED = (
    "f_t_q_adjacent_change_mean",
    "f_t_q_previous_difference",
    "f_t_q_next_difference",
    "f_t_previous_context_missing",
    "f_t_next_context_missing",
    "f_t_head_a_area_change_mean",
    "f_t_head_b_area_change_mean",
    "f_t_pair_center_distance_change_mean",
)


def summary_only(table):
    if not set(DROP_ORDERED) <= set(table):
        raise ValueError("The registered eight-column transition ablation cannot be applied")
    return table.drop(columns=list(DROP_ORDERED)).copy()


def choose_alpha(candidates):
    if sorted(row["alpha"] for row in candidates) != [0.0, 0.5, 1.0]:
        raise ValueError("Require exactly the three registered validation alpha candidates")
    best = min(row["validation_mse"] for row in candidates)
    tied = [row for row in candidates if row["validation_mse"] <= best * 1.01]
    return min(tied, key=lambda row: row["alpha"])


def bootstrap_ratio(numerator, denominator):
    numerator, denominator = np.asarray(numerator), np.asarray(denominator)
    if numerator.shape != denominator.shape or numerator.ndim != 1:
        raise ValueError("Paired draws must align")
    rng = np.random.default_rng(400001)
    index = rng.integers(len(numerator), size=(2000, len(numerator)))
    ratios = np.sqrt(
        np.mean(numerator[index] ** 2, axis=1)
        / np.maximum(np.mean(denominator[index] ** 2, axis=1), 1e-30)
    )
    return {
        "rmse_ratio": float(np.sqrt(np.mean(numerator**2) / np.mean(denominator**2)))
        if np.any(denominator)
        else None,
        "paired_draw_bootstrap_95pct": np.quantile(ratios, [0.025, 0.975]).tolist(),
        "resamples": 2000,
        "seed": 400001,
        "scope": "Monte Carlo uncertainty on the fixed available corpus",
    }


def load_main(main, processed):
    lock_path = main / "development/policy-lock.json"
    result_path = main / "evaluation/result.json"
    lock, result = json.loads(lock_path.read_text()), json.loads(result_path.read_text())
    verification = json.loads((main / "independent-validation.json").read_text())
    if (
        not result["complete"]
        or verification["status"] != "passed"
        or verification["evaluation_result_sha256"] != file_hash(result_path)
        or result["policy_lock_sha256"] != file_hash(lock_path)
    ):
        raise ValueError("Main run must be complete, independently verified and unchanged")
    if file_hash(processed / "oracle/oracle_labels.csv") != result["oracle_file_sha256"]:
        raise ValueError("Main reference version changed")
    tables, hashes = load_feature_population(main / "features")
    if hashes != lock["feature_hashes"] or hashes != result["feature_hashes"]:
        raise ValueError("Main frozen feature hashes changed")
    return lock, result, tables, hashes


def load_frozen_policy(main, name, lock):
    path = main / "development" / f"{name}-policy.joblib"
    if file_hash(path) != lock["model_hashes"][name]:
        raise ValueError("Main frozen policy changed")
    return joblib.load(path)


def evaluate_plans(ids, q, populations, counts, path, oracle):
    selected = np.load(path)["selected"]
    rows = []
    for draw, selection in enumerate(selected):
        queried = oracle.query(tuple(ids[i] for i in selection))
        plan = reconstruct_plan(populations, counts, selection)
        rows.append({"draw": draw, **estimate_frames(ids, q, plan, queried).as_dict()})
    return pd.DataFrame(rows), selected


def independent_check(data, selections, populations, counts, q, y):
    """Recompute all draw estimates and variances with independent vectorized formulas."""
    if (np.diff(np.sort(selections, axis=1), axis=1) == 0).any():
        raise ValueError("Duplicate query within a draw")
    for draw, selected in enumerate(selections):
        rng = np.random.default_rng(np.random.SeedSequence([200000 + draw, 1, 4]))
        regenerated = np.concatenate(
            [
                rng.choice(pop, size=int(count), replace=False)
                for pop, count in zip(populations, counts, strict=True)
            ]
        )
        if not np.array_equal(selected, regenerated):
            raise ValueError("Follow-up query RNG replay failed")
    point, variance = np.full(len(selections), np.mean(q)), np.zeros(len(selections))
    edges = np.r_[0, np.cumsum(counts)]
    for h, population in enumerate(populations):
        positions = selections[:, edges[h] : edges[h + 1]]
        if not np.isin(positions, population).all():
            raise ValueError("Query outside its planned stratum")
        nh, n = len(population), counts[h]
        residuals = y[positions] - q[positions]
        point += nh / len(q) * residuals.mean(axis=1)
        if n < nh:
            variance += (nh / len(q)) ** 2 * (1 - n / nh) * residuals.var(axis=1, ddof=1) / n
    if not np.allclose(data.prevalence, point, rtol=0, atol=1e-12):
        raise ValueError("Independent follow-up point recomputation failed")
    if not np.allclose(data.variance, variance, rtol=0, atol=1e-12):
        raise ValueError("Independent follow-up variance recomputation failed")
    return {
        "status": "passed",
        "draws": len(data),
        "max_point_difference": float(np.max(np.abs(data.prevalence.to_numpy() - point))),
        "max_variance_difference": float(np.max(np.abs(data.variance.to_numpy() - variance))),
    }


def run_followup(
    stage: str, main: Path, processed: Path, output: Path, *, draws=1000, validation_draws=100
):
    if (
        stage not in ["windows", "summary-only"]
        or output.exists()
        or min(draws, validation_draws) < 1
    ):
        raise ValueError("Require a registered stage, positive draws and a new output directory")
    lock, main_result, tables, hashes = load_main(main, processed)
    if draws > main_result["draws_per_method_budget"]:
        raise ValueError("Follow-up paired comparisons cannot exceed saved main draws")
    main_lock_hash = file_hash(main / "development/policy-lock.json")
    main_result_hash = file_hash(main / "evaluation/result.json")
    output.mkdir(parents=True)
    registration = {
        "stage": "A1" if stage == "windows" else "A2",
        "designation": "exploratory",
        "main_policy_lock_sha256": main_lock_hash,
        "main_result_sha256": main_result_hash,
        "feature_hashes": hashes,
        "test_draws": draws,
        "fraction": 0.1,
        "seed_start": 200000,
        "budget_index": 1,
        "method_stream_id": 4,
        "validation_draws": validation_draws,
        "removed_columns": list(DROP_ORDERED) if stage == "summary-only" else [],
        "main_result_replacement_allowed": False,
        "implementation_sha256": file_hash(Path(__file__)),
        "error_model_implementation_sha256": file_hash(Path(__file__).parent / "frame_policy.py"),
        "registered_protocol_sha256": file_hash(Path("docs/FOLLOWUP_EXPERIMENTS.md")),
    }
    registration_path = output / "registration.json"
    registration_path.write_text(json.dumps(registration, indent=2) + "\n")
    test_mask = tables["static"].split.eq("test").to_numpy()
    train_mask = tables["static"].split.eq("train").to_numpy()
    val_mask = tables["static"].split.eq("validation").to_numpy()
    ids = tuple(tables["static"].loc[test_mask, "record_id"])
    q = tables["static"].loc[test_mask, "f_q"].to_numpy(float)
    budget = integer_budget(0.1, len(ids))
    tables["static"].loc[test_mask, ["record_id", "source_id"]].to_csv(
        output / "population_index.csv", index_label="row_index"
    )
    policies, candidates = {}, []
    if stage == "windows":
        for width in [5, 11]:
            name = f"temporal-w{width}"
            chosen = choose_alpha([c for c in lock["candidates"] if c["feature_set"] == name])
            policy = load_frozen_policy(main, name, lock)
            policies[name] = (
                policy,
                tables[name].loc[test_mask].reset_index(drop=True),
                chosen["alpha"],
            )
            candidates.append(chosen.copy())
    else:
        name = lock["selected_temporal"]["feature_set"]
        reduced = summary_only(tables[name])
        train = reduced.loc[train_mask].reset_index(drop=True)
        validation = reduced.loc[val_mask].reset_index(drop=True)
        train_ids, val_ids = tuple(train.record_id), tuple(validation.record_id)
        references = read_references(processed, train_ids)
        y_train = np.array([references[key] for key in train_ids])
        source_folds = pd.read_csv(processed / "development_folds.csv").set_index("source_id").fold
        print("Fitting summary-only model with five original training-source folds", flush=True)
        policy, diagnostics, oof = fit_frame_policy(
            train, y_train, train.source_id.map(source_folds)
        )
        joblib.dump(policy, output / "summary-only-policy.joblib")
        np.save(output / "summary-only-oof.npy", oof)
        (output / "summary-only-development.json").write_text(json.dumps(diagnostics, indent=2))
        validation_budget = integer_budget(0.1, len(val_ids))
        val_designs = []
        for alpha in [0.0, 0.5, 1.0]:
            pop, count = make_design(
                policy.strata(validation), policy.residual_sd, validation_budget, alpha
            )
            path = output / f"validation-alpha{alpha:g}.npz"
            sha = save_queries(path, pop, count, validation_draws, 100000, 1, 4)
            val_designs.append((alpha, pop, count, path, sha))
        # All validation plans are saved before their reference values are exposed for selection.
        references = read_references(processed, val_ids)
        oracle = FrameOracle(references, val_ids)
        truth = float(np.mean(list(references.values())))
        for alpha, pop, count, path, sha in val_designs:
            data, _ = evaluate_plans(val_ids, validation.f_q.to_numpy(), pop, count, path, oracle)
            candidates.append(
                {
                    "alpha": alpha,
                    "validation_mse": float(np.mean((data.prevalence - truth) ** 2)),
                    "query_file": path.name,
                    "query_sha256": sha,
                    "budget": validation_budget,
                    "feature_set": "summary-only",
                    "draws": validation_draws,
                }
            )
        chosen = choose_alpha(candidates)
        policies["summary-only"] = (
            policy,
            reduced.loc[test_mask].reset_index(drop=True),
            chosen["alpha"],
        )
    selection = {
        "main_lock_sha256": main_lock_hash,
        "candidates": candidates,
        "selected_alphas": {key: values[2] for key, values in policies.items()},
        "tie_rule": "within 1% validation MSE; smaller alpha",
        "selection_uses_test_outcomes": False,
        "feature_columns": {key: list(value[0].feature_columns) for key, value in policies.items()},
    }
    selection_path = output / "followup-policy-lock.json"
    selection_path.write_text(json.dumps(selection, indent=2) + "\n")
    designs, plan_manifest = {}, []
    for name, (policy, test, alpha) in policies.items():
        populations, counts = make_design(policy.strata(test), policy.residual_sd, budget, alpha)
        path = output / f"test-queries-{name}.npz"
        sha = save_queries(path, populations, counts, draws, 200000, 1, 4)
        designs[name] = (populations, counts, path)
        plan_manifest.append(
            {
                "policy": name,
                "budget": budget,
                "draws": draws,
                "alpha": alpha,
                "stratum_sizes": list(map(len, populations)),
                "stratum_counts": counts.tolist(),
                "query_file": path.name,
                "query_sha256": sha,
            }
        )
    (output / "query-manifest.json").write_text(json.dumps(plan_manifest, indent=2) + "\n")
    # Training/selection never receive test outcomes. All test plans precede test queries.
    references = read_references(processed, ids)
    oracle = FrameOracle(references, ids)
    y = np.array([references[key] for key in ids], dtype=float)
    truth = float(y.mean())
    all_data, checks, summaries = [], {}, {}
    for name, (populations, counts, path) in designs.items():
        data, positions = evaluate_plans(ids, q, populations, counts, path, oracle)
        checks[name] = independent_check(data, positions, populations, counts, q, y)
        summaries[name] = summarize_draws(data, truth)
        all_data.append(data.assign(policy=name))
        print(
            f"Evaluated {name}: {draws} draws, B={budget}, "
            f"RMSE={summaries[name]['rmse_pp']:.6f} pp",
            flush=True,
        )
    data = pd.concat(all_data, ignore_index=True)
    data.to_csv(output / "draw-results.csv", index=False)
    comparisons = {}
    if stage == "windows":
        pivot = data.pivot(index="draw", columns="policy", values="prevalence")
        comparisons["W11/W5"] = bootstrap_ratio(
            pivot["temporal-w11"] - truth, pivot["temporal-w5"] - truth
        )
        selected_name = lock["selected_temporal"]["feature_set"]
        saved = np.load(main / "evaluation" / f"queries-M4-b{budget}.npz")["selected"]
        current = np.load(designs[selected_name][2])["selected"]
        if not np.array_equal(saved[:draws], current):
            raise ValueError("Selected window query plans do not reproduce main M4")
    main_draws = pd.read_csv(main / "evaluation/draw-results.csv")
    for name, group in data.groupby("policy"):
        for comparator in ["M3", "M4"]:
            baseline = main_draws[(main_draws.method == comparator) & (main_draws.budget == budget)]
            baseline = baseline.sort_values("draw").head(draws)
            if len(baseline) != draws:
                raise ValueError("Main comparator draw grid does not align")
            comparisons[f"{name}/{comparator}"] = bootstrap_ratio(
                group.sort_values("draw").prevalence.to_numpy() - truth,
                baseline.prevalence.to_numpy() - truth,
            )
            if (
                stage == "windows"
                and name == lock["selected_temporal"]["feature_set"]
                and comparator == "M4"
            ):
                if not np.allclose(
                    group.sort_values("draw").prevalence, baseline.prevalence, rtol=0, atol=1e-12
                ):
                    raise ValueError("Selected window estimates do not reproduce main M4")
    if (
        file_hash(main / "development/policy-lock.json") != main_lock_hash
        or file_hash(main / "evaluation/result.json") != main_result_hash
    ):
        raise ValueError("The locked main result changed during follow-up")
    report = {
        "complete": True,
        "stage": registration["stage"],
        "designation": "exploratory ablation",
        "budget": budget,
        "test_draws_per_policy": draws,
        "population_size": len(ids),
        "reference_prevalence": truth,
        "results": summaries,
        "comparisons": comparisons,
        "selected_alphas": selection["selected_alphas"],
        "independent_checks": checks,
        "main_result_unchanged": True,
        "test_plans_saved_before_query": True,
        "selected_main_window_reproduced": stage == "windows",
        "registration_sha256": file_hash(registration_path),
        "policy_lock_sha256": file_hash(selection_path),
        "main_result_sha256": main_result_hash,
    }
    (output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    return report
