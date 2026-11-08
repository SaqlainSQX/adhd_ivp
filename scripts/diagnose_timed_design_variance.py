"""Post-hoc evaluation-only variance explanation; never chooses a sampler."""

import json
from pathlib import Path

import numpy as np

from gaze_audit.followups import load_main
from gaze_audit.frame_study import file_hash, make_design, read_references
from gaze_audit.strengthening import write_json

cfg = json.loads(Path("configs/timed-research-d-v1.json").read_text())
root = Path(cfg["output"])
destination = root / "posthoc-exact-design-variance.json"
if destination.exists():
    raise ValueError("Preserve previous diagnostic")
_, _, tables, _ = load_main(Path(cfg["main_run"]), Path(cfg["processed"]))
table = tables["static"][tables["static"].split.eq("test")].reset_index(drop=True)
refs = read_references(Path(cfg["processed"]), tuple(table.record_id))
y = np.array([refs[k] for k in table.record_id], float)
q = table.f_q.to_numpy(float)
rows = []
for row in json.loads((root / "query-manifest.json").read_text()):
    name = row["policy"]
    if name == "power-uniform":
        groups, sd = np.zeros(len(q), int), np.ones(1)
    else:
        k = "K4" if name == "power-score" else name
        policy = json.loads((root / f"{k}-training.json").read_text())
        groups = np.searchsorted(policy["cuts"], q, side="left")
        sd = np.array(policy["sd"])
    pop, counts = make_design(groups, sd, row["budget"], row["alpha"])
    components = []
    for p, n in zip(pop, counts, strict=True):
        size = len(p)
        residual = y[list(p)] - row["weight"] * q[list(p)]
        variance = float(residual.var(ddof=1)) if size > 1 else 0.0
        components.append((size / len(q)) ** 2 * (1 - n / size) * variance / n)
    rows.append(
        dict(
            policy=name,
            budget=row["budget"],
            exact_design_rmse_pp=float(np.sqrt(sum(components)) * 100),
        )
    )
write_json(
    destination,
    dict(
        designation="post-hoc evaluation-only diagnostic",
        explanation="For each frozen design the estimator is design-unbiased; exact "
        "design RMSE is sqrt of finite-population stratified residual variance. Full "
        "test labels are used only here for explanation; no new policy or test-based "
        "lambda is selected.",
        rows=rows,
        result_sha256=file_hash(root / "result.json"),
    ),
)
print("Saved full-population variance explanation for 24 frozen designs.")
