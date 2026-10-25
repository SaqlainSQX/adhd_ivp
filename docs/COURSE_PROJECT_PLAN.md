# Course project: sequential execution plan

Version 1.0, 25 October 2026. Workspace: `G:\ivp`.
Repository: https://github.com/SaqlainSQX/adhd_ivp

This is the practical course-project plan agreed after the methodology review.
It takes priority over the broader conference-oriented experiment wish list in
[methodology.md](methodology.md) when deciding the required project scope.
The statistical definitions and data limitations in that document still apply.

**Start at P00 and follow the order below. Do not jump to a full GPU run.**

## 1. What we have decided to build

We will estimate the proportion of benchmark-defined mutual-looking pair-frames
using frozen MTGS predictions and a limited random sample of reference labels.
We will investigate whether temporal information improves which labels we query.
The contribution for the course is a working, tested, reproducible system and an
honest comparison of its methods. A new statistical theorem or a win over every
published system is not required.

The primary query unit is **one unordered person pair in one frame**. We will keep
MTGS frozen, process data once, cache its outputs, and run the sampling experiments
on those small caches. Blocks are an optional extension after the frame experiment.
We will not train a new gaze backbone in the required project.

Primary question: does temporal-guided sampling estimate prevalence more accurately
than uniform correction and static-guided sampling for the same number of labels?

Primary comparison: temporal-guided versus static-guided frame queries at a 10%
label budget. Other budgets and the uniform baselines remain necessary context.
Test results are exploratory: project development has already inspected test
annotation summaries and label-only diagnostics. Course conclusions can still be
validly reported with that history disclosed.

### Required methods

| ID | Method | Prediction used for correction | Queries |
| --- | --- | --- | --- |
| M0 | Model-only | Frozen native MTGS score q | None |
| M1 | Human-only uniform | None | Uniform random eligible frames |
| M2 | Uniform residual correction | Frozen q | Uniform random eligible frames |
| M3 | Static error-guided correction | Frozen q | Stratified random sample guided by per-frame features |
| M4 | Temporal error-guided correction | Frozen q | Same design as M3 with temporal features added |

M3 is the extra control that lets us attribute an M4 improvement to temporal input.
M1–M4 have exactly the same test-label budget. M0 spends zero test labels and is
reported separately rather than pretending it used each audit budget.

A small interpretation control, M5, will follow the main run: use a temporal
residual predictor to form a calibrated surrogate, then query uniformly. It tells
us whether any improvement comes from a better surrogate rather than selection.
Entropy sampling, power-tuned correction, extra predictors and paper replications
are extensions rather than requirements for completing this course project.

### Completion definition

The required project is complete when P00–P06 and E00–E06 produce their listed
artifacts, pass their gates and can be rerun from saved inputs. Negative findings
are acceptable. Missing alignment, leaked labels, changed denominators or unfair
budgets are implementation problems to fix, not negative scientific findings.

## 2. Status today and executable versus planned work

| Item | Current state |
| --- | --- |
| Literature/methodology review | Written; course scope now narrowed by this plan |
| Public VSGaze annotation archive | Present locally at `data/research/VSGaze.tar.gz`, checksum verified |
| Aggregate annotation/source counts | Reproduced; see [inventory](research/annotation-inventory.json) |
| Synthetic block pipeline and small statistical tests | Implemented and previously checked |
| Raw videos/decoded frame alignment | Not established |
| Kaggle account for this project | Not configured; separate credentials still needed if using Kaggle |
| Pinned MTGS installation/checkpoint/inference cache | Not established |
| Frame-specific feature/scoring/audit pipeline in this plan | Must be implemented |

The current CLI implements `gaze-audit demo` and `gaze-audit run`. Its real-cache
`run` remains a provisional **block pipeline**. Setting `--block-length 1` does not
create the missing frame-context features or all the methods planned here.

Only command blocks labelled **available now** can be used as existing entry points.
Future stage interfaces are specified in [PIPELINE_IMPLEMENTATION.md](PIPELINE_IMPLEMENTATION.md).
Those interfaces are implementation requirements, not claims that scripts exist.
The JSON in [course-project.json](../configs/course-project.json) is a design
configuration to guide implementation; the current CLI does not consume it.

## 3. Order and dependencies

| Order | Stage | Where | Gate before moving on |
| ---: | --- | --- | --- |
| 1 | P00 Environment and account isolation | Local CPU | Existing tests/demo work; optional Kaggle identity isolated |
| 2 | P01 Verify annotation release | Local CPU | Counts and archive hashes match |
| 3 | P02 Normalize annotations and freeze manifests | Local CPU | Canonical IDs, labels, splits and exclusion ledger validated |
| 4 | P03 Obtain media and verify alignment | Local CPU | Exact available frame universe and visual alignment pass |
| 5 | P04 MTGS smoke test and resource benchmark | GPU, Kaggle or local | Native output understood; pinned model works on several clips |
| 6 | P05 Cache full predictions | GPU | Every retained pair-frame joins exactly once; cache validates |
| 7 | P06 Build static/temporal features | Local CPU | Features depend only on allowed inputs and respect time gaps |
| 8 | E00 Verify frame estimators and budgets | Local CPU | Enumeration, census, oracle and exact-budget checks pass |
| 9 | E01 Characterize frozen predictor | Local CPU | Baseline score/cost/coverage diagnostics saved |
| 10 | E02 Establish uniform sampling baselines | Local CPU | M1/M2 behave correctly over 100 development draws |
| 11 | E03 Fit and select error-guided policies | Local CPU | Source-grouped training and validation-only selection complete |
| 12 | E04 Lock and run main benchmark | Local CPU | M0–M4, four budgets, 1,000 audit draws; no evaluation tuning |
| 13 | E05 Interpret gains with M5 and small ablations | Local CPU | Acquisition versus calibration explained; costs disclosed |
| 14 | E06 Export results, demo and course report | Local CPU | Tables/plots/reproduction and limitations complete |
| Later | X01–X04 optional extensions | As appropriate | Required project complete first |

Use [EXPERIMENT_TRACKER.md](EXPERIMENT_TRACKER.md) as the live checklist. A stage
changes to complete only when its output and acceptance evidence are recorded.

## 4. Folder and artifact layout

Paths below are relative to the repository for portability. On this PC their root
is `G:\ivp`; on Kaggle code receives explicit input/output roots.

```text
configs/course-project.json                 Tracked experimental design
docs/COURSE_PROJECT_PLAN.md                  This master plan
docs/EXPERIMENT_TRACKER.md                   Progress, gates and result locations
docs/PIPELINE_IMPLEMENTATION.md              Missing commands/modules to implement
data/research/VSGaze.tar.gz                  Existing archive, ignored
data/credentials/kaggle-course/              Separate credentials, ignored
data/raw/childplay/                          Original media, ignored
data/manifests/<data_version>/               Source/clip/frame/pair manifests, ignored
data/processed/<data_version>/public/        Permitted geometry and eligible IDs
data/processed/<data_version>/oracle/        Reference values, kept out of inference/features
checkpoints/mtgs/<checkpoint_sha256>/        Frozen weights, ignored
external/MTGS/                              Separate upstream checkout, ignored
outputs/inference/<cache_version>/          Prediction shards and inference metadata
outputs/features/<feature_version>/         Feature tables and validation summaries
outputs/experiments/<run_id>/                Audits, policies, logs, metrics and plots
reports/course-project/                     Approved aggregate results/report sources, tracked
```

Create a data version only after P03 freezes the actual media-available population.
Example naming: `childplay-vsgaze-2025-v1-local-v1`. A new exclusion, changed frame
mapping, checkpoint or feature definition creates a new version; it never silently
replaces an old completed result. Generated data and raw labels stay out of Git.

Each run must save config snapshot, input hashes, Git commit, package versions,
seed list, retained population size, costs, status and failure reason. Suggested
run ID: `e04_<utc-timestamp>_<short-git-sha>`. Record both UTC timestamps and local
date/time when useful. Raw results are never overwritten to hide a failed run.

## 5. P00: environment, account isolation and smoke checks

**Inputs:** current checkout, Python 3.11+, uv; Kaggle credentials only if GPU work
will run there. **Resources:** CPU; no need to spend GPU quota here.

**Available now, from `G:\ivp`:**

```powershell
uv sync --frozen --extra dev --extra research
uv run --extra dev --extra research ruff check .
uv run --extra dev --extra research pytest --basetemp outputs/pytest-course-start
uv run gaze-audit demo --draws 3 --output outputs/course-start-demo
```

Choose a new demo/temp directory if preserving an earlier run. The demo is a
software check with invented data; never use it as a ChildPlay result.

For Kaggle, create a project-specific launcher before authenticating. Credentials
belong under the ignored `data/credentials/kaggle-course/` or another private local
location. The launcher sets `KAGGLE_CONFIG_DIR` for its child process, removes
inherited credential selectors in that child and verifies the intended identity
without printing tokens. Do not overwrite another agent's shared Kaggle config.
Credential files must not be bundled with notebook code or uploaded datasets.

Local Kaggle CLI 2.2.4 and its kernels command help were inspected while planning.
This does not imply this project's account is connected or GPU quota is available.
Account verification and accelerator availability are runtime checks, not plan constants.

**Outputs:** `environment.json`, package lock references, successful test/demo log;
optional sanitized `kaggle_identity_check.json`. **Gate:** local smoke tests pass,
and any Kaggle job launcher is isolated before it submits anything.

## 6. P01: verify the release and reproduce the inventory

**Available now:**

```powershell
uv run --extra research python scripts/research/inspect_vsgaze.py --archive data/research/VSGaze.tar.gz
uv run --extra research python scripts/research/feasibility_checks.py
```

Expected archive SHA-256:
`3bf42763c968b9684a3276e32b41403a43392282c67bdc8e461058ca949cb386`.
Expected published MD5: `c83980c07b349df3af84981721045d3b`.

| Split | Frames | Sources | Eligible binary pair-frames | Positive | Unknown real pair-frames |
| --- | ---: | ---: | ---: | ---: | ---: |
| Train | 100,209 | 68 | 285,585 | 6,396 | 129,441 |
| Validation | 10,283 | 6 | 33,568 | 259 | 11,741 |
| Test | 9,986 | 21 | 38,847 | 651 | 41,572 |

These are VSGaze-release counts, not a promise that every original video is still
obtainable. The original ChildPlay frame total differs; retain the release identity.

**Outputs:** existing inventory and feasibility JSON under `outputs/research/`.
**Gate:** checksums/counts match or a documented release discrepancy is resolved.
This stage has already been completed in this workspace; rerun only to reproduce
the check or when input release changes.

## 7. P02: normalized manifests and explicit data boundaries

Implement an archive adapter using the pinned release reader. It must write:

| Table | Required information |
| --- | --- |
| `sources.csv` | source_id, original split, media locator, available identity/channel metadata |
| `clips.csv` | clip_id, source_id, source bounds, naming/downsampling flags, annotation frame count |
| `frames.csv` | frame_id, clip_id, original frame index, expected media location, later alignment fields |
| `public_people.csv` | frame_id, real person/track ID, normalized head box, geometry validity |
| `public_pairs.csv` | record_id, frame_id, canonical person_a/person_b, eligibility mask, split |
| `oracle_labels.csv` | record_id, binary reference label for eligible rows only |
| `exclusions.csv` | stage, candidate ID, exclusion reason and relevant source/frame |
| `development_folds.csv` | training source_id and one of five fixed fold IDs |

Stable IDs must depend on source/clip/frame/person identity, never on label values
or row ordering. Keep both directions of model outputs correctly associated with
the canonical person order. Reconcile reverse annotations before export; conflict
is an error, not a majority vote. Unknown values remain unknown and never become zero.

Primary population: all real unordered person-pair/frame records with binary LAEO
reference, valid required geometry and media verified in P03. Do not select only
positive-looking scenes or relabel known human behavior to improve performance.
The unknown-availability mask may define this benchmark population but is not a
risk-learning feature. Exclude gaze points, gaze classes, reference LAH, LAEO and
shared-attention annotations from public inference/feature tables.

Use original train/validation/test source partitions. For the practical course
regime, train error models on original training labels as historical data, select
policies on validation and evaluate on test. Disclose whether MTGS saw the original
training sources. Its possible exposure is not removed by grouping error-model folds.
This regime is feasible for the course and avoids pretending six validation videos
support a large standalone error-model training/tuning study.

Use deterministic `GroupKFold(n_splits=5)` on training sources for out-of-fold error
predictions and moment estimates. Save the fold assignment. All clips from a source
stay together. Preserve original source IDs including underscores; avoid splitting
YouTube IDs at their first underscore. Subject/channel overlap, when knowable, is
a reported limitation beyond source-video separation.

**Checks:** unique canonical record IDs, matching label/public eligibility IDs,
valid finite head geometry, binary-only oracle, zero source overlap between splits,
and zero sources crossing development folds. Reconcile exclusions against P01.
**Gate:** normalized tables and a schema/row-count report pass before media or models.

## 8. P03: obtain media, decode once and establish exact alignment

1. Read original ChildPlay release instructions and locate the source media.
   Inventory local team copies first. Prefer existing authorized copies instead
   of repeatedly downloading the same videos.
2. Record an availability outcome for every source and clip. Do not silently
   replace inaccessible originals with similar videos.
3. Create a per-clip decoding map: original source index, decoded frame, timestamp,
   resolution, FPS/timebase, extraction stride and any offset. Handle
   `-downsampled` clips explicitly. Infer no offset from a visually plausible frame
   alone; verify multiple positions against annotation geometry.
4. Decode only the media needed for annotated clips and the verified temporal
   context of the chosen checkpoint. Avoid storing an entire movie when only a
   short clip is needed. Reuse decoded frames across person pairs.
5. Overlay provided boxes/IDs on at least the first/middle/last annotated frame of
   every retained clip. Review all six validation sources, and sample across train
   and test sources/resolutions/downsampled clips. Save a contact sheet and a
   review ledger. This visual work uses geometry only, not hidden gaze labels.
6. Reject a misaligned clip until corrected. Any correction must be recorded, then
   the affected frames checked again. Unexplained boundary/timebase mismatches block inference.
7. Freeze a retained-record manifest and exclusion ledger before model evaluation.

The full original inventory is the reference target when all required media pass.
If some media are irrecoverable, create a **media-available subset version** and
recompute M, split counts and all budgets for that version. Use exactly this same
population for every method. Publish source/record exclusions and keep the original
inventory alongside it. A clearly disclosed smaller benchmark is acceptable for
the course; changing the target between methods is not.

**Resource check:** measure decoded size for representative clips, project total
disk need, and check free space before bulk extraction. Save the estimate rather
than assuming a fixed disk requirement.

**Outputs:** `alignment.json`, `media_availability.csv`, `frame_mapping.csv`, review
contact sheets, `population_manifest.json`, final exclusion ledger and hashes.
**Gate:** no unresolved retained-frame mapping errors; all retained records have
usable media and required geometry. Missing-media cases are explicit.

## 9. P04: pin MTGS, run a small GPU smoke test and estimate cost

**Model decision:** one released temporal MTGS configuration. Prefer the original
temporal `mtgs-vsgaze` variant for an initial match to the supplied presentation,
subject to verifying the actual released configuration. Record the precise release,
repository commit, weight SHA-256, architecture, resolution, model temporal length,
preprocessing, person-mask convention and native score interpretation. Do not write
guessed model input dimensions or window length into an executable config.

Keep its runtime separate from the current CPU statistics environment. Resolve and
record upstream PyTorch/CUDA/Python requirements from the pinned code; the existing
Python 3.13 CPU environment is not proof that the model runtime is compatible.
Install/verify the model on the chosen GPU runner before a full data upload.

Start with three to five training clips chosen deterministically by IDs/geometry
coverage, including a downsampled example if retained. Choose them without looking
at reference label values. Include multiple people and a short or difficult track.

Smoke-test order: import model, load weights with expected keys, one frame/window,
one full clip, then the remaining smoke clips. Use evaluation/inference mode and
disable gradient storage. Batch-size trial sequence: 1,2,4; stop increasing before
memory exhaustion. Use FP32 first; an FP16 change needs an explicit small numerical
comparison and a new inference configuration hash.

Verify native LAEO as `min(directional_A_to_B, directional_B_to_A)` using learned
social outputs for this pinned variant. Keep logits versus sigmoid scores explicit.
Gaze-point/head-box post-processing is a separate output variant and not a silent
replacement. No hidden annotation values may be passed into model forward inputs.

Measure load time, processed frames/windows per second, peak GPU memory, output
size and failures. Project full runtime from the retained workload and observed
throughput, including overlap in model windows, startup and I/O. Use the projection
to choose shard size and job timeout; no GPU-hours estimate is assumed in advance.

**Outputs:** `model-provenance.json`, pinned runtime record, smoke prediction shard,
geometry/score visual checks, `throughput.json`, projected job/disk plan.
**Gate:** all smoke outputs valid, correct pair/direction mapping, no hidden inputs,
and a full-run resource plan based on measurements. On failure fix this small run.

## 10. P05: full frozen prediction cache

Inference order is training shards, validation shards, then test shards. Run one
shard successfully before queuing the next. Shard by original source video so clips
from a source are processed together; exceptionally long sources can be split into
documented clip chunks without changing source identity. Select shard duration
from P04 rather than a fixed unmeasured number of clips.

Every shard is immutable and includes input hashes, expected record IDs, runtime,
checkpoint/config hash, completion status and score count. Write to a temporary
output, validate it, then mark completed. Resume only unfinished/invalid shards;
do not rerun valid GPU work for each sampling experiment.

Cache public outputs for real pairs needed by eligible anchors and legitimate
temporal context, including pairs whose references are unknown if their public
inputs exist. Reference values are excluded from inference bundles.

Required cache columns: record_id, source_id, clip_id, original frame index,
timestamp/sequence index, canonical pair IDs, directional scores, q, valid-track and
model-context metadata. Keep permitted geometry in a separate public sidecar keyed
by record_id. The existing strict `predictions.csv` schema cannot accept all these
extra fields; implement a versioned enriched cache plus a narrow legacy export.

Merge shards only when all hashes agree. Check duplicates, probability range,
finite values, directional consistency and exact retained-anchor coverage. Track
missing predictions explicitly. A rerun-induced population change requires a new
data/cache version shared by all methods.

**Outputs:** per-source prediction shards, `cache_manifest.json`, merge validation
report and one compact merged cache per split. **Gate:** complete coverage of the
frozen retained population, no conflicts, stable repeated predictions within an
explicit recorded numerical tolerance. CPU experiments use these caches thereafter.

### Kaggle execution pattern, if used

Implement one private smoke script/notebook and one resumable shard-inference
script. Bundle only inference code, public geometry/frame manifests, weights/media
as permitted inputs, and configuration. Keep oracle tables off the inference runner.
Do not upload the entire local repository folder with credentials or labels.

The isolated launcher will use these locally verified CLI forms:

```text
kaggle kernels push -p <prepared-job-folder>
kaggle kernels status <owner>/<kernel-slug>
kaggle kernels output <owner>/<kernel-slug> -p <fresh-download-folder>
```

These are command forms, not commands to run with literal placeholders. The
project launcher/metadata/input datasets are still to implement. Fill actual owner,
private kernel ID, input versions, GPU availability and timeout after account setup.
Use the [official metadata schema](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels_metadata.md).
Record the returned kernel version; downloading output alone does not prove the
expected version ran. Check completion and local output hashes before merging.
If Kaggle is unavailable, use the same inference bundle on a local/team GPU.

## 11. P06: public static and temporal feature tables

Features are deterministic functions of frozen predictions and allowed geometry.
The feature builder has no reference-label argument. Eligible anchor IDs come from
the frozen manifest; do not use the eligibility mask as a learned feature.

**Static features, same for M3 and M4:** q; the two directional scores; signed and
absolute directional imbalance; q entropy using clipped values only inside the
log calculation; each head's normalized center, width, height and area; pair center
distance; area ratio with epsilon 1e-6; real-person occupancy in that frame.
Sort person IDs once and preserve all direction/box associations.

**Temporal additions for M4:** neighborhood q mean/std/min/max; mean absolute
adjacent q difference; previous/next q difference; mean/std of directional
imbalance; per-person head-area and pair-distance changes; context count and
public tracking-gap indicators. Start with symmetric windows of 5 and 11 positions;
window size includes the anchor. No future-frame restriction is needed for this
offline project. A live/online demonstration would be a different experiment.

Define continuity using the P03 timestamp/frame mapping and verified extraction
stride. Stay inside one clip and unordered pair. Break at an unexplained frame gap
or missing track; never treat skipped original frames as adjacent simply because
their rows are adjacent. At boundaries use available context and record its size.
Do not fill context with labels, cross split boundaries or interpolate hidden gaze.
Unknown-labeled neighbors may supply predictions if their public tracks/media exist;
they cannot supply labels. Query blocks in X01 break at unknown eligibility gaps.

Missing values have declared defaults and indicator columns. Fit any scaling or
imputation statistics on training data only and reuse them on validation/test.
Do not use raw source/person IDs as predictive numeric features; they are join,
grouping and debugging identifiers.

**Checks:** recomputing after arbitrary oracle-label changes gives identical
features; shuffling input row order gives identical keyed features; hand-check
boundary/gap cases; no cross-pair context; window 1 reproduces anchor-only behavior.
**Outputs:** feature tables, feature schema/version/hash, feature-validation report.
**Gate:** these checks pass before fitting error models.

## 12. E00: frame estimator, oracle and exact-budget verification

Keep the existing tests, then add the planned frame-specific checks before using
the richer cache. This stage is software verification, not an effectiveness result.

For fixed q and SRS-without-replacement inside strata, use:

```text
e_i = y_i - q_i
p_hat = [sum_all q_i + sum_h (N_h/n_h) sum_sample_h e_i] / M
V_hat = [sum_h N_h^2 * (1 - n_h/N_h) * s_e,h^2 / n_h] / M^2
```

For M1 set q to zero and use a single stratum. M2 also uses one stratum. For M3/M4
the partition and sample counts are fixed before querying labels. Minimum stratum
sample is `min(N_h,20)` where the budget supports it. Two observations only suffice
to compute sample variance, not to establish a reliable normal interval. Collapse
development-defined strata or mark an infeasible budget; never assign zero inclusion.

Allocate an exact integer B for frame methods. Solve bounded continuous counts
with required minima and saturation, floor counts, then distribute remaining
positions by descending fractional remainder with a deterministic tie break.
Assert sum(n_h)=B and n_h<=N_h. The current independent randomized rounding is
acceptable for expected-cost blocks but must not be used for an exact frame cap.

Test exhaustive small populations with one/multiple strata, variable q and rare
labels: mean estimated prevalence equals truth over all possible samples, and mean
estimated variance equals true design variance. Census must recover exact truth
with zero sampling variance. Check no replacement, exact budget, reproducible seeds,
all-positive/all-negative inputs and wrong/missing label IDs.

Predraw selected IDs and log stratum sizes/counts and n_h/N_h before oracle access.
The estimator receives only queried labels. Exact full-population truth belongs to
the evaluator. Debug mode with full labels must be explicit and never be a sampler input.

Report normal 95% intervals as approximate. Add the bounded-residual conservative
reference described in methodology §8; it can be wide. Keep raw point estimates and
raw interval endpoints, flag zero variance and sparse positives, and distinguish
optional clipped display values. Compare interval coverage and width together.

**Outputs:** frame test suite, oracle-access example, budget checks and interval
verification record. **Gate:** checks pass; do not continue by suppressing failures.

## 13. E01: frozen-model diagnostic baseline

Calculate on development first: mean q, reference prevalence, their difference in
percentage points, score histograms, reliability diagram/Brier score, directional
imbalance distribution and source-level errors. Fix any classification threshold
on validation only; F1 is secondary context, not the primary endpoint.

Measure S²(y), S²(y-q), Cov(y,q), their ratio and residual autocovariance at valid
lags 1–10 within clip/pair sequences. Aggregate lag covariances without joining
across gaps. Distinguish label autocorrelation from residual autocorrelation.
This evaluates whether correction has a plausible variance advantage and whether
contiguous residual queries are likely redundant.

Do not tune methods on test diagnostics. Full test quality diagnostics are computed
after E04's lock, or explicitly tagged evaluation-only. The fixed-corpus M0 estimate
is deterministic, so repeat neither its estimate nor its confidence interval across
1,000 seeds. M0 has no sampling-based audit interval.

**Outputs:** `predictor_diagnostics.csv`, development reliability/residual plots,
source summaries, timing and provenance note. **Gate:** numerical correctness and
transparent model bias. A poorly calibrated predictor is a finding, not a reason to
remove difficult sources or fabricate probabilities.

## 14. E02: uniform baselines before learning a sampling policy

Run M1 and M2 on validation at 5%,10%,20%,40%, with 100 audit draws initially.
Use the same uniform sampled IDs for M1 and M2 for each budget/seed; only their
estimators differ. Labels queried once count once per method-run, not twice because
two calculations reuse an oracle return. Use a common seed list across methods.

Compare mean error with Monte Carlo uncertainty, empirical sampling variance with
mean estimated variance, realized budgets, interval coverage and width. Sample
sizes are based on the actual retained validation M, not the test budget table.
No requirement that M2 must beat M1; if it loses, examine residual variance and
retain the result. Add a separate weight-tuning extension later if appropriate.

**Outputs:** per-draw records and summary for M1/M2, calibration checks and a budget
validation table. **Gate:** no unexplained estimator bias, wrong weights or label
count mismatch. Sampling error must not be mistaken for a coding bug or vice versa.

## 15. E03: fit static/temporal policies and select on development only

**Course default:** RandomForestRegressor with 64 trees, max_depth=4,
min_samples_leaf=100, random_state=42, n_jobs=1 for reference reproducibility.
Keep the same learner/settings for static and temporal inputs. These defaults
are plan choices; the current provisional block code uses different leaf settings.

Train the primary error learner to predict the **signed frame residual y-q**.
Use predicted residual mean mu_hat as the scalar stratum score, with training
out-of-fold quartiles defining up to four fixed strata. This permits separating
groups with different bias. Estimate each stratum's centered residual SD from
training out-of-fold assignments. Do not justify SRS strata solely with squared
error; a second-moment score is an optional target ablation in X02.

Procedure:

1. Build five source-grouped training folds from P02. For each feature set/window,
   fit on four folds and score the fifth. Save all OOF predictions.
2. Compute unique OOF quartile cut points and centered residual SD. Empty score
   bins are removed; equal-score ties stay together. Shrink stratum variance toward
   global development residual variance using prior count 20, then floor SD at 1e-6.
   The exact rule is in PIPELINE_IMPLEMENTATION.md §5.
3. Fit a final error learner on all training rows. Apply the frozen cuts and moment
   estimates to validation scores; report any score-distribution shift and bin sizes.
4. On validation, compare mixture alpha in {0,.5,1}. Alpha=0 is proportional
   allocation inside the given strata, not global uniform sampling. Alpha=1 uses
   Neyman allocation based on centered SD; alpha=.5 interpolates two feasible,
   separately normalized allocations. Respect E00 minima/caps/exact integer B.
5. Temporal window candidates are {5,11}. Static has no temporal window. For each
   candidate use 100 validation audit draws at the primary 10% budget.
6. Select minimum validation MSE separately for static and temporal policies.
   Tie within 1% relative MSE: prefer smaller alpha, then smaller temporal window.
   All candidates receive the same validation seed list. Keep the selection table,
   not only its winning row. This is nine candidate configurations in total:
   3 static plus 2 windows times 3 temporal mixtures.
7. Freeze model, feature schema, cut points, SDs, window and alpha. Keep the same
   chosen policy for all test budgets. Do not refit it with validation labels after
   selection in the first course run; that would change the calibration regime.

The validation set is reused development information, with six source videos;
report the resulting tuning uncertainty. Do not describe the candidate winner as
proven generally best. Historical training plus fully available validation labels
are separate development costs, not part of test budget B.

**Outputs:** OOF tables, saved static/temporal models, candidate validation audit
table, selected policies and `policy_lock.json`. **Gate:** all locked inputs and
hyperparameters recorded; no evaluation labels used in the selection function.

## 16. E04: main frame benchmark

Before running, write `experiment_lock.json` with config hash, model/cache/feature
hashes, chosen policies, exact retained test IDs, test M, seeds, methods, metrics,
intervals and the primary comparison. Commit this lock or an aggregate hash record
before launching test audits. Any later change creates a separately labelled run.

Use B=round(fraction*M), with a specified round-half-up rule for nonnegative
counts. For the complete original known test population, M=38,847 gives:

| Budget fraction | Revealed pair-frame labels |
| --- | ---: |
| 5% | 1,942 |
| 10% | 3,885 |
| 20% | 7,769 |
| 40% | 15,539 |

If P03 produced a subset, recompute these numbers from that frozen subset. Report
both fraction and integer count. Development/inference costs are separate columns.

Use audit draw IDs 0–999 and seeds 200000+draw_id. Do not search seeds for favorable
plots. Evaluation scripts read locked policies and pre-draw queries, then use the
oracle, then calculate estimates; evaluator truth is used only to score outcomes.
Run one 10%-budget draw per method as an execution check, then 100 draws, then the
full 1,000. Validation completed in earlier stages; these small test checks permit
fixing execution errors, not selecting a different algorithm based on outcomes.

M1–M4 give 4 methods x 4 budgets x 1,000 = 16,000 small CPU audit runs. M0 adds one
deterministic result. Same-seed methods need not select identical records; M1/M2
must share uniform queries, and M5 will reuse those same uniform samples.
Use a dedicated random generator for each method/budget/draw so loop order does
not affect results. Derive it from `[200000+draw_id,budget_index,method_stream_id]`
with SeedSequence; M1/M2/M5 share stream ID 1, M3 uses 3 and M4 uses 4. Store enough
metadata to replay one specified draw exactly.

For every draw save method, budget, seed, estimate, raw CI endpoints, SE, queried
labels, positive labels found, stratum n/N, actual cost, elapsed CPU time and flags.
Query logs contain selected IDs and inclusion probabilities. Full truth never
appears in a policy object or public feature artifact.

Required summary metrics: bias, MAE, RMSE in **percentage points**; 95% empirical
coverage for each declared interval; mean/median interval width; zero-variance,
zero-positive and failed draw rates; expected/realized label cost; source spread.
Failures remain in the denominator and are reported separately, with metrics for
successful draws clearly conditional on success.

Coverage MCSE is sqrt(C*(1-C)/R). For RMSE/differences, bootstrap paired draw IDs
with seed 400000 and 2,000 resamples as a Monte Carlo uncertainty summary on this
fixed corpus. It does not measure transfer to new videos. Report per-source
diagnostics separately; avoid unsupported independent-source significance claims.

Primary effect: RMSE(M4)/RMSE(M3) at 10%. Also show M4/M2. A 10% relative reduction
is a useful practical target, not a grading requirement or a promised result.
Interval width alone is not a win if empirical coverage is poor. Never silently
switch interval methods or drop a hard budget after inspecting its result.

**Outputs:** `audits.csv`, `summary.csv`, `queries.jsonl`, `failures.csv`, locked
configs/policies, reproducibility metadata and preliminary plots.
**Gate:** exact budgets, reproducible replay, complete method/budget grid and all
failures accounted for. Lack of temporal improvement does not fail the course stage.

## 17. E05: explain the result with a small control set

### Required interpretation control M5

Reuse the selected temporal residual learner from E03. Define g_i=clip(q_i+mu_hat_i,0,1),
freeze it, and use uniform residual correction with g in place of q. Do not refit
using test labels. Reuse M1/M2's sampled IDs at the same budgets and seeds.
Calculate the same metrics; M5 adds 4,000 CPU runs and zero additional GPU inference.
If M5 matches/exceeds M4, report that contextual prediction refinement may be as
useful as selective querying. Do not call the selection mechanism superior.

### Two small recommended ablations

1. Compare temporal windows 5 and 11 at the primary budget with the locked learner
   and selection recipe. A policy not selected in E03 is an exploratory ablation,
   not a replacement for the main winner. Use 1,000 draws, same seed list.
2. Remove ordered transition/lag features while retaining neighborhood summaries,
   retrain on training, and select alpha on validation only. This checks whether
   improvement comes from order-sensitive features or simple contextual smoothing.

If time is short, complete M5 and mark these two ablations deferred. Static versus
temporal removal is already tested by M3 versus M4 in E04.

Show development costs for training and validation, target audit costs separately,
and the existing-label-reuse regime. The full historical inventory is 319,153
eligible development labels before media exclusions. We are reusing them for this
offline course benchmark, not claiming to have purchased them cheaply.

**Outputs:** M5 comparison, ablation tables if run, error-source interpretation and
cost ledger. **Gate:** the report explains the observed mechanism with evidence,
including a tie or loss. Do not add a new architecture just to force a positive result.

## 18. E06: course deliverables and reproducibility handoff

Produce these final figures using the same saved summary data:

1. RMSE versus revealed labels for M1–M5; horizontal M0 error reference labelled
   as a zero-audit-label method with separate compute/development cost.
2. Bias versus labels and empirical coverage versus labels, with 95% reference.
3. Interval width versus labels, interpreted with coverage.
4. Static versus temporal versus contextual-calibration comparison at 10%.
5. One reproducible clip/example showing native scores, temporal features and the
   selected query locations; separate optional reference overlays from prediction-only views.
6. Development/inference/audit cost breakdown and actual retained population/exclusions.

Main result table: rows M0–M5, columns estimate/error metrics, coverage, width,
test-label budget and development cost. Separate deterministic and sampled outputs.
Include the data schema, sampling/estimator equations, simple architecture diagram,
split policy, actual runtime, findings, limitations and reproduction instructions.
Use the class's required report/deck format when supplied; do not invent a required
page count. This plan does not require writing those final artifacts yet.

Demo sequence: show data/version and method settings; display cached predictions;
run/replay one chosen audit seed; display selected labels and corrected prevalence;
show the aggregate experiment chart. A local notebook or CLI with plots is enough.
A custom dashboard is optional and should not delay the experiments.

Reproduction check: a clean environment reproduces one saved draw exactly and the
aggregate tables within the declared deterministic/numerical behavior. A teammate
uses the README plus retained data instructions without relying on private paths.
Do not rerun all GPU inference when verifying a CPU sampling change.

**Outputs:** aggregate report tables/figures, course report/deck source when requested,
demo notebook/script, final config and a reproducibility note under
`reports/course-project/`. **Gate:** someone can explain and rerun the project,
regardless of whether M4 is the best method.

## 19. Optional experiments after the required sequence

| ID | Question | Design and outputs | Condition |
| --- | --- | --- | --- |
| X01 | Do contiguous queries help? | Lengths 2,5,10; nonoverlapping eligible blocks; static versus temporal block score; matched expected label costs; include realized cost quantiles and actual residual variance | E04/E05 done; frozen cache reused |
| X02 | Which error target/simple learner helps? | Residual mean versus second moment; Ridge(alpha=1, train-only scaling) versus the fixed RF; entropy strata or development-tuned lambda as simple added controls | Development-only selection; label extra runs exploratory |
| X03 | How many development labels are needed? | Training label fractions 1%,5%,20%,100%, selected uniformly within source under fixed seed; refit both policies and report total cost; calibration/tuning labels counted | Core pipeline stable; avoid selecting known positives free of charge |
| X04 | Is there a real time benefit? | Small randomized frame/block annotation task with a shared UI, two annotators if available, equal unique pair-frame labels, observed setup/navigation/decision time and duplicate-item checks | Actual media/annotators; no simulated time-saving claim |

X01 block budgets are expected costs. Use positive inclusion and correct weights;
do not cut off a pre-drawn block sample at an arbitrary hard label cap. Unknowns,
missing indices and pair changes break blocks. Ordinary block length is not a
duration estimate. The unfavorable constant-score block diagnostic is motivation
to test, not a substitute for measuring MTGS residuals.

For X04, a feasible pilot is 100 unique pair-frame labels per interface format per
annotator, plus a separately counted 10% repeated-item subset. One format shows
individual queried frames with equal contextual viewing; the other requests up to
five consecutive labels per task. Counterbalance format order, log skipped items,
and charge shared clip openings fairly. Do not claim clinical annotation quality
from this small timing exercise.

Not required: new gaze-backbone training, SACF integration, a second clinical
dataset, Robust ASI/CPS/StratPPI author-code reproduction, novel proofs or a production
service. Add only if the course requirements or remaining time justify it.

## 20. Failure handling and stopping decisions

| Failure | Next action |
| --- | --- |
| Media unavailable | Record missing sources; try team copies; freeze a documented common subset if recovery fails |
| Index/box misalignment | Stop that clip, correct the map and recheck; never compensate with labels |
| MTGS/runtime incompatibility | Fix pinned upstream GPU environment in the smoke job; leave CPU environment intact |
| GPU out of memory | Lower batch size; if image/window settings change, version config/cache and rerun consistently |
| Kaggle interrupted/connection unavailable | Preserve job/version state and completed shards; resume or move the same bundle to a team GPU |
| Native directional mapping uncertain | Stop cache generation; verify source code/hand cases before any prevalence result |
| Residual correction loses to human-only | Keep result, inspect development residual variance; optional independently tuned weight is a new declared comparison |
| Temporal method ties/loses | Finish analysis; show why context adds little or does not transfer |
| Coverage below nominal | Report failure; check estimator implementation, strata and sparse observations; retain conservative reference |
| Test-driven algorithm change desired | Keep old run, change config/version, label the new analysis exploratory |
| Time pressure | Complete M0–M4, M5 and report; defer blocks/extra learners/paper baselines |

No specific calendar duration or GPU quota is assumed. Record P04's measured
throughput and the actual course deadline before making a time budget. The ordered
milestones already define what to drop first if resources are limited.

## 21. How we will work through the sequence together

For each stage: implement the missing command if needed; review its inputs and
outputs; run the smallest smoke case; resolve errors; run the stage; inspect its
gate artifacts; update the tracker and commit code/config/aggregate findings.
Then move to the next stage. Do not mark an implementation task done solely because
its file exists or a Kaggle job was submitted.

Use feature branches for implementation and pull reviewed code before another
teammate runs a stage. Keep one named owner and one checker per stage in the tracker;
the plan does not assign teammates without their agreement. Model inference and
data processing should finish before separate experiments reuse their caches.

Store credentials/media privately, code/configuration in Git, and approved
aggregate outputs/report sources in `reports/course-project/`. If GitHub is offline,
record the local commit and pending push; an offline commit is not a successful sync.
