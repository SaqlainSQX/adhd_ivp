# Mutual-looking prevalence audit

Research project for measuring benchmark-defined mutual-looking prevalence from
frozen gaze predictions and a limited sample of reference labels.

**Current priority: execute the course-project plan in sequence.** The methodology
and deep review are documented. The annotation adapter, frame estimator and
preliminary human-only baseline now run; the complete frame-based study is in progress.
No real-data performance improvement by the proposed method has been established.

## Start here

- [Sequential course-project plan](docs/COURSE_PROJECT_PLAN.md): detailed processing,
  inference and experiment stages, commands, outputs and gates.
- [Execution tracker](docs/EXPERIMENT_TRACKER.md) and
  [implementation checklist](docs/PIPELINE_IMPLEMENTATION.md).
- [Actual execution evidence](docs/research/execution-progress.md): normalized data,
  media acquisition, frame-index checks and the 4,000-draw human-only reference.
- [Design configuration](configs/course-project.json): defaults, budgets, methods,
  dependencies and settings to resolve before running; not yet consumed by the CLI.
- [Deep idea assessment](docs/research/idea-validation.md): conditional-go verdict,
  prior-work overlap, independently verified data and block/cost diagnostics.
- [Research evidence matrix](docs/research/evidence-matrix.md): primary sources and
  what each does and does not establish.
- [Consolidated methodology](docs/methodology.md): target, contribution, equations,
  comparisons, access protocol, evaluation and costs.
- Four review passes: [validity](docs/revisions/01-validity-review.md),
  [contribution](docs/revisions/02-contribution-review.md),
  [experiment design](docs/revisions/03-experiment-review.md),
  [feasibility and decisions](docs/revisions/04-feasibility-review.md).
- [Implementation roadmap](docs/roadmap.md) and [data contract](docs/data-contract.md).
- [Team Git workflow](CONTRIBUTING.md).

The public annotation inventory has now been independently checked. Raw-media
alignment, actual MTGS predictions and empirical method gains remain unverified.

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
That original CLI covers provisional block sampling with synthetic development
data. The separate scripts now support checksum-pinned ChildPlay annotation import,
public-media acquisition, source-frame mapping, exact-budget frame estimation,
conservative intervals and a replayable human-only baseline. MTGS inference and
the full method comparison remain in progress; consult the execution tracker.

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
