# Extra experiments: completed round C

The accepted course submission remains on `main` at `59fb784`. The new round,
including every loss and tie, is saved on `codex/extra-experiments-v1`.

All C1/C2/C3 stages are complete. Independent recomputation passed for 32,000
test evaluations and 2,400 validation candidate evaluations; source-nested label
subsets were reconstructed. All 47 tests and Ruff pass. Three new figures were
visually checked. Frozen main/B1 results, policies and source folds are unchanged.

## What is worth adding to the presentation?

Add one exploratory slide showing downstream calibration-label cost. At the
primary 1,032-label audit budget, 9,599 training labels (5%) give RMSE 0.2120 pp,
versus 0.2148 with all 191,956 labels. The ratio is 0.9867 [0.9422,1.0347] on
this fixed corpus. All 25,139 validation labels and the pretrained MTGS backbone
remain in use; this is not a cold-start or measured annotation-time result.

Keep the learner changes in the appendix. Ridge-static approximately ties the
score control; neither Ridge nor squared-residual RF reaches the registered
10% primary RMSE gain against that control. Some secondary-budget normal
interval failures remain severe. The squared RF has a secondary conservative-
interval width tradeoff, not a primary accuracy win.

Full tables, uncertainty, cost curves and all outcomes:
[round-C report](../reports/course-project/extra-c/results.md).
Protocol: [EXTRA_EXPERIMENTS_C.md](EXTRA_EXPERIMENTS_C.md).
Aggregate verification: [evidence manifest](research/extra-c-evidence-manifest.json).

## Reproduction and files

```powershell
.\.venv\Scripts\python.exe -u scripts/run_extra_experiments.py all
.\.venv\Scripts\python.exe scripts/validate_extra_experiments.py
.\.venv-mtgs\Scripts\python.exe scripts/report_extra_experiments.py
```

These document the completed run; existing outputs refuse overwrite. To reproduce,
copy `configs/extra-experiments-c-v1.json`, change its output root, and pass that
config to all three scripts. Keep registered inputs, settings and seed streams.
The original root is `outputs/experiments/extra-c-20261107-v1`, with durable
status, execution/validation logs, policy/query locks and fit progress. Raw labels,
source-nested selected IDs, query arrays, OOF vectors and models remain ignored.
No experiment or GPU job is left queued for this round. The earlier demo remains
unchanged and its server is separate from the completed CPU experiments.
