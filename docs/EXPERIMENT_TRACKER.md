# Course-project execution tracker

Master instructions: [COURSE_PROJECT_PLAN.md](COURSE_PROJECT_PLAN.md).
Defaults: [course-project.json](../configs/course-project.json).
Missing interfaces: [PIPELINE_IMPLEMENTATION.md](PIPELINE_IMPLEMENTATION.md).

This tracker records execution, not intentions. Update status, owner, evidence
paths and actual values after each gate. `Completed` requires inspected outputs.
No future stage is marked complete merely because this plan exists.

## Required sequence

| Order | ID | Stage | Status | Owner / checker | Evidence and next action |
| ---: | --- | --- | --- | --- | --- |
| 1 | P00 | Environment and isolated optional Kaggle account | Completed | Codex | Project-only Kaggle launcher verified as `watasimycola`; separate local CUDA environment; 31 tests pass |
| 2 | P01 | Annotation inventory | Completed in previous review | Existing review | `docs/research/annotation-inventory.json`; archive present in ignored local data folder |
| 3 | P02 | Normalize data and freeze source/fold manifests | Completed before media filtering | Codex | `research/data-preparation-report.json`; all file hashes/joins checked; 358,000 eligible anchors total; five source folds |
| 4 | P03 | Media availability, decode mapping and visual alignment | In progress | Codex | All mappings prepared; three-case extraction pilot and 36-frame cross-split visual review passed. Original acquisition and one-frame-count review pool running; final population pending |
| 5 | P04 | Pin MTGS and benchmark smoke inference | Completed for released DINO temporal variant | Codex | `research/mtgs-runtime-smoke.json`; strict load, native parity after auxiliary pruning, AMP development check and batches 1/2/4 pass on RTX 4060 |
| 6 | P05 | Full prediction shards and merge | First 37-source shard running | Codex | `outputs/inference/mtgs-strict-shard-v1`; final source set/cache merge pending |
| 7 | P06 | Static/temporal frame features | Implemented; real smoke passed | Codex | Static/windows 5 and 11 built for 236 pair predictions from 100 training frames. Full-cache build pending |
| 8 | E00 | Verify frame estimator, exact budgets and oracle | Core mathematics verified ahead of media | Codex | Exhaustive one/two-stratum point/variance tests, exact budgets, census, oracle boundary and exact hypergeometric coverage pass. End-to-end cache integration pending |
| 9 | E01 | Frozen-model development diagnostics | Pending | Unassigned | q bias, residual variance, calibration and lag structure |
| 10 | E02 | Uniform human/residual baseline checks | Preliminary M1 completed; E02 pending | Codex | 4,000 human-only draws on full pre-media test annotations; `research/m1-annotation-baseline.json`. M2 and final common-population validation pending |
| 11 | E03 | Fit and select static/temporal policies | Implemented; real execution pending | Codex | Five source folds, signed residuals, centered SD, nine validation candidates, immutable lock; synthetic integration check passes |
| 12 | E04 | Locked M0–M4 main benchmark | Implemented; real execution pending | Codex | Four exact budgets, saved queries, 1,000 draws by default; changing test labels leaves policies/query plans unchanged |
| 13 | E05 | Contextual-surrogate control and interpretation | Implemented; real execution pending | Codex | M5 shares M1/M2 queries; same frozen temporal residual model; paired draw bootstrap against M3/M2/M5 |
| 14 | E06 | Aggregate results, course report and demo | Pending | Unassigned | Reproducible tables/plots and one-draw replay |

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
| Data version / retained population hash | Not set | P03 |
| Full release or documented subset | Not set | P03 availability/exclusion ledger |
| Retained train/validation/test M | Not set | P03 population manifest |
| Upstream MTGS commit and checkpoint SHA-256 | Source `a2ce45f44ed73d86e89e16bffb6be7a9567e3052`; tensor state `5599382ab78f3993d31300f4e16ed13bc20bed26d7ec9735a37473eb374d994f` | `research/mtgs-checkpoint-provenance.json` also records original training artifact hash |
| Exact resolution and model temporal length | Scene 448; heads 224; patch 14; five times at stride 3 | Strict checkpoint load/runtime smoke |
| Model runtime Python/PyTorch/CUDA versions | Python 3.13.1; PyTorch 2.11.0+cu128; CUDA 12.8 | Separate `.venv-mtgs`; global CPU environment unchanged |
| GPU runner and account identity | Local RTX 4060 Laptop 8 GiB; Kaggle `watasimycola` for private CPU jobs | No Kaggle GPU job used so far |
| Measured throughput / peak GPU memory | 8.03 frames/s; peak 1,472,728,576 allocated bytes | 100-frame cached AMP development smoke; full-shard throughput measured separately |
| Inference shard target runtime / timeout | Not set | P04 workload projection |
| Course deadline / final artifact requirements | Not supplied | Add when known; no need to block earlier stages |

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
