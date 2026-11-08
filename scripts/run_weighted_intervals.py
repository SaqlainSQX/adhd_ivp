"""Run the registered F interval extension on immutable saved query streams."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from gaze_audit.followups import load_main
from gaze_audit.frame_study import file_hash, read_references
from gaze_audit.strengthening import write_json
from gaze_audit.weighted_intervals import public_error_allocation, weighted_binary_totals

started = time.monotonic()
config_path = Path("configs/weighted-intervals-f-v1.json")
cfg = json.loads(config_path.read_text())
main, previous, out = [Path(cfg[k]) for k in ["main", "input", "output"]]
if out.exists():
    raise ValueError("Preserve existing output; register a new version")
assert file_hash(main / "evaluation/result.json") == cfg["main_result_sha256"]
assert file_hash(previous / "result.json") == cfg["input_result_sha256"]
_, _, tables, hashes = load_main(main, Path(cfg["processed"]))
table = tables["static"][tables["static"].split.eq("test")].reset_index(drop=True)
index = pd.read_csv(previous / "population_index.csv")
assert table.record_id.tolist() == index.record_id.tolist()
out.mkdir(parents=True)
registration = dict(
    config=cfg,
    config_sha256=file_hash(config_path),
    protocol_sha256=file_hash(Path(cfg["protocol"])),
    implementation_sha256=file_hash(Path("src/gaze_audit/weighted_intervals.py")),
    runner_sha256=file_hash(Path(__file__)),
    feature_hashes=hashes,
    started_utc=datetime.now(timezone.utc).isoformat(),
)
write_json(out / "registration.json", registration)
designs = []
for path, origin in [
    (main / "evaluation/query-manifest.json", "main"),
    (previous / "query-manifest.json", "D"),
]:
    for row in json.loads(path.read_text()):
        name = row.get("design", row.get("policy"))
        if (origin == "main" and name not in ["M3", "M4"]) or (
            origin == "D" and name not in ["K4", "power-uniform"]
        ):
            continue
        source = path.parent / row["file"]
        assert file_hash(source) == row["sha256"]
        sizes = row["stratum_sizes"] if origin == "main" else row["sizes"]
        counts = row["stratum_counts"] if origin == "main" else row["counts"]
        designs.append(
            dict(
                design=name,
                budget=row["budget"],
                file=str(source),
                sha256=row["sha256"],
                sizes=sizes,
                counts=counts,
                allocations={
                    r: public_error_allocation(sizes, counts, r).tolist() for r in cfg["recipes"]
                },
            )
        )
write_json(out / "public-allocation-lock.json", dict(designs=designs, labels_used=False))
# All error allocations are fixed and written before this stage opens references.
refs = read_references(Path(cfg["processed"]), tuple(table.record_id))
y = np.array([refs[k] for k in table.record_id], int)
truth_total = int(y.sum())
point_main = pd.read_csv(main / "evaluation/draw-results.csv")
point_d = pd.read_csv(previous / "draw-results.csv")
exact_main = pd.read_csv(
    "outputs/experiments/strengthening-20261107-v1/B2b-exact-reference-v2/interval-draws.csv"
)
summaries, rows, primary = {}, {}, {}
for entry in designs:
    name, budget = entry["design"], entry["budget"]
    saved = np.load(entry["file"])
    selected = saved["selected"]
    assert selected.shape == (1000, budget)
    assert np.array_equal(saved["counts"], entry["counts"])
    bounds = np.r_[0, np.cumsum(entry["counts"])]
    successes = np.stack(
        [y[selected[:, a:b]].sum(axis=1) for a, b in zip(bounds[:-1], bounds[1:], strict=True)],
        axis=1,
    )
    for recipe in cfg["recipes"]:
        endpoints = np.array(
            [weighted_binary_totals(k, entry["counts"], entry["sizes"], recipe) for k in successes]
        )
        lo, hi = endpoints[:, 0], endpoints[:, 1]
        width = (hi - lo) / len(y) * 100
        covered = (lo <= truth_total) & (hi >= truth_total)
        if name in ["M3", "M4"]:
            points = (
                point_main[(point_main.method == name) & (point_main.budget == budget)]
                .sort_values("draw")
                .prevalence.to_numpy()
            )
        else:
            points = (
                point_d[(point_d.policy == name) & (point_d.budget == budget)]
                .sort_values("draw")
                .prevalence.to_numpy()
            )
        summary = dict(
            coverage=float(covered.mean()),
            missed_total_draws=int((~covered).sum()),
            mean_width_pp=float(width.mean()),
            width_quantiles_pp=np.quantile(width, [0, 0.05, 0.5, 0.95, 1]).tolist(),
            point_outside_rate=float(np.mean((points * len(y) < lo) | (points * len(y) > hi))),
        )
        if name == "K4":
            power = (
                point_d[(point_d.policy == "power-score") & (point_d.budget == budget)]
                .sort_values("draw")
                .prevalence.to_numpy()
            )
            summary["power_score_point_outside_rate"] = float(
                np.mean((power * len(y) < lo) | (power * len(y) > hi))
            )
        if recipe == "equal":
            if name in ["M3", "M4"]:
                base = exact_main[
                    (exact_main.method == name) & (exact_main.budget == budget)
                ].sort_values("draw")
            else:
                base = point_d[(point_d.policy == name) & (point_d.budget == budget)].sort_values(
                    "draw"
                )
            assert np.array_equal(lo, base.lower_total) and np.array_equal(hi, base.upper_total)
        summaries[f"{name}-b{budget}-{recipe}"] = summary
        rows.append(
            pd.DataFrame(
                dict(
                    design=name,
                    budget=budget,
                    recipe=recipe,
                    draw=np.arange(1000),
                    lower_total=lo,
                    upper_total=hi,
                )
            )
        )
        if name == "K4" and budget == 1032:
            primary[recipe] = width
        print(
            f"{name} B{budget} {recipe}: coverage{summary['coverage']:.3f}, "
            f"width{width.mean():.4f}pp",
            flush=True,
        )
pd.concat(rows, ignore_index=True).to_csv(out / "interval-results.csv", index=False)
rng = np.random.default_rng(cfg["bootstrap_seed"])
indices = rng.integers(1000, size=(cfg["bootstrap_resamples"], 1000))
ratios = primary["inverse-fraction"][indices].mean(axis=1) / primary["equal"][indices].mean(axis=1)
comparison = dict(
    mean_width_ratio=float(primary["inverse-fraction"].mean() / primary["equal"].mean()),
    draw_bootstrap_95pct=np.quantile(ratios, [0.025, 0.975]).tolist(),
    scope="Fixed corpus and saved draws; not new-source uncertainty",
)
assert (
    file_hash(Path("src/gaze_audit/weighted_intervals.py")) == registration["implementation_sha256"]
)
assert file_hash(main / "evaluation/result.json") == cfg["main_result_sha256"]
assert file_hash(previous / "result.json") == cfg["input_result_sha256"]
result = dict(
    complete=True,
    designation=cfg["designation"],
    interval_cases=sum(len(r) for r in rows),
    results=summaries,
    primary=comparison,
    new_queries=0,
    all_equal_intervals_reproduced=True,
    elapsed_seconds=time.monotonic() - started,
    registration_sha256=file_hash(out / "registration.json"),
    allocation_lock_sha256=file_hash(out / "public-allocation-lock.json"),
)
write_json(out / "result.json", result)
write_json(out / "status.json", dict(state="completed", interval_cases=result["interval_cases"]))
