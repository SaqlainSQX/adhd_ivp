# Course-project execution tracker

Master instructions: [COURSE_PROJECT_PLAN.md](COURSE_PROJECT_PLAN.md).
Defaults: [course-project.json](../configs/course-project.json).
Implementation contracts: [PIPELINE_IMPLEMENTATION.md](PIPELINE_IMPLEMENTATION.md).
Execution commands: [RUN_EXPERIMENTS.md](RUN_EXPERIMENTS.md).

This tracker records execution, not intentions. Update status, owner, evidence
paths and actual values after each gate. `Completed` requires inspected outputs.
No future stage is marked complete merely because this plan exists.

## Required sequence

| Order | ID | Stage | Status | Owner / checker | Evidence and next action |
| ---: | --- | --- | --- | --- | --- |
| 1 | P00 | Environment and isolated optional Kaggle account | Completed | Codex | Project-only Kaggle launcher verified as `watasimycola`; separate local CUDA environment; 31 tests pass |
| 2 | P01 | Annotation inventory | Completed in previous review | Existing review | `docs/research/annotation-inventory.json`; archive present in ignored local data folder |
| 3 | P02 | Normalize data and freeze source/fold manifests | Completed before media filtering | Codex | `research/data-preparation-report.json`; all file hashes/joins checked; 358,000 eligible anchors total; five source folds |
| 4 | P03 | Media availability, decode mapping and visual alignment | Completed for documented subset | Codex | All 95 sources attempted; verified-population-v2 retains 53 sources. Frame-count review pool excluded after scene-cut failure; another missing-count source excluded after visual review. `research/verified-population-manifest.json` |
| 5 | P04 | Pin MTGS and benchmark smoke inference | Completed for released DINO temporal variant | Codex | `research/mtgs-runtime-smoke.json`; strict load, native parity after auxiliary pruning, AMP development check and batches 1/2/4 pass on RTX 4060 |
| 6 | P05 | Full prediction shards and merge | Completed | Codex | Both shards complete; exact final cache has 314,058 public pair scores. One previously cached, subsequently excluded source is dropped explicitly. `course-20261107-v1/cache/manifest.json` |
| 7 | P06 | Static/temporal frame features | Completed | Codex | Label-free static/windows 5 and 11 built from the full cache; 227,411 eligible anchors. Frozen feature hashes in policy lock |
| 8 | E00 | Verify frame estimator, exact budgets and oracle | Completed | Codex | Statistical tests and real-cache integration pass; independent replay/recomputation of all 20,000 main audits also passes |
| 9 | E01 | Frozen-model development diagnostics | Completed | Codex | `course-20261107-v1/development-checks/result.json`; development score, calibration and lag diagnostics retained |
| 10 | E02 | Uniform human/residual baseline checks | Completed | Codex | 800 validation baseline method-runs before policy fitting; all main budgets also evaluated on the same frozen test population |
| 11 | E03 | Fit and select static/temporal policies | Completed | Codex | Five source folds, nine validation candidates, static alpha 1; temporal window 11 / alpha 1. Immutable lock preserved |
| 12 | E04 | Locked M0–M4 main benchmark | Completed | Codex | Four exact budgets, 1,000 draws each; all losses/ties retained. Main result SHA b7dba063…aead9 |
| 13 | E05 | Contextual-surrogate control and interpretation | Completed, including A1 and A2 | Codex | M5 complete. Window-5 RMSE 0.2504 versus window-11 0.2765 pp; summary-only 0.2754 pp at B=1,032. No clear transition-feature gain; main comparison unchanged |
| 14 | E06 | Aggregate results, course report and demo | Completed for required course evidence package | Codex | All 20,000 main + 3,000 follow-up audit evaluations checked (1,000 reproduce main M4); seven figures visually reviewed. [Assessment](research/course-results.md), shareable report, replay and tracked aggregate evidence saved |

## Optional queue

| ID | Experiment | Status | Start only when |
| --- | --- | --- | --- |
| X01 | Block lengths 2,5,10 versus frame queries | Deferred | Required sequence is complete |
| X02 | Alternate learner, error target, entropy/tuned-weight controls | Deferred | Required sequence is complete |
| X03 | Development-label cost curves | Deferred | Required sequence is complete |
| X04 | Timed annotation-interface pilot | Deferred | Required sequence is complete and annotators/media available |

## Runtime decisions to fill before GPU work

| Decision | Actual value | Evidence |
| --- | --- | --- |
| Data version / retained population hash | verified-population-v2; `f656637160d3139e232d7526d7b1942f6b4a66fcc872f6220fc0b470b8a775d7` | Population-manifest SHA-256; `configs/execution-verified-v1.json` |
| Full release or documented subset | 53 retained of 95 attempted sources; 40 train, 3 validation, 10 test | P03 availability/exclusion ledger; source-count review pool stays excluded |
| Retained train/validation/test M | 191,956 / 25,139 / 10,316 | Exact test label budgets 516 / 1,032 / 2,063 / 4,126 |
| Upstream MTGS commit and checkpoint SHA-256 | Source `a2ce45f44ed73d86e89e16bffb6be7a9567e3052`; tensor state `5599382ab78f3993d31300f4e16ed13bc20bed26d7ec9735a37473eb374d994f` | `research/mtgs-checkpoint-provenance.json` also records original training artifact hash |
| Exact resolution and model temporal length | Scene 448; heads 224; patch 14; five times at stride 3 | Strict checkpoint load/runtime smoke |
| Model runtime Python/PyTorch/CUDA versions | Python 3.13.1; PyTorch 2.11.0+cu128; CUDA 12.8 | Separate `.venv-mtgs`; global CPU environment unchanged |
| GPU runner and account identity | Local RTX 4060 Laptop 8 GiB; Kaggle `watasimycola` for private CPU jobs | No Kaggle GPU job used so far |
| Measured throughput / peak GPU memory | 8.03 frames/s; peak 1,472,728,576 allocated bytes | 100-frame cached AMP development smoke; full-shard throughput measured separately |
| Inference shard target runtime / timeout | Not set | P04 workload projection |
| Course deadline / final artifact requirements | Not supplied | Add when known; no need to block earlier stages |

## November 7 execution and results

The initial GPU batch completed while the previous work was running. All its 147
clip hashes, 184,461 unique score IDs, probability bounds and native minimum-score
identities were checked again. One source in that original batch was later excluded
by the frozen media population; the final merger records and drops its cache.

The remaining 17 sources completed in 6,243.9 seconds. The sequential main run
`outputs/experiments/course-20261107-v1/` completed merge, features, diagnostics,
policy selection, all 20,000 sampled method evaluations, independent validation,
replay and report generation. Its pipeline state is `complete`; visual review
passed for all five report figures and the public query timeline. Maximum
independent point/variance discrepancies were 1.11e-16 / 6.03e-17.

At B=1,032, RMSE was 0.5529 pp for uniform residual correction, 0.2603 pp for
static guidance and 0.2765 pp for temporal guidance. The locked temporal/static
ratio is 1.0623 with paired-draw Monte Carlo interval [0.9889, 1.1421]: no temporal
gain is established. Normal interval coverage was only 93.0% / 93.3% for the
guided methods. [Full assessment and caveats](research/course-results.md).

Registered follow-ups execute in `outputs/experiments/followups-20261107/`.
A1 is complete: both alphas are 1; window 5 / 11 RMSE is 0.2504 / 0.2765 pp;
all 2,000 follow-up draws independently checked, with exact main-M4 reproduction.
A2 ran from 10:44:30 UTC for 547.9 seconds, CPU only, output
`A2-summary-only-v1`. Alpha 1 was selected on validation only. Its 1,000 draws
passed independent RNG/point/variance checks; the exact eight-column removal,
model settings, query hashes and unchanged main-result hashes were also checked.
Summary-only/full-temporal RMSE ratio is 0.9960 [0.9454, 1.0478]; no clear gain
from the removed transition/boundary features is established. Its command,
completion state and stdout/stderr logs remain in the follow-up root.
The registered protocol and seeds are in [FOLLOWUP_EXPERIMENTS.md](FOLLOWUP_EXPERIMENTS.md).

GitHub synchronization recovered; the main results, report and follow-up
implementation are pushed in `bff410c`. The completed A2 evidence and final
assessment are synchronized separately after visual QA. Raw references/media/
checkpoints remain ignored. Required course experiments are complete; X01–X04
remain deferred rather than being added to seek a positive temporal result.

## Frozen main policy lock

| Field | Static M3 | Temporal M4 |
| --- | --- | --- |
| Feature version/hash | static / a149f032…aad68 | temporal-w11 / 1594d838…80981 |
| OOF/fold artifact | development/static-oof-scores.npy; original five training-source folds | development/temporal-w11-oof-scores.npy; same folds |
| Final error model hash | 4052ebc1…e0f7d | 8fde8b32…ad3a6 |
| Temporal window | Not applicable | 11 |
| Mixture alpha | 1 | 1 |
| Stratum cuts / centered SD file | development/static-development.json | development/temporal-w11-development.json |
| Validation selection evidence | Nine candidates, 100 draws each; policy-lock.json | Same; minimum validation MSE with registered 1% tie rule |

Full authoritative hashes and validation candidates are in
[main-policy-lock.json](research/main-policy-lock.json). Cuts and SDs are in
[main-development-policies.json](research/main-development-policies.json).
Local paths above are relative to `outputs/experiments/course-20261107-v1/`.

Software checks after follow-up implementation: **34 tests pass**, Ruff passes.

## Per-stage record template

Copy this for each completed or failed stage:

```text
Stage ID:
Status: planned / implementing / running / failed / completed / deferred
Owner:
Checker:
Started / finished:
Git commit:
Exact command or Kaggle kernel/version:
Config/data/cache hashes:
Inputs:
Outputs and log paths:
Actual counts / runtime / cost:
Gate checks and evidence:
Failure or deviation:
Decision and next stage:
GitHub sync state:
```

## Experiment result record template

```text
Experiment ID / run ID:
Evaluation designation: exploratory
Actual eligible population M and hash:
Methods and frozen policy hashes:
Budgets (fraction and integer labels):
Seed range and draw count:
Primary comparison:
Bias / MAE / RMSE (percentage points):
Coverage and width for each interval:
Failure / zero-variance / zero-positive rates:
Development labels reused or newly purchased:
GPU inference and CPU audit cost:
Interpretation, including ties/losses:
Reproduction / replay command:
```
