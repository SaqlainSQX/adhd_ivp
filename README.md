# Mutual-looking prevalence audit

Research project for measuring benchmark-defined mutual-looking prevalence from
frozen gaze predictions and a limited sample of reference labels.

**Main course experiment complete and independently validated (7 November 2026).**
At the 10% test-label budget, static guidance achieved 0.2603 percentage-point
RMSE, temporal guidance 0.2765, and uniform residual correction 0.5529. Guided
sampling helped on this fixed subset; the locked temporal policy did not beat
static guidance. All 20,000 sampled audits passed independent replay and
recomputation. Both registered interpretation ablations are complete and checked;
extra transition features showed no clear benefit. See the
[results assessment](docs/research/course-results.md).

## Start here

- [Sequential course-project plan](docs/COURSE_PROJECT_PLAN.md): detailed processing,
  inference and experiment stages, commands, outputs and gates.
- [Execution tracker](docs/EXPERIMENT_TRACKER.md) and
  [implementation checklist](docs/PIPELINE_IMPLEMENTATION.md).
- [Results and limitations](docs/research/course-results.md),
  [aggregate main evidence](docs/research/main-course-results.json), and
  [registered interpretation experiments](docs/FOLLOWUP_EXPERIMENTS.md).
- [Run and resume instructions](docs/RUN_EXPERIMENTS.md): verified subset, local
  environments, full sequential execution, outputs and exact audit replay.
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

The fixed media-available population contains 53 verified sources, including
10,316 eligible test pair-frames from 10 sources. Predictions and audit results
are complete for that population; unavailable or misaligned sources remain excluded.

The completed comparison uses common frozen predictions and a common estimator
to compare static and temporal frame-query guidance against uniform controls.
Contiguous-query experiments remain optional. Correction, stratification and
active sampling are existing statistical methods.

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
conservative intervals and a replayable real-data study. Use the separate
frame-study commands in the run instructions to reproduce the completed main
comparison; consult the execution tracker for the remaining interpretation check.

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

Do not commit raw videos, reference-label tables, weights, credentials or per-query
experiment artifacts. Track hashes, reproducible configurations and the selected
aggregate report/figures under `reports/course-project/` instead.
Original code licensing is not yet selected by the team; upstream model and data
terms remain separate.
