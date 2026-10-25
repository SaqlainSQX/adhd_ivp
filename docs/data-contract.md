# Provisional cache contract

This is the existing strict v1 scaffold contract. The enriched directional-score,
geometry and temporal cache planned for the course is specified in
[COURSE_PROJECT_PLAN.md](COURSE_PROJECT_PLAN.md) and
[PIPELINE_IMPLEMENTATION.md](PIPELINE_IMPLEMENTATION.md). That v2 interface still
needs implementation; extra columns cannot be passed to the current v1 reader.

The scaffold consumes a normalized CSV export. It is **not** a native VSGaze HDF5
reader. The actual adapter must follow the [official schema](https://www2.idiap.ch/en/dataset/vsgaze)
and pass the inventory/alignment gates in the methodology.

```text
dataset/
  provenance.json
  train/predictions.csv
  train/labels.csv
  validation/predictions.csv
  validation/labels.csv
  test/predictions.csv
  test/labels.csv
```

All prediction CSVs contain exactly:

| Column | Meaning |
| --- | --- |
| record_id | Stable unique string for one eligible unordered pair-frame |
| source_id | Original video ID, stable across all clips and splits |
| clip_id | Clip ID within its source |
| frame_index | Integer frame index on a documented timeline |
| person_a, person_b | Nonnegative real track/person IDs |
| probability | Frozen mutual-looking score in [0,1] |

Each labels CSV contains exactly `record_id,label`, with one binary value (0 or 1)
for every eligible prediction row. No unknown labels occur in this normalized
export. The adapter must record exclusions and expose the eligibility mask without
exposing binary values to the sampler.

The reader canonicalizes unordered pair IDs, excludes self/placeholder pairs, and
rejects duplicate IDs or pair-frames. The adapter must reconcile and deduplicate
reverse orientations before export, including rejecting label/score conflicts.
Scores and labels must use exactly matching eligible record IDs. Original source
IDs cannot overlap between train/validation/test. Absence of source overlap does
not itself establish subject independence or backbone training separation.

Blocks stop at frame gaps and source/clip/pair changes. Excluding unknown rows must
preserve the original frame index so an unknown record creates a gap. If source
frames were extracted at a stride, explicitly normalize the index and record the
mapping rather than accidentally merging unrelated frames.

For real inputs `provenance.json` must include:

```json
{
  "synthetic": false,
  "predictor": "exact model and decoder/post-processing variant",
  "checkpoint_sha256": "actual checkpoint content hash",
  "upstream_revision": "actual source commit",
  "configuration_sha256": "actual preprocessing/inference configuration hash",
  "media_alignment_verified": true,
  "source_checkpoint_separation_reviewed": true
}
```

The booleans are operator attestations, not independent verification by the CLI.
Keep a supporting exposure and alignment report. The runner hashes all cache and
label inputs, records configuration/dependency versions, and logs revealed test
queries. The current risk model uses prediction summaries only; geometry and
per-frame context features belong to later implementation tasks.

Separate CSV files and the oracle API provide an offline access boundary, not a
security sandbox. Genuine protected annotation access needs a separate process or
service. Evaluation code intentionally has full reference access for auditing.
