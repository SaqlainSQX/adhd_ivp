# Running the course experiment

The project is now executable on the downloaded, verified ChildPlay subset.
The design is in [COURSE_PROJECT_PLAN.md](COURSE_PROJECT_PLAN.md); actual status
is in [EXPERIMENT_TRACKER.md](EXPERIMENT_TRACKER.md).

## Current population and run

The frozen population is `data/raw/childplay/verified-population-v2`. It retains
53 of the 95 attempted public sources: 40 train, 3 validation and 10 test.
There are 191,956 train, 25,139 validation and 10,316 test eligible pair-frames.
Test budgets are 516, 1,032, 2,063 and 4,126 labels per audit.

Only this subset is the estimand. Unknown references, unavailable videos and
sources with unresolved alignment failures are excluded with recorded reasons.
The earlier `verified-population-v1` was withdrawn during visual review and must
not be used. The frame-count-discrepancy download pool is quarantined.

The November 7 continuation uses:

```text
outputs/inference/mtgs-strict-shard-v1/       Finished initial 37-source inference batch
outputs/inference/mtgs-remaining-shard-v1/    Finished remaining 17 sources
outputs/experiments/course-20261107-v1/      Completed main run; independent + visual QA passed
outputs/experiments/followups-20261107/      Registered A1 and A2 complete and checked
```

The first batch contains one subsequently excluded source. The merger explicitly
drops that source and records it, then requires exact coverage of every public
pair in the final population. The total retained source count remains 53.

The main run has state `complete` and all 20,000 sampled audits passed independent
validation. Five report figures and the replay timeline have passed visual review.
See [the results assessment](research/course-results.md) and the tracked evidence
under `docs/research/main-course-*`. No repeat GPU inference is needed.

For any new run, check its `pipeline-status.json` for the current stage.
A failed stage records its log and exit status; a waiting stage does not
mean the comparison has completed. `computed_waiting_for_visual_review` means
the computations and report files exist but their figures still need inspection.

## Environments

Use `.venv/Scripts/python.exe` for normalization, features, development policies,
sampling and tests. Use `.venv-mtgs/Scripts/python.exe` for CUDA inference and
Matplotlib report generation. Keep both environments local and ignored by Git.
The model runtime was checked with Python 3.13.1, PyTorch 2.11.0+cu128,
torchvision 0.26.0+cu128, timm 0.9.2, einops 0.6.0 and torch-geometric 2.7.0.
The local GPU is an RTX 4060 Laptop with 8 GiB. These are recorded execution
versions; installing a different runtime requires a new smoke/provenance check.

Original source code and model weights are external research dependencies, with
their own terms. The official MTGS checkpoint is pinned and converted into a
tensor-only state file. Its native social-gaze outputs use all provided real
tracks, temporal offsets -6,-3,0,3,6 and an image resolution of 448. The auxiliary
heatmap branch is omitted after an exact native-output parity check. All compared
sampling methods share this same frozen temporal predictor: “static guidance”
means current-frame error features, not a different static backbone.

## Continue inference

Do not launch a second GPU process while the saved inference process is running.
For a fresh run, use a new output directory:

```powershell
$taskSources = (Get-Content configs/remaining-inference-sources.json -Raw | ConvertFrom-Json).sources
.\.venv-mtgs\Scripts\python.exe -X utf8 -u scripts/infer_mtgs_cache.py `
  --acquisition data/raw/childplay/verified-population-v2 --sources $taskSources `
  --amp --runtime-lock outputs/inference/mtgs-smoke-cache-v1/inference-provenance.json `
  --output outputs/inference/NEW-SHARD
```

Inference reads public geometry and media only. It never reads the oracle CSV.
Every completed clip has an individual prediction file and SHA-256 in its
provenance file. Preserve a partial run rather than relabeling it complete.

## Sequential experiment

The recorded main driver has finished. For a separate reproduction,
use a new run directory and the relevant completed inference paths:

```powershell
.\.venv\Scripts\python.exe -X utf8 -u scripts/finish_course_experiment.py `
  --population data/raw/childplay/verified-population-v2 `
  --shards outputs/inference/mtgs-strict-shard-v1 outputs/inference/mtgs-remaining-shard-v1 `
  --run outputs/experiments/NEW-RUN
```

The driver waits for the declared inference manifests, verifies exact cache
coverage, builds label-free static/window-5/window-11 features, runs development
diagnostics, fits five-fold source-group error models, selects among nine
validation candidates, freezes a policy lock and evaluates M0–M5. M1/M2/M5 share
uniform query IDs. Every test query plan is saved before reference lookup.

Default validation selection uses 100 draws; final evaluation uses 1,000 draws
at each of four budgets, totaling 20,000 sampled method evaluations. The predictor
is not retrained. Temporal-policy selection uses validation only. The study is
exploratory because reference labels had already been inspected during feasibility
work and only three validation sources remain accessible.

The report includes RMSE, bias, coverage, interval width, source-domain
sensitivity and a contextual-surrogate control. A temporal loss or tie remains a
valid course-project outcome. Report generator checks are separate from visual
inspection; do not present synthetic software-test charts as ChildPlay results.

Before accepting a real pipeline report, `validate_experiment_run.py` independently
replays all saved random query streams and recomputes every point estimate,
finite-population variance and RMSE summary. It checks exact budgets, sampling
without replacement, frozen allocations and input hashes. Successful evidence is
saved as `independent-validation.json`; an inconsistency stops report generation.

## Replay and report

When a run completes, its directories contain:

| Directory | Contents |
| --- | --- |
| `cache` | Exact merged frozen predictions and provenance |
| `features` | Public static and temporal features with hashes |
| `development-checks` | Train/validation diagnostics and uniform baseline checks |
| `development` | Three fitted policies, OOF scores, nine candidates and immutable lock |
| `evaluation` | Saved query indices, draw results, all comparisons and source sensitivity |
| `replay` | Exact M4 draw-0 replay, revealed queries and a public timeline example |
| `report` | Markdown course report, tables, cost ledger and exportable PNG/SVG figures |

Replay verifies the saved RNG plan, oracle version, policy hash and estimate. The
public timeline contains frozen scores, temporal summaries and query marks;
revealed labels are in a separate file. Neither output is committed as raw data.

## Team synchronization

Tracked code, plans and aggregate evidence belong in GitHub. Data, credentials,
images, checkpoints and environments stay ignored. The project Kaggle launcher
isolates this account inside its child process:

```powershell
.\.venv\Scripts\python.exe scripts/kaggle_course.py --direct -- kernels status watasimycola/social-gaze-frozen-weights
```

It does not change the other agent's Kaggle configuration. Keep credentials out
of commands, logs and commits. GitHub synchronization resumed successfully on
November 7; the main results and follow-up implementation are pushed in `bff410c`,
with completed A2 evidence pushed in `f10c192` after final inspection.

## Registered interpretation experiments

Read [FOLLOWUP_EXPERIMENTS.md](FOLLOWUP_EXPERIMENTS.md) first. These exploratory
ablations retain the locked main winner and all main losses/ties. They reuse
the inference/features cache, original training folds and exact B=1,032 budget.
Use a new output directory for a reproduction:

```powershell
.\.venv\Scripts\python.exe -u scripts/run_followup_experiment.py windows `
  --output outputs/experiments/NEW-A1-WINDOWS
.\.venv\Scripts\python.exe -u scripts/run_followup_experiment.py summary-only `
  --output outputs/experiments/NEW-A2-SUMMARY-ONLY
```

Run in this order. A1 uses the two existing window models and validation-selected
alphas; it independently checks 2,000 draws and reproduces all primary M4 draws.
A2 refits after dropping exactly eight registered features, selects alpha with
100 validation draws and freezes the policy before 1,000 test draws. Each output
saves registration, policy lock, query manifest, exact query arrays, per-draw
results, independent numerical/RNG checks and main-result integrity hashes.

The completed A2 launch is recorded in
`outputs/experiments/followups-20261107/status.json`, with separate stdout/stderr
logs beside it. Check its process ID, logs and `A2-summary-only-v1/result.json`
before resuming; an existing output directory is never overwritten. If a failure
requires repair, retain the logs/artifacts and use a new versioned directory.

Both follow-ups are now complete. Their aggregate evidence is under
`docs/research/followup-A*-*.json`; the final plot/table is under
`reports/course-project/followup-*`. Recreate it from the saved aggregates with
`.venv-mtgs/Scripts/python.exe scripts/plot_followup_results.py`.
