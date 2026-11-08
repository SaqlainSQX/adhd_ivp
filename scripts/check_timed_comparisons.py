"""Check shared query streams, all bootstrap comparisons and prior tracked evidence."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from gaze_audit.extra_experiments import frozen_inputs
from gaze_audit.frame_study import file_hash
from gaze_audit.strengthening import write_json

cfg = json.loads(Path("configs/timed-research-d-v1.json").read_text())
main, simple, processed = frozen_inputs(cfg)
root = Path(cfg["output"])
result = json.loads((root / "result.json").read_text())
lock = json.loads((root / "policy-lock.json").read_text())
data = pd.read_csv(root / "draw-results.csv")
truth = result["reference_prevalence"]
if (root / "comparison-validation.json").exists():
    raise ValueError("Preserve verification evidence")
for budget in [516, 1032, 2063, 4126]:
    uniform = np.load(root / f"queries-power-uniform-b{budget}.npz")["selected"]
    original = np.load(main / f"evaluation/queries-uniform-b{budget}.npz")["selected"]
    assert np.array_equal(uniform, original)
    if lock["selected_alpha"]["K4"]["alpha"] == lock["frozen_q_alpha"]:
        score = np.load(root / f"queries-power-score-b{budget}.npz")["selected"]
        control = np.load(root / f"queries-K4-b{budget}.npz")["selected"]
        assert np.array_equal(score, control)
main_draws = pd.read_csv(main / "evaluation/draw-results.csv")
for name, comparison in result["comparisons"].items():
    left, right = name.split("/")
    policy, budget_text = left.rsplit("-b", 1)
    budget = int(budget_text)
    numerator = data[(data.policy == policy) & (data.budget == budget)].sort_values("draw")
    if right == "M2":
        denominator = main_draws[
            (main_draws.method == "M2") & (main_draws.budget == budget)
        ].sort_values("draw")
    else:
        denominator = data[(data.policy == "K4") & (data.budget == budget)].sort_values("draw")
    a = (numerator.prevalence.to_numpy() - truth) ** 2
    b = (denominator.prevalence.to_numpy() - truth) ** 2
    rng = np.random.default_rng(cfg["bootstrap_seed"])
    draws = rng.integers(len(a), size=(cfg["bootstrap_resamples"], len(a)))
    ratios = np.sqrt(a[draws].mean(axis=1) / b[draws].mean(axis=1))
    assert abs(np.sqrt(a.mean() / b.mean()) - comparison["rmse_ratio"]) < 1e-12
    assert np.allclose(
        np.quantile(ratios, [0.025, 0.975]), comparison["draw_bootstrap_95pct"], rtol=0, atol=1e-12
    )

checks = []
for file in [
    "docs/research/extra-c-evidence-manifest.json",
    "docs/research/strengthening-evidence-manifest.json",
]:
    manifest = json.loads(Path(file).read_text())
    for filename, expected in manifest["files"].items():
        content = Path(filename).read_bytes()
        if Path(filename).suffix.lower() not in [".png", ".jpg", ".jpeg"]:
            content = content.replace(b"\r\n", b"\n")
        assert hashlib.sha256(content).hexdigest() == expected, filename
    checks.append(dict(manifest=file, files=len(manifest["files"]), status="passed"))
write_json(
    root / "comparison-validation.json",
    dict(
        status="passed",
        comparisons=len(result["comparisons"]),
        shared_query_cases=8,
        prior_manifests=checks,
        result_sha256=file_hash(root / "result.json"),
        scope_note="D1 score/K4 and uniform/M2 reuse exact queries; K settings use "
        "common stream21 with different designs. Generic inherited streams-differ "
        "wording in raw result is imprecise; arrays and bootstrap values are checked.",
    ),
)
print("Shared query arrays, all comparisons and prior evidence verified.")
