# F interval comparison: complete

The registered public-weight interval comparison is complete. Main/A/B/C/D/E
results, point estimates, labels and queries remain unchanged. No new GPU work.

Primary inverse-fraction score-K4 width ratio0.974098 [0.974015,0.974180], only
2.59% less width and below the predeclared10% descriptive target. Mean primary
width8.69777 ->8.47248 pp, empirical coverage0.996 ->1.000 on1,000 saved draws.
The secondary inverse-sqrt-count recipe gives8.44195 pp/coverage0.999; it does
not become the primary winner after seeing outcomes. M4 has a secondary width
reduction10.4595 ->9.2813 pp, but the interval remains broad and its point-error
result is unchanged. Single-stratum uniform intervals reproduce identically.

All48,000 integer endpoint cases (4designs ×4budgets ×3recipes ×1000) passed
separate allocation/endpoint/tail/summary checks. Every equal recipe reproduces
accepted old intervals. Primary paired width bootstrap independently reproduced.
54 tests pass; Ruff passes. The three-panel width figure was visually reviewed.
The established union-bound construction provides fixed-design finite-population
coverage, not an independent-video or clinical claim, and not a centered normal
interval repair. Every recipe, budget, miss and point-outside rate is retained.

Protocol frozen atd0aa034, implementation6439f56. First v1 runner failed at an
output container initialized as a dictionary; no result was accepted. Its output
root/status and log are preserved. Versioned repaird1744d6 changes only that
container and adds config CLI; v2 retains identical comparisons and endpoints.
Accepted CPU runtime8.43 seconds, excluding separate checking/reporting.

Accepted root:`outputs/experiments/weighted-f-20261108-v2`.
Failed root:`outputs/experiments/weighted-f-20261108-v1`.
Report:[weighted-f/results.md](../reports/course-project/weighted-f/results.md).
Review branch:`codex/weighted-intervals-f-v1`.

```powershell
.venv/Scripts/python.exe scripts/run_weighted_intervals.py --config configs/weighted-intervals-f-v2.json *> outputs/weighted-f-run-v2.log
.venv/Scripts/python.exe scripts/validate_weighted_intervals.py *> outputs/weighted-f-validation-v2.log
.venv-mtgs/Scripts/python.exe scripts/report_weighted_intervals.py *> outputs/weighted-f-report-v2.log
.venv/Scripts/python.exe -m pytest -q --basetemp outputs/pytest-weighted-f-v1
.venv/Scripts/ruff.exe check src scripts tests
```

Existing numerical/verification roots refuse overwrite; a reproduction needs a
new config/output and verifier path. Aggregates and hashes are tracked under
`docs/research/weighted-f-*`; raw label/query arrays remain local and ignored.
The standing10-minute research continuation remains active. Next: X01 block
feasibility and synthetic checks, per CONTINUOUS_RESEARCH_QUEUE.md. Do not add
more interval recipes to chase a positive primary result on the same corpus.
