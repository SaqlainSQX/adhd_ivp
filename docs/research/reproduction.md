# Reproducing the validation checks

The scripts inspect existing annotations and perform planning calculations. They
do not run MTGS and do not demonstrate an accuracy gain by the proposed method.

## Environment and inputs

From the repository root, install the pinned optional HDF5 reader:

```powershell
uv sync --frozen --extra dev --extra research
New-Item -ItemType Directory -Force -Path data/research
Invoke-WebRequest -Uri 'https://zenodo.org/records/17357752/files/VSGaze.tar.gz?download=1' -OutFile data/research/VSGaze.tar.gz
```

The archive is 103,425,122 bytes. The script checks the official release MD5 before
reading it. Do not substitute an arbitrary HDF5/pickle archive: this specific
release stores pandas object columns as NumPy object-array pickles. The reader
restricts class resolution to the needed NumPy array constructors and never
extracts archive members to disk. This is a pinned-release inspection utility,
not a general-purpose hostile-file sandbox.

```powershell
uv run --extra research python scripts/research/inspect_vsgaze.py --archive data/research/VSGaze.tar.gz
uv run --extra research python scripts/research/feasibility_checks.py
```

`outputs/research/vsgaze-inventory.json` contains source IDs and aggregate counts;
`outputs/research/feasibility-checks.json` contains arithmetic and toy diagnostics.
Raw data and individual labels remain ignored by Git. The committed copies in
this folder omit individual source IDs and preserve only aggregates and provenance.

## What is checked

- Canonical unordered real pairs, agreement between reverse orientations, binary
  labels, unknown counts, frame/clip counts and parsed original-source counts.
- Parsed train/validation/test source intersections.
- Query units with maximum lengths 1,2,5,10, preserving tails and breaking at
  missing integer frame indices. Downsampled timelines require separate alignment
  review before model experiments; these diagnostics use the published indices.
- Centered residual variances for a constant label-informed q=p diagnostic. The
  ratio is S²(block residual)/(mean block cost * S²(frame residual)). It compares
  uniform block-SRS to the frame-SRS variance expression at matched expected cost;
  continuous reference counts are used when exact integer budget matching is impossible.
- Uniform frame-SRS reference standard errors and exact hypergeometric zero-positive
  probabilities; hypothetical unknown-label bounds and development-cost scenarios.

Original source IDs are parsed from the release's `videoID_start-end` and
`videoID_start-end-downsampled` names. This is not identity/session verification.
Frame/clip paths are annotations only; no present media availability is implied.

## Interpretation limits

The use of full test labels makes these explicitly exploratory diagnostics.
Constant q=p is an oracle-informed diagnostic, not an available MTGS score. Strong
label clustering need not imply the same residual clustering after model assistance.
Cost scenarios and toy sequences are illustrative and never substitutes for measured
annotation time, held-out risk prediction or actual method comparisons.

Local verification: archive checksum and inventory reproduced; planning values
recomputed from the inventory; lint and existing statistical tests checked. The
tests do not certify scientific novelty or empirical effectiveness.
