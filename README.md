# Mutual-looking prevalence audit

Research project for measuring benchmark-defined mutual-looking prevalence from
frozen gaze predictions and a limited sample of reference labels.

**Current priority: methodology.** The four-pass review is complete. The code is a
provisional synthetic scaffold and does not yet implement the complete revised study.
No real-data results or performance improvements have been established.

## Start here

- [Consolidated methodology](docs/methodology.md): target, contribution, equations,
  comparisons, access protocol, evaluation and costs.
- Four review passes: [validity](docs/revisions/01-validity-review.md),
  [contribution](docs/revisions/02-contribution-review.md),
  [experiment design](docs/revisions/03-experiment-review.md),
  [feasibility and decisions](docs/revisions/04-feasibility-review.md).
- [Implementation roadmap](docs/roadmap.md) and [data contract](docs/data-contract.md).
- [Team Git workflow](CONTRIBUTING.md).

The principal proposed comparison separates **temporal context in scoring** from
**contiguous batches in annotation**. It uses a common predictor and estimator to
compare static/frame, temporal/frame, static/block and temporal/block policies.
Correction, stratification and active sampling are existing statistical methods.

## Run the provisional software demo

Python 3.11 or newer and [uv](https://docs.astral.sh/uv/) are required.
From the repository root:

```powershell
uv sync --frozen --extra dev
uv run pytest
uv run ruff check .
uv run gaze-audit demo --draws 100 --output outputs/demo
```

Choose a new output directory for each run. Demo scores and labels are invented.
The demo produces `report.json`, `summary.csv`, per-draw `audits.csv`, and query
logs. They verify software operation and must not be reported as research results.

For a normalized prediction cache with separate labels and provenance:

```powershell
uv run gaze-audit run --data data/processed/childplay --output outputs/childplay-run --draws 1000
```

That command requires the [documented input contract](docs/data-contract.md).
Actual ChildPlay/VSGaze import, MTGS inference, frame-context scoring, conservative
intervals and the full baseline suite remain roadmap work. The current demo covers
initial block sampling and approximate intervals only. It uses fully labeled
synthetic development sets and charges those labels separately.

## Repository layout

```text
docs/                  Methodology, revision passes and implementation tasks
src/gaze_audit/         Provisional offline audit package
tests/                 Statistical and data-boundary checks
.github/               CI and contribution templates
data/                  Local datasets, ignored by Git
checkpoints/           Local model weights, ignored by Git
outputs/               Local experiment artifacts, ignored by Git
```

Do not commit raw videos, reference-label tables, weights, credentials or generated
experiment artifacts. Track hashes and reproducible run configurations instead.
Original code licensing is not yet selected by the team; upstream model and data
terms remain separate.
