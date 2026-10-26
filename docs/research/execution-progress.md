# Execution evidence, 26 October 2026

These are exploratory course-project results. Model-assisted and temporal-method
improvements have not yet been measured. The full sequential protocol remains in
[COURSE_PROJECT_PLAN.md](../COURSE_PROJECT_PLAN.md).

## Data preparation

The checksum-pinned VSGaze release was exported to ignored
`data/processed/vsgaze-17357752-v1`. Independent checks verified all CSV hashes,
unique identities, person/frame joins, exact oracle/eligible population equality,
source-disjoint splits and five source-group training folds. Public inference
tables contain geometry and availability bookkeeping, with reference values in
a separate oracle table. Availability is not a predictive feature.

| Split | Frames | Source videos | Eligible binary pair-frames | Positive |
| --- | ---: | ---: | ---: | ---: |
| Train | 100,209 | 68 | 285,585 | 6,396 |
| Validation | 10,283 | 6 | 33,568 | 259 |
| Test | 9,986 | 21 | 38,847 | 651 |

Unknown labels remain excluded rather than treated as negatives. Out-of-image
boxes are clipped to the image bounds, with clipping flags preserved. No known
binary pair was removed for invalid geometry in this release. See the full
[preparation validation](data-preparation-report.json).

## Frame mapping and acquisition

The [official ChildPlay archive](https://zenodo.org/records/8252535) includes the
source URLs, extraction script and nine documented clips with an intentionally
preserved one-frame lag. Its downsampled clips skip alternate source frames, while
JPEG filename indices increase by one. P02's `original_frame_index` field therefore
denotes the **annotation filename index**, not a decoded source index.

P03 creates a separate mapping without rewriting P02 IDs:

```text
relative = annotation_filename_index - clip_start + 1
stride = 2 for downsampled clips, otherwise 1
decoded_source_index_0based = start - 1 + stride*(relative-1) + downsampled - special_lag
```

All 120,478 VSGaze frames map within the original released clip lengths;
3,809 belong to downsampled clips and 2,701 to lagged clips (sets may overlap).
The original release has 71 additional frames. Their absence in VSGaze is not
explained by this check. Mapping alone does not prove visual alignment.
See [mapping provenance](frame-mapping-report.json).

Private Kaggle job `watasimycola/social-gaze-media-probe`, version 1, could read
metadata for five deterministic public YouTube sources. Actual downloads in
`social-gaze-media-pilot`, version 1, then encountered a login/bot challenge for
all three pilot sources. No cookies or challenge bypass were used. The normal
public download route on this PC successfully downloaded source `1Aea8BH-PCs`;
the local three-source pilot then downloaded and decoded 1,638 JPEGs, including
the downsampled and deliberately lagged cases. First/middle/last geometry overlays
passed inspection. Full collection is running; missing/private/challenged videos
remain recorded as failures. One-frame source-count differences are downloaded
into a separate pool for additional visual review before inclusion.

A second visual review checked 36 images from 12 clips, four clips per split,
including child/adult interactions, head turns, clip boundaries and background
faces. The displayed geometry aligned with visible heads. Some public boxes cover
poster/toy/background faces; these released entities are retained rather than
silently redefined. See [visual review](strict-media-visual-review.json).

The public Hugging Face search result `goldpotatoes/ChildPlay` is an unrelated
board-game dataset and is not used. The inspected `kunli-cs/CP_gaze` listing
contains annotation/metadata files, with a gated dataset card; gated contents
were not accessed. Related official ChildPlay-Hand media is being checked only
as an acquisition fallback, but its streaming inspection timed out. The working
local route is being used. No substitute images are treated as ChildPlay data.

## Frozen predictor runtime

The currently released `Idiap/mtgs-vsgaze` artifact contains **MTGS-DINO temporal**
weights: five temporal embeddings and a 32x32 scene-position grid. The execution
uses this released variant at scene resolution 448, head size 224, patch size 14,
and context offsets -6,-3,0,3,6. This is an execution clarification made before
method-effectiveness comparisons; it is not an original-2024-checkpoint replication.

MTGS source is pinned to `a2ce45f44ed73d86e89e16bffb6be7a9567e3052`, DINO source to
`7764ea0f912e53c92e82eb78a2a1631e92725fc8`, and the official checkpoint release to
Hugging Face revision `1b8b24a275fa2afe2e39d057291975bd87add35f`. The original
training artifact was checksum verified and loaded with explicit scheduler globals
under `weights_only=True`; an inference-only tensor dictionary was exported.
See [checkpoint provenance](mtgs-checkpoint-provenance.json).

The local RTX 4060 Laptop has 8 GiB VRAM. A separate ignored `.venv-mtgs` runs
Python 3.13.1, PyTorch 2.11.0+cu128 and CUDA 12.8. Shared global Python and the
other agent's Kaggle configuration are unchanged. Native social-gaze inference
uses all public real tracks, one zero placeholder, P02 clipping followed by the
upstream square-box transform, deterministic preprocessing and zero missing
context. Training augmentation and hidden gaze/reference fields are excluded.

The unused auxiliary heatmap decoder exceeded the chosen 50% GPU memory cap.
Pruning only that independent output produced exactly identical native LAH/LAEO
logits in the full-versus-pruned single-time check. Heatmap/postprocessed metrics
are consequently unavailable from this native-only cache. No native weights were
trained or changed. The native score remains the minimum of the two sigmoid LAH
probabilities.

Float16 autocast was checked on public training inputs against float32: the first
window's maximum probability difference was 0.001507 (prespecified tolerance .002).
Across the 12 overlapping training frames, maximum native-q difference was
0.001940. This is a numerical development check, not an accuracy or novelty result.
The AMP predictor is now fixed for all compared methods. Caching public input
preprocessing changed none of the 100-frame predictions and improved measured
throughput to 8.03 frames/s. Peak allocated memory in that run was 1.47 GB.
See [runtime smoke evidence](mtgs-runtime-smoke.json).

A 37-source, hash-frozen shard snapshot has begun inference locally. These caches
can be merged only after the final availability/review population is frozen;
partial source coverage is not a final experiment. Static and temporal feature
builders already ran on 236 real pair predictions from the 100 training frames.
The signed-residual policy and locked M0-M5 runner pass software integration checks,
including invariance of test queries/locks to changed test reference values. Real
policy selection and method comparison still await complete caches.

## Human-only annotation reference: M1

Before media filtering, the test annotation population contains 38,847 eligible
pair-frames and prevalence **1.675805%**. This diagnostic must be rerun on the final
media-verified common population before comparison with M2–M5.

For each budget, 1,000 independent SRS-without-replacement draws were generated
using the planned `SeedSequence([200000+draw,budget_index,1])` scheme. All query
index files were saved before opening reference values. Saved population indices
and query files allow exact replay. No predictor or learned policy is used.

| Fraction | Exact labels per draw | RMSE (percentage points) | Normal 95% coverage | Exact hypergeometric coverage |
| --- | ---: | ---: | ---: | ---: |
| 5% | 1,942 | 0.2824 | 94.1% | 95.9% |
| 10% | 3,885 | 0.1926 | 95.4% | 95.2% |
| 20% | 7,769 | 0.1322 | 94.8% | 95.2% |
| 40% | 15,539 | 0.0798 | 95.2% | 96.0% |

There were no failed, zero-positive or zero-variance draws. At 10%, empirical
variance was 3.7119e-6, mean estimated variance 3.8197e-6, and known SRS design
variance 3.8172e-6. The normal interval's average width was 0.7649 percentage
points; the exact interval's was 0.7896. The bounded reference covered all 1,000
draws and was wider, averaging 3.8556 percentage points. Coverage differences
at this replication count have Monte Carlo noise; these are fixed-corpus checks.

Full aggregate results: [M1 baseline JSON](m1-annotation-baseline.json). The run
took about 123 seconds locally. Reused archive references simulate annotation
queries; no new human annotation time or clinical validity was measured.

## Reproduction

Run from the repository with the project virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp outputs/pytest-review-02
.\.venv\Scripts\python.exe scripts/prepare_childplay.py --output data/processed/NEW-P02-VERSION
.\.venv\Scripts\python.exe scripts/validate_prepared_data.py --report outputs/p02-review.json
.\.venv\Scripts\python.exe scripts/prepare_frame_mapping.py --output data/processed/NEW-MAPPING-VERSION
.\.venv\Scripts\python.exe scripts/run_human_baseline.py --output outputs/experiments/NEW-M1-RUN
```

Completed data/run directories refuse overwrite. Raw data, query outputs,
credentials and model checkpoints remain ignored by Git. The isolated Kaggle
launcher sets credentials/configuration only in its child process, preserving
the other agent's account configuration. At this checkpoint, local project
commits exist; current GitHub synchronization still needs a successful push.
