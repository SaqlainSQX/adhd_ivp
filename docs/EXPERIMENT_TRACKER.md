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
| 1 | P00 | Environment and isolated optional Kaggle account | Partly verified previously | Unassigned | CPU environment/tests/demo exist. Recheck before work; project Kaggle launcher and identity check pending |
| 2 | P01 | Annotation inventory | Completed in previous review | Existing review | `docs/research/annotation-inventory.json`; archive present in ignored local data folder |
| 3 | P02 | Normalize data and freeze source/fold manifests | Not implemented | Unassigned | Build export adapter and full exclusion ledger |
| 4 | P03 | Media availability, decode mapping and visual alignment | Pending | Unassigned | Locate team media; retain only verified common population |
| 5 | P04 | Pin MTGS and benchmark smoke inference | Pending | Unassigned | Record actual runtime/checkpoint and GPU availability |
| 6 | P05 | Full prediction shards and merge | Pending | Unassigned | Run source shards once; retain hash-validated caches |
| 7 | P06 | Static/temporal frame features | Not implemented | Unassigned | Label-free feature builder and gap/boundary checks |
| 8 | E00 | Verify frame estimator, exact budgets and oracle | Not implemented | Unassigned | Existing block tests remain; new frame checks required |
| 9 | E01 | Frozen-model development diagnostics | Pending | Unassigned | q bias, residual variance, calibration and lag structure |
| 10 | E02 | Uniform human/residual baseline checks | Pending | Unassigned | 100 validation draws at four budgets |
| 11 | E03 | Fit and select static/temporal policies | Pending | Unassigned | Five training-source folds; nine validation candidates |
| 12 | E04 | Locked M0–M4 main benchmark | Pending | Unassigned | Four budgets, 1,000 draws; 16,000 sampled method-runs |
| 13 | E05 | Contextual-surrogate control and interpretation | Pending | Unassigned | M5 at equal budget; small ablations if time permits |
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
| Upstream MTGS commit and checkpoint SHA-256 | Not set | P04 provenance |
| Exact resolution and model temporal length | Not set | P04 pinned configuration |
| Model runtime Python/PyTorch/CUDA versions | Not set | P04 environment record |
| GPU runner and account identity | Not set | P00/P04; no credentials in this table |
| Measured throughput / peak GPU memory | Not set | P04 benchmark |
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
