"""Separate public-weight, integer endpoint and saved-summary verification."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from gaze_audit.exact_intervals import checked_binary_interval
from gaze_audit.followups import load_main
from gaze_audit.frame_study import file_hash, read_references
from gaze_audit.strengthening import write_json

cfg = json.loads(Path("configs/weighted-intervals-f-v2.json").read_text())
root = Path(cfg["output"])
destination = root / "independent-validation.json"
if destination.exists():
    raise ValueError("Preserve accepted verification")
r = json.loads((root / "result.json").read_text())
reg = json.loads((root / "registration.json").read_text())
assert file_hash(Path("src/gaze_audit/weighted_intervals.py")) == reg["implementation_sha256"]
assert file_hash(Path("scripts/run_weighted_intervals.py")) == reg["runner_sha256"]
assert file_hash(root / "public-allocation-lock.json") == r["allocation_lock_sha256"]
_, _, tables, _ = load_main(Path(cfg["main"]), Path(cfg["processed"]))
table = tables["static"][tables["static"].split.eq("test")].reset_index(drop=True)
refs = read_references(Path(cfg["processed"]), tuple(table.record_id))
y = np.array([refs[k] for k in table.record_id], int)
data = pd.read_csv(root / "interval-results.csv")
assert len(data) == 48000 == r["interval_cases"]
checks = []
primary = {}
for entry in json.loads((root / "public-allocation-lock.json").read_text())["designs"]:
    sizes, counts = np.array(entry["sizes"]), np.array(entry["counts"])
    active = counts < sizes
    assert file_hash(Path(entry["file"])) == entry["sha256"]
    selected = np.load(entry["file"])["selected"]
    ends = np.r_[0, np.cumsum(counts)]
    successes = np.stack(
        [y[selected[:, a:b]].sum(axis=1) for a, b in zip(ends[:-1], ends[1:], strict=True)], axis=1
    )
    for recipe in cfg["recipes"]:
        weights = np.zeros(len(sizes))
        if recipe == "equal":
            weights[active] = 1.0
        elif recipe == "inverse-fraction":
            weights[active] = sizes[active] / counts[active]
        else:
            weights[active] = sizes[active] / np.sqrt(counts[active])
        if active.any():
            weights *= 0.05 / weights.sum()
        assert np.allclose(weights, entry["allocations"][recipe], rtol=0, atol=1e-16)
        assert abs(weights.sum() - 0.05) < 1e-14 or not active.any()
        endpoints = np.zeros((1000, 2), dtype=int)
        for h, (size, n) in enumerate(zip(sizes, counts, strict=True)):
            for k in np.unique(successes[:, h]):
                if n == size:
                    lower = upper = int(k)
                else:
                    lo, hi = checked_binary_interval(int(k), int(n), int(size), float(weights[h]))
                    lower, upper = round(lo * size), round(hi * size)
                selected_success = successes[:, h] == k
                endpoints[selected_success, 0] += lower
                endpoints[selected_success, 1] += upper
        subset = data[
            (data.design == entry["design"])
            & (data.budget == entry["budget"])
            & (data.recipe == recipe)
        ].sort_values("draw")
        assert np.array_equal(subset.draw, np.arange(1000))
        assert np.array_equal(subset.lower_total, endpoints[:, 0])
        assert np.array_equal(subset.upper_total, endpoints[:, 1])
        width = (endpoints[:, 1] - endpoints[:, 0]) / len(y) * 100
        covered = (endpoints[:, 0] <= y.sum()) & (endpoints[:, 1] >= y.sum())
        s = r["results"][f"{entry['design']}-b{entry['budget']}-{recipe}"]
        assert s["coverage"] == float(covered.mean())
        assert abs(s["mean_width_pp"] - width.mean()) < 1e-12
        assert np.allclose(
            s["width_quantiles_pp"], np.quantile(width, [0, 0.05, 0.5, 0.95, 1]), rtol=0, atol=1e-12
        )
        if entry["design"] == "K4" and entry["budget"] == 1032:
            primary[recipe] = width
        checks.append(
            dict(
                design=entry["design"],
                budget=entry["budget"],
                recipe=recipe,
                cases=1000,
                status="passed",
            )
        )
index = np.random.default_rng(400006).integers(1000, size=(2000, 1000))
ratio = primary["inverse-fraction"][index].mean(axis=1) / primary["equal"][index].mean(axis=1)
assert np.allclose(
    np.quantile(ratio, [0.025, 0.975]), r["primary"]["draw_bootstrap_95pct"], rtol=0, atol=1e-12
)
write_json(
    destination,
    dict(
        status="passed",
        interval_cases=len(data),
        checks=checks,
        result_sha256=file_hash(root / "result.json"),
        allocation_lock_sha256=file_hash(root / "public-allocation-lock.json"),
        exact_endpoint_checks="Every distinct stratum success count checked against "
        "CDF/SF acceptance and adjacent integer tails",
        primary_bootstrap="reproduced",
    ),
)
print("Verified 48000 saved integer interval cases and primary comparison.")
