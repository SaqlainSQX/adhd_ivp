# X01 block continuation status

F is complete and synced on codex/weighted-intervals-f-v1 at9a3470f. Its primary
width improvement is2.59%, below the registered10% target. Do not add more F
recipes. The user's standing10-minute research prompt remains active.

G1 protocol/config: X01_BLOCK_PILOT_G.md, configs/block-pilot-g-v1.json. Current
stage: G1/G2 and research-demo extension H completed; feasibility review I is next. Read
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

G2 protocol/config: X01_BLOCK_GUIDANCE_G2.md and configs/block-guidance-g2-v1.json.
G2 completed48,000 test method evaluations plus3,600 validation candidate draws;
all passed separate verification of public partitions/OOF scores, training SDs,
alpha choice, query RNG, point/FPC variance, bounded endpoints, costs, summaries
and112 bootstrap comparisons. All12 alpha selections are1. No model was refit.

Primary L5/B1032 T/S ratio1.113855 [1.038896,1.203388]: temporal is worse, not a
registered10% improvement. RMSE Q/S/T is0.474055/0.536961/0.598097 pp; uniform
G1 is1.165998. Guidance helps relative to uniform blocks, but L5/Q remains2.1972
times the G2 L1/Q RMSE. AtL10/B4126 normal coverage Q/S/T is0.713/0.446/0.391;
bounded references are broad. Retain every loss and cost tail; do not propose
another arbitrary learner/window/grid to rescue temporal guidance.

G2 runtime63.3 seconds, CPU only.58 tests and Ruff pass. New figure visually
reviewed. No numerical failure or version repair occurred. Raw root:
outputs/experiments/block-guidance-g2-20261108-v1; tracked aggregates:
docs/research/g2-*. Report: reports/course-project/block-guidance-g2/results.md.
Review branch: codex/block-guidance-g2-v1. Main remains59fb784.

```powershell
.venv/Scripts/python.exe scripts/run_block_guidance.py *> outputs/g2-run-v1.log
.venv/Scripts/python.exe scripts/validate_block_guidance.py *> outputs/g2-independent-v1.log
.venv-mtgs/Scripts/python.exe scripts/report_block_guidance.py *> outputs/g2-report-v1.log
.venv/Scripts/python.exe -m pytest -q --basetemp outputs/pytest-g2-v1
.venv/Scripts/ruff.exe check src scripts tests
```

H is completed and checked; see RESEARCH_DEMO_H_STATUS.md. The research explorer
is available on localhost8766 with portable aggregates, sampled-only D replay,
cost/coverage/source-loss views and a course walkthrough. Original explorer and
scientific evidence remain unchanged. Next is the feasibility/provenance audit
in EXTERNAL_VALIDATION_REVIEW_I.md. No G2 computation remains active. Keep the
standing10-minute prompt active and continue from actual files/process state.

No source-held-out generalization or human time-saving claim is justified.
