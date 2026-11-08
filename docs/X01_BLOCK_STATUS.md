# X01 block continuation status

F is complete and synced on codex/weighted-intervals-f-v1 at9a3470f. Its primary
width improvement is2.59%, below the registered10% target. Do not add more F
recipes. The user's standing10-minute research prompt remains active.

G1 protocol/config: X01_BLOCK_PILOT_G.md, configs/block-pilot-g-v1.json. Current
stage: G1 completed and checked; G2 guidance comparison is next. Read
actual outputs/experiments/block-g-20261108-v1/status.json and logs before
continuing; never duplicate an active run. G1 numerical results are accepted.
G1 uses frozen q, lengths1/2/5/10, weights1/.5, matched expected label budgets,
32,000 method-draw evaluations completed. No new GPU inference or model fitting.

G1 result: L5/L1 lambda1 RMSE ratio2.10893 [1.97818,2.23823] atB1032;
RMSE1.1660 vs0.5529 pp. All lengths>1 lose at equal expected label cost.
The fixed weight0.5 helps relative to weight1 but does not reverse the block loss.
L5 has mean4.875 frames/block and about211.7 queried blocks atB1032 rather than
1032 singleton tasks. Realized frame-label cost varies around1032; no human-time
benefit is measured or inferred. All lengths, costs, coverage and bias are retained.

The public inventory partitions every eligible frame exactly once and breaks
gaps/pairs/clips. Test10316 frames form115 contiguous runs; requested L2/L5/L10
produce5186/2116/1092 blocks. Train191956 and validation25139 frames retained.
All32000 estimates passed independent RNG/point/algebraic variance checks;
length1 reproduces original M2 queries/points. Saved-output statistics, actual
cost arrays, normal interval summaries and primary bootstrap passed separate
checks.56 tests/Ruff pass; figure visually reviewed. CPU runner13.4 seconds.
No numerical failure occurred in G1. Report-only lint fixes changed no outcomes.
Raw queries and block mappings remain local/ignored; tracked evidence is under
docs/research/block-g-*. Report: reports/course-project/block-g/results.md.

```powershell
.venv/Scripts/python.exe scripts/run_block_pilot.py *> outputs/block-g-run-v1.log
.venv-mtgs/Scripts/python.exe scripts/report_block_pilot.py *> outputs/block-g-report-v2.log
.venv/Scripts/python.exe -m pytest -q --basetemp outputs/pytest-block-g-v1
.venv/Scripts/ruff.exe check src scripts tests
```

Next: register and implement G2 static-versus-temporal block guidance per G1's
fixed recipe. Existing five-fold OOF score files are in the main development
folder; do not refit or replace the main policies. G1 does not select G2's length
or weight on test. After X01, proceed to the local-demo extension in the standing
queue. No source-held-out generalization or human time-saving claim is justified.
