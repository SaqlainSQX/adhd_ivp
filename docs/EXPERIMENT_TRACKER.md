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
| 6 | P05 | Full prediction shards and merge | Initial batch complete; remaining 17 sources running | Codex | Initial batch: 44,908 frames, 184,461 pair scores, 147 validated clip hashes. `outputs/inference/mtgs-remaining-shard-v1` resumed November 7. Final merge waits for exact frozen-population coverage |
| 7 | P06 | Static/temporal frame features | Implemented; real smoke passed | Codex | Static/windows 5 and 11 built for 236 pair predictions from 100 training frames. Full-cache build pending |
| 8 | E00 | Verify frame estimator, exact budgets and oracle | Core mathematics verified ahead of media | Codex | Exhaustive one/two-stratum point/variance tests, exact budgets, census, oracle boundary and exact hypergeometric coverage pass. End-to-end cache integration pending |
| 9 | E01 | Frozen-model development diagnostics | Pending | Unassigned | q bias, residual variance, calibration and lag structure |
| 10 | E02 | Uniform human/residual baseline checks | Preliminary M1 completed; E02 pending | Codex | 4,000 human-only draws on full pre-media test annotations; `research/m1-annotation-baseline.json`. M2 and final common-population validation pending |
| 11 | E03 | Fit and select static/temporal policies | Implemented; real execution pending | Codex | Five source folds, signed residuals, centered SD, nine validation candidates, immutable lock; synthetic integration check passes |
| 12 | E04 | Locked M0–M4 main benchmark | Implemented; real execution pending | Codex | Four exact budgets, saved queries, 1,000 draws by default; changing test labels leaves policies/query plans unchanged |
| 13 | E05 | Contextual-surrogate control and interpretation | Implemented; real execution pending | Codex | M5 shares M1/M2 queries; same frozen temporal residual model; paired draw bootstrap against M3/M2/M5 |
| 14 | E06 | Aggregate results, course report and demo | Runner/report/replay implemented; real outputs pending | Codex | Sequential `course-20261107-v1` run waits for inference, then runs all CPU stages. Replay test verifies identical query plans/estimates and rejects changed references; figures need final visual review |

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

## November 7 continuation

The initial GPU batch completed while the previous work was running. All its 147
clip hashes, 184,461 unique score IDs, probability bounds and native minimum-score
identities were checked again. One source in that original batch was later excluded
by the frozen media population; the final merger records and drops its cache.

The remaining 17 verified sources are running with the same checkpoint, precision,
geometry and temporal-input convention. `outputs/experiments/course-20261107-v1/`
contains a sequential driver waiting for that inference batch. It will execute
merge, features, E01/E02 diagnostics, E03 policy selection, 20,000 sampled method
evaluations, replay and report generation. A waiting run is not a completed result.

The GitHub connection recovered: the three prior local commits through `5486926`
were pushed to `main` on November 7. New continuation code and aggregate evidence
are committed separately. Raw references/media/checkpoints remain ignored.

## Policy lock to fill after development

| Field | Static M3 | Temporal M4 |
| --- | --- | --- |
| Feature version/hash | Not set | Not set |
| OOF/fold artifact | Not set | Not set |
| Final error model hash | Not set | Not set |
| Temporal window | Not applicable | Not selected |
| Mixture alpha | Not selected | Not selected |
| Stratum cuts / centered SD file | Not set | Not set |
| Validation selection evidence | Not set | Not set |

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
