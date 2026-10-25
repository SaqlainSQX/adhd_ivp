"""Offline audit runner. Test truth is used only after plans and queries are fixed."""

import hashlib
import importlib.metadata
import json
import platform
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from .data import assert_disjoint_sources, make_blocks
from .estimation import estimate
from .oracle import LabelOracle, reference_prevalence
from .policy import draw_plan, fit_policy


def generate_demo(root: Path, seed: int) -> None:
    """Generate invented scores and labels, never an MTGS or ChildPlay result."""
    rng = np.random.default_rng(seed)
    root.mkdir(parents=True, exist_ok=False)
    for split, count in [("train", 24), ("validation", 12), ("test", 12)]:
        rows, labels = [], []
        for source in range(count):
            bias = rng.uniform(0.01, 0.09)
            for frame in range(160):
                phase = np.sin(frame / 14 + source)
                truth = np.clip(bias + 0.035 * phase, 0.002, 0.2)
                score = np.clip(0.065 + 0.04 * phase + rng.normal(0, 0.012), 0.001, 0.99)
                record_id = f"{split}-{source:03d}-{frame:04d}"
                rows.append(
                    {
                        "record_id": record_id,
                        "source_id": f"{split}-{source:03d}",
                        "clip_id": f"clip-{source:03d}",
                        "frame_index": frame,
                        "person_a": 1,
                        "person_b": 2,
                        "probability": score,
                    }
                )
                labels.append({"record_id": record_id, "label": int(rng.random() < truth)})
        folder = root / split
        folder.mkdir()
        pd.DataFrame(rows).to_csv(folder / "predictions.csv", index=False)
        pd.DataFrame(labels).to_csv(folder / "labels.csv", index=False)
    (root / "provenance.json").write_text(
        json.dumps(
            {
                "synthetic": True,
                "predictor": "synthetic-generator-v1",
                "seed": seed,
                "description": "Invented scores and labels for software verification only",
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def run_audit(
    root: Path,
    output: Path,
    *,
    draws: int = 100,
    seed: int = 42,
    block_length: int = 5,
    budgets: tuple = (0.05, 0.1, 0.2, 0.4),
) -> dict:
    if draws < 1 or not budgets or any(not 0 < x <= 1 for x in budgets):
        raise ValueError("Require positive draws and budget fractions in (0, 1]")
    if output.exists():
        raise ValueError("Output directory already exists; choose a new run directory")
    provenance = json.loads((root / "provenance.json").read_text(encoding="utf-8"))
    if provenance.get("synthetic") is not True:
        required = ["predictor", "checkpoint_sha256", "upstream_revision", "configuration_sha256"]
        if any(
            not isinstance(provenance.get(k), str) or not provenance[k].strip() for k in required
        ):
            raise ValueError(
                "Real caches require predictor and pinned checkpoint/config/code provenance"
            )
        for key in ["media_alignment_verified", "source_checkpoint_separation_reviewed"]:
            if provenance.get(key) is not True:
                raise ValueError(f"Real cache requires explicit provenance attestation: {key}")
    blocks, oracles, truth, hashes = {}, {}, {}, {}
    for split in ["train", "validation", "test"]:
        prediction_path = root / split / "predictions.csv"
        label_path = root / split / "labels.csv"
        prediction_frame = pd.read_csv(
            prediction_path,
            dtype={
                "record_id": str,
                "source_id": str,
                "clip_id": str,
            },
        )
        reference = pd.read_csv(label_path, dtype={"record_id": str})
        blocks[split] = make_blocks(prediction_frame, block_length)
        ids = {r for block in blocks[split] for r in block.record_ids}
        oracles[split] = LabelOracle(reference, ids)
        truth[split] = reference_prevalence(reference)
        for path in [prediction_path, label_path]:
            hashes[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    hashes["provenance.json"] = hashlib.sha256((root / "provenance.json").read_bytes()).hexdigest()
    assert_disjoint_sources(blocks)
    train_labels = oracles["train"].query(blocks["train"], seed=seed, purpose="risk-fit")
    policy = fit_policy(blocks["train"], train_labels, seed)
    # Validation is fully purchased development data. Never charge it to the test query budget.
    oracles["validation"].query(blocks["validation"], seed=seed, purpose="policy-validation")
    validation_strata = policy.strata(blocks["validation"])
    val_cost = sum(b.cost for b in blocks["validation"])
    tuning = []
    for mix in [0.0, 0.25, 0.5, 0.75, 1.0]:
        squared_errors = []
        for draw in range(20):
            plan = draw_plan(
                blocks["validation"],
                validation_strata,
                policy.residual_sd,
                val_cost * 0.2,
                mix,
                seed + 10000 + draw,
            )
            selected = [blocks["validation"][i] for h in plan for i in h.selected]
            queried = oracles["validation"].query(
                selected, seed=seed + 10000 + draw, purpose=f"validation-mix-{mix}"
            )
            value = estimate(blocks["validation"], plan, queried)
            squared_errors.append((value.prevalence - truth["validation"]) ** 2)
        tuning.append({"mix": mix, "mse": float(np.mean(squared_errors))})
    mix = min(tuning, key=lambda item: item["mse"])["mix"]
    test = blocks["test"]
    population_cost = sum(b.cost for b in test)
    risk_strata = policy.strata(test)
    # Entropy cut points use training predictions only; this baseline also draws at random.
    entropy_cuts = np.unique(
        np.quantile([b.features[3] for b in blocks["train"]], [0.25, 0.5, 0.75])
    )
    entropy_strata = np.searchsorted(entropy_cuts, [b.features[3] for b in test])
    methods = {
        "human_uniform_blocks": (np.zeros(len(test), dtype=int), np.ones(1), 0.0, True),
        "residual_uniform_blocks": (np.zeros(len(test), dtype=int), np.ones(1), 0.0, False),
        "entropy_blocks": (entropy_strata, np.arange(1, len(entropy_cuts) + 2), 1.0, False),
        "temporal_risk_blocks": (risk_strata, policy.residual_sd, mix, False),
    }
    output.mkdir(parents=True)
    rows = []
    with (output / "queries.jsonl").open("w", encoding="utf-8") as log:
        for fraction in budgets:
            for method, (strata, sd, allocation_mix, human_only) in methods.items():
                for draw in range(draws):
                    draw_seed = seed + draw
                    context = {"method": method, "budget_fraction": fraction, "draw": draw}
                    try:
                        plan = draw_plan(
                            test, strata, sd, population_cost * fraction, allocation_mix, draw_seed
                        )
                    except ValueError as exc:
                        rows.append({**context, "failure": str(exc)})
                        continue
                    selected = [test[i] for h in plan for i in h.selected]
                    offset = len(oracles["test"].log)
                    queried = oracles["test"].query(selected, seed=draw_seed, purpose=method)
                    value = estimate(test, plan, queried, human_only)
                    # Full plan is fixed before the oracle returns selected values.
                    for entry, stratum_plan in zip(
                        oracles["test"].log[offset:],
                        [part for part in plan for _ in part.selected],
                        strict=True,
                    ):
                        log.write(
                            json.dumps(
                                {
                                    **context,
                                    **entry,
                                    "stratum": stratum_plan.stratum,
                                    "conditional_inclusion_probability": (
                                        len(stratum_plan.selected) / len(stratum_plan.population)
                                    ),
                                    "expected_stratum_blocks": stratum_plan.expected_blocks,
                                    "population_stratum_blocks": len(stratum_plan.population),
                                    "selected_stratum_blocks": len(stratum_plan.selected),
                                }
                            )
                            + "\n"
                        )
                    rows.append(
                        {
                            **context,
                            **value.as_dict(),
                            "failure": "",
                            "error_pp": 100 * (value.prevalence - truth["test"]),
                            "covered": value.ci_low <= truth["test"] <= value.ci_high,
                            "width_pp": 100 * (value.ci_high - value.ci_low),
                        }
                    )
    audits = pd.DataFrame(rows)
    audits.to_csv(output / "audits.csv", index=False)
    summaries = []
    for (method, fraction), group in audits.groupby(["method", "budget_fraction"]):
        successful = group.loc[group.failure == ""]
        summary = {
            "method": method,
            "budget_fraction": float(fraction),
            "successful_draws": len(successful),
            "failed_draws": len(group) - len(successful),
        }
        if len(successful):
            coverage = float(successful.covered.mean())
            summary.update(
                {
                    "bias_pp": float(successful.error_pp.mean()),
                    "rmse_pp": float(np.sqrt(np.mean(successful.error_pp**2))),
                    "bias_mcse_pp": float(
                        successful.error_pp.std(ddof=1) / np.sqrt(len(successful))
                    )
                    if len(successful) > 1
                    else None,
                    "coverage": coverage,
                    "coverage_mcse": float(np.sqrt(coverage * (1 - coverage) / len(successful))),
                    "mean_width_pp": float(successful.width_pp.mean()),
                    "mean_labels": float(successful.labels_revealed.mean()),
                    "min_labels": int(successful.labels_revealed.min()),
                    "max_labels": int(successful.labels_revealed.max()),
                }
            )
        summaries.append(summary)
    pd.DataFrame(summaries).to_csv(output / "summary.csv", index=False)
    try:
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        revision = None
    report = {
        "synthetic": provenance.get("synthetic") is True,
        "provenance": provenance,
        "input_sha256": hashes,
        "git_revision": revision,
        "python": platform.python_version(),
        "versions": {p: importlib.metadata.version(p) for p in ["numpy", "pandas", "scikit-learn"]},
        "seed": seed,
        "draws": draws,
        "block_length": block_length,
        "budgets": list(budgets),
        "selected_mix": mix,
        "validation_tuning": tuning,
        "risk_cut_points": policy.cut_points.tolist(),
        "residual_sd": policy.residual_sd.tolist(),
        "risk_model_parameters": policy.model.get_params(),
        "test_records": population_cost,
        "test_blocks": len(test),
        "test_reference_prevalence": truth["test"],
        "model_only_prevalence": sum(b.q_sum for b in test) / population_cost,
        "development_labels": sum(b.cost for s in ["train", "validation"] for b in blocks[s]),
        "summary": summaries,
        "limitations": [
            "Normal intervals are approximate; rare events can cause severe undercoverage.",
            "Budgets constrain expected label count, not a hard realized cap.",
            "Audit repetitions measure sampling uncertainty on one fixed corpus, not transfer.",
            "Only initial block baselines implemented; full deck comparison suite remains pending.",
        ],
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False), encoding="utf-8"
    )
    with (output / "development_queries.jsonl").open("w", encoding="utf-8") as log:
        for split in ["train", "validation"]:
            for entry in oracles[split].log:
                log.write(json.dumps({"split": split, **entry}) + "\n")
    return report
