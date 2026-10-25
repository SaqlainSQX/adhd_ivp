# Implementation checklist for the course execution plan

This document specifies missing software. It does not claim these commands already
exist. See [COURSE_PROJECT_PLAN.md](COURSE_PROJECT_PLAN.md) for the experiment order
and [EXPERIMENT_TRACKER.md](EXPERIMENT_TRACKER.md) for current status.

## 1. Available entry points today

| Existing command | What it actually does |
| --- | --- |
| `uv run gaze-audit demo ...` | Invented scores/labels and provisional block pipeline |
| `uv run gaze-audit run ...` | Provisional block audit on the strict normalized CSV contract |
| `uv run --extra research python scripts/research/inspect_vsgaze.py --archive ...` | Pinned-release annotation inventory and constant-score block diagnostic |
| `uv run --extra research python scripts/research/feasibility_checks.py` | Planning arithmetic from the preceding inventory output |
| `uv run --extra dev pytest ...` | Existing package tests; frame extensions still need additional tests |

No complete data-to-MTGS-to-frame-audit entry point exists yet. The JSON design
file is not loaded by the provisional CLI. Preserve that distinction in README
updates and teammate handoffs.

## 2. Proposed unified interface: not implemented

Implement one clear stage runner instead of a collection of ad-hoc notebook cells.
The desired interface is:

```text
gaze-audit pipeline check --stage <stage-id> --plan configs/course-project.json
gaze-audit pipeline run --stage <stage-id> --plan configs/course-project.json --run-id <new-id>
gaze-audit pipeline status --run-id <existing-id>
gaze-audit pipeline replay --run-id <existing-id> --method M4 --budget 0.1 --draw 0
```

These command forms are a specification. Do not run them until implemented and
their help/validation tests pass. `check` reports missing inputs, hashes, unresolved
model settings and dependency gates without submitting jobs. `run` refuses to
overwrite a completed run. Resume requires identical input/config hashes and uses
completed shard manifests, not a blind rerun. `status` distinguishes submitted,
running, failed and validated-complete. `replay` uses saved policies and selected IDs.

The runner must reject `execution_status=plan_only_not_consumed_by_current_cli`
until it supports the declared schema and records an actual run snapshot. A copied
runtime config can then declare execution readiness after null values are resolved;
do not modify the historical design file just to imply execution happened.

## 3. Modules to implement, in dependency order

| Order | Suggested module | Input | Output | Acceptance behavior |
| ---: | --- | --- | --- | --- |
| 1 | `pipeline/config.py` | Versioned JSON plan/runtime config | Typed validated settings | Checks stage IDs, budgets, seed schema, dependency gates and unresolved model/data fields |
| 2 | `pipeline/artifacts.py` | Config and actual artifact files | Hash manifests and run status | Atomic completion, no overwrite, failed-run retention and hash-compatible resume |
| 3 | `adapters/vsgaze.py` | Pinned HDF5 release | Public manifests, oracle table, exclusions | Canonical pair/ID mapping, reverse reconciliation, binary/unknown distinction |
| 4 | `pipeline/media.py` | Clip manifest and actual media | Frame/time mapping, availability, alignment review bundle | Handles unavailable sources/downsampling; never declares visual alignment from a join alone |
| 5 | `inference/mtgs_adapter.py` | Public frames/tracks/geometry and pinned model | Native directional score shards | Exact upstream API verified; no label inputs; evaluation mode; actual configuration recorded |
| 6 | `pipeline/cache.py` | Inference shards | Versioned enriched cache and legacy export | Expected IDs, direction mapping, finite scores and consistent model/config hashes |
| 7 | `features/frame.py` | Public prediction/geometry sidecars | Static and temporal keyed features | Label-free API, boundary/gap handling, deterministic order, no source-ID memorization |
| 8 | `policies/frame.py` | Training features and development residual labels | OOF scores, strata, SDs, models | Source-grouped folds; identical learner for static/temporal; development-only selection |
| 9 | `sampling/frame.py` | Frozen strata, counts, budget and seed | Pre-drawn query plan | Exact B, SRS within strata, no replacement, positive inclusion and deterministic integer allocation |
| 10 | `estimation/frame.py` | Frozen q, plan and queried labels | Estimate, variance, interval outputs | Correct finite-population formula, census, approximate/conservative distinction |
| 11 | `experiments/frame_audit.py` | Locked artifacts and oracle | Per-draw audits, query logs and failures | All M1–M4 budgets/draws; M0 once; no policy fitting inside test loop |
| 12 | `experiments/controls.py` | Selected temporal residual model | M5 and ablation outputs | Same uniform queries/costs; no extra test training |
| 13 | `reporting/course.py` | Saved aggregate results | Tables, plots, cost ledger and demo/replay bundle | Explicit units, costs, failures, retained denominator and evaluation designation |

These are suggested source locations under `src/gaze_audit/`. Consolidate small
modules if useful while preserving the boundaries and acceptance behavior.

## 4. Data adapter details that must not be guessed

- Verify whether a raw `pairs` value is a real ID or an index for each upstream
  consumer. Use the release's `person_ids` mapping and hand examples; do not assume
  array position equals track ID. Exclude the zero/placeholder head correctly.
- Verify raw box coordinate order before converting to the canonical normalized
  `(xmin,ymin,xmax,ymax)` sidecar. Validate `0<=xmin<xmax<=1` and corresponding y,
  with documented handling for tiny numerical tolerance only. Log invalid boxes.
- Match original clip/timebase and any extraction stride in P03. Retain both the
  original frame index and verified sequence/timestamp fields. Preserve gaps.
- Generate `record_id` deterministically from source, clip, frame and sorted pair.
  Swapping person order also swaps directional scores and geometry associations.
- Export reference values only in an oracle table. Current archive-reader outputs
  include gaze fields; they are not safe model inputs without an explicit allowlist.
- Write an enriched public cache/sidecar schema v2. A narrow v1 export can contain
  only the columns accepted by the current `normalize_predictions`; it does not
  silently become the richer feature cache.

## 5. Policy and allocation details

Primary error target is signed residual y-q; the provisional block squared-error
model is not the primary frame policy. Use out-of-fold score quartiles and
centered residual moments. For n training OOF rows in a stratum, use the fixed
shrinkage rule:

```text
d = max(n - 1, 0)
v_h = (d * s_h^2 + 20 * v_global) / (d + 20)
sigma_h = max(sqrt(v_h), 1e-6)
```

If n<2 use d=0 and the global variance. Population and sample SD conventions must
be documented consistently. Do not use unqueried evaluation labels to repair SDs.

For exact frame allocation, first establish feasible minima `min(N_h,20)`. Normalize
the proportional and SD-weighted count vectors separately to the same B under caps.
Mix their continuous vectors, floor them and distribute the remaining count by
largest fractional remainder, respecting caps. If rounding creates a contradiction,
fail with diagnostics rather than silently changing B. Test edge cases at census.

Candidate ties are all rows with MSE <= best_MSE * 1.01. If best_MSE=0, only exact
zero candidates qualify. Then prefer smaller alpha and smaller temporal window.
Use the exact same rule for repeated runs; no subjective choice of the nicest plot.

For RNG, derive a stream using NumPy SeedSequence from
`[base_seed+draw_id, budget_index, method_stream_id]`. Uniform M1/M2/M5 share
stream ID 1; M3 uses 3 and M4 uses 4. Development base seed is 100000 and main audit
base is 200000. A stable stream map is saved in the lock; do not use Python's
process-randomized `hash()` to create seeds.

## 6. Kaggle launcher and inference-job contract

Implement a small local launcher before any project-account operations. It accepts
a credential directory and prepared job folder, creates a child-process environment,
removes inherited Kaggle credential values there and sets this project's selectors.
It does not mutate machine/user environment variables or another agent's files.
Do not print token content or bundle the credential directory. Verify the intended
account using an appropriate authenticated read-only operation for the installed CLI.

Keep a smoke job bundle and a shard job bundle containing:

```text
kernel-metadata.json          Real owner/private kernel ID and pinned input sources
inference.py                 Tested pinned-MTGS adapter entry point
job-config.json              Actual checkpoint/config/manifest/shard references
runtime-requirements.txt      Pinned GPU environment resolved in P04
```

Required inputs are public geometry, media and weights, uploaded or attached only
as permitted. Hidden oracle files and local credentials are never attached.
Job outputs include `shard_predictions`, `shard_manifest.json`, environment record,
throughput/memory stats and logs. Partial outputs have `completed=false`; successful
Kaggle status is necessary but insufficient without local cache validation.

Resolve credentials, notebook metadata and dataset ownership at execution time.
No account names, tokens, dataset slugs, GPU type, quota or runtime timeout are
invented by the design configuration. GPU resources are used for inference; cached
statistics run on CPU and can continue without a Kaggle connection.

## 7. Required verification additions

Data: canonicalization/conflict cases, unknown exclusions, source leakage, invalid
box handling, and exact joins after unavailable-media exclusions.

Features: label-change invariance, shuffled-row invariance, no cross-pair/split
context, valid gap handling, downsampled timeline and short-window boundaries.

Sampling/statistics: exhaustive single/multiple-stratum examples, exact B at all
caps/minima, no replacement, census equality/zero variance, deterministic replay,
oracle access limited to selected IDs, empirical versus known small-population
variance, and conservative-bound small-population checks.

Experiment orchestration: test that the evaluation path cannot fit/select models,
all declared method/budget cells are present, failure counts are retained, M0 is
not counted as repeated sampling evidence, and M1/M2/M5 share uniform query IDs.

Focus tests on these statistical/data boundaries. Documentation-only changes do
not need a repeated full experiment suite.

## 8. What to implement first

Start with config/artifact helpers and P02's normalized archive export. They unlock
media alignment and prevent costly inference on ambiguous IDs. Account isolation
can be prepared alongside local setup, but a Kaggle API key is not required to
complete annotation processing. Next implement P03 and the smallest P04 smoke job.
Do not start implementing every optional baseline before that job works.
