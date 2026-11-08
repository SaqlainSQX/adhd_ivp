# Timed round D: completed research and evidence

User-authorized 30-minute checkpoint: 8 November 2026, approximately 11:25 IST
(05:55 UTC). Round began at about 10:54 IST. Timer id
`30-minute-research-checkpoint` is a single timebox reminder, not an ongoing job
monitor. At the checkpoint, summarize this file and remove the timer; launch no
new experiment. The numerical work and required review finished before it.

The exploratory round is complete. **Add the power-weight result as an extension;
retain the locked main study and its negative temporal finding.** D1 selected
lambda0.5 on validation for both frozen query designs. D2 selected K8 on
validation; it loses to K4 at the primary test budget. No combined K/lambda
search or further grid was launched after these outcomes.

| Primary B1032 comparison | Result |
| --- | --- |
| Power score / same-query K4 | RMSE0.196725 /0.219884 pp; ratio0.894677, Monte Carlo95% range[0.871237,0.919003]; passes registered descriptive10% threshold |
| Validation-selected K8 / K4 | RMSE0.234413 /0.219884 pp; ratio1.066080 [1.001280,1.135466]; loss retained |
| Power uniform / original M2 | RMSE0.462234 /0.552886 pp; ratio0.836038 [0.809596,0.865208]; secondary gain |

The previous B1 score result was0.207857 pp on stream7. This round's control uses
stream21, so the same-query10.5% effect differs from the5.4% change relative to
that earlier simulation number. No population or labels changed. Post-hoc
exact finite-population design RMSE is0.215985 vs0.192033 pp (11.1% lower),
supporting the variance explanation only on this fixed population.

At10%, power-score normal coverage is0.947, exact binary reference0.996 with
mean width8.6978 pp. At40%, normal coverage falls to0.391, versus K4's0.450;
exact coverage is1 with width1.2075 pp. Point accuracy gains do not fix normal
interval reliability. Exact reference intervals have a distinct center and can
exclude the residual estimate. All ties, losses and budgets remain reported.

## Execution and checks

- Protocol/config frozen in commit4da6bf3; numerical code6d65833. CPU only;
  all training labels191956 and reused validation labels25139, same frozen
  predictions/test population10316. No new Kaggle/GPU work or credentials used.
- Raw root:`outputs/experiments/timed-d-20261108-v1`. Registered seed starts
 100000/200000, score stream21, uniform1,1000 draws/candidate. Validation22,000
 candidate evaluations; test24,000 method-draw evaluations, including shared
 query streams (not24,000 independent experiments). CPU runner275.5 seconds.
- Independent verification passed all24,000 test cases: query hashes/RNG,
 budgets/inclusion, points/FPC variances, normal/bounded endpoints, exact integer
 endpoints/tail checks, coverage and RMSE. Training moments and every validation
 candidate/selection also passed. Separate checker verified all24 bootstrap
 comparisons, shared queried records and86 prior tracked evidence files.
-49 tests passed in12.38 seconds; Ruff passed. First test attempt had4 sandbox
 temporary-directory setup errors,45 passed. Retried with an in-project unique
 temporary directory; no test assertions changed.
- First plot command failed because the separate plotting environment did not
 have the package installed. Kept its log; removed that unnecessary dependency
 from the plot-only script and succeeded in a new log. No numerical rerun.
  A later report-only scope clarification hit a duplicate-keyword error; its
  failed v3 log is retained. Corrected dictionary merging; final v4 succeeded.
- Two figures visually reviewed: readable axes/legends, all six policies, high
 budget coverage collapse visible. Original main/B/C evidence unchanged.
- Generic inherited `scope` text in raw comparison JSON says streams differ.
 The correct detail is shared exact queries for D1/K4 and uniform/M2; common
 seeds/different designs across K. Raw evidence retained; corrected scope and
 explicit note are in the derived report and comparison check.

## Commands and deliverables

```powershell
.venv/Scripts/python.exe scripts/run_timed_research.py *> outputs/timed-d-v1-console.log
.venv/Scripts/python.exe scripts/validate_timed_research.py *> outputs/timed-d-v1-independent.log
.venv/Scripts/python.exe scripts/check_timed_comparisons.py *> outputs/timed-d-comparison-check.log
.venv/Scripts/python.exe scripts/diagnose_timed_design_variance.py *> outputs/timed-d-design-variance.log
.venv-mtgs/Scripts/python.exe scripts/report_timed_research.py *> outputs/timed-d-report-v4.log
.venv/Scripts/python.exe -m pytest -q --basetemp outputs/pytest-timed-d-v1
.venv/Scripts/ruff.exe check src scripts tests
```

Existing numerical/verification outputs are write-protected by runner guards;
reruns need a new versioned configuration/output. Reports can be regenerated
from accepted raw outputs. Tracked aggregate snapshots/hashes are under
`docs/research/timed-d-*`; raw queries/labels remain ignored locally. The report
is [timed-d/results.md](../reports/course-project/timed-d/results.md), literature
is [timed-d-literature.md](research/timed-d-literature.md). Review branch
`codex/timed-research-d-v1` includes the earlier C appendix and this extension;
`main` remains at59fb784.

These are known statistical tools adapted to a reproducible course system, not
a new inference theorem, clinical system or independent test replication. Three
validation sources and repeated test inspection limit generalization. The next
stronger scientific step is a genuinely unseen source evaluation with this
recipe frozen, rather than another grid on the same test set.
