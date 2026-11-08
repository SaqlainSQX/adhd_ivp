# Source sensitivity E: complete

Completed8 November2026 after the user asked to continue. Protocol committed in
d7a51f8, implementation2e69077, before these diagnostic outcomes. No new queries,
training, allocation selection or GPU/Kaggle work. D1's lambda0.5 stays frozen.
Original main, C and D evidence remains unchanged.

At B1032, all10 leave-one-source-out domains have lower point-estimate RMSE;
8/10 show at least10% reduction. Mean ratio0.8923, worst0.9876, best0.8560.
These are overlapping domains under the original query design, not ten
independent validations or nine-source equal-budget experiments.

The improvement is heterogeneous. Only3/6 positive-reference source domains
improve; S01,S07,S08 lose. Four sources with zero positives have a mechanical
0.5 error ratio when the fixed weight is halved. Omitting S05 nearly eliminates
the aggregate gain: ratio0.9876 [0.9603,1.0162]. The largest source S07 gets
worse individually (ratio1.3534), although the full aggregate improves. Keep
these outcomes in the presentation; do not call weighting uniformly better.

All168,000 domain-method-draw estimates (2methods ×4budgets ×21domains ×1000)
passed independent inverse-inclusion point and algebraic variance recomputation
inside the runner. Every source sum/complement matches saved D whole-population
estimates. Query arrays/hashes and RNG were replayed. Saved CSV summaries,
domain/complement identities and all84 bootstrap comparisons passed separate
report checks. The exhaustive synthetic test verifies design unbiasedness and
both exact and estimated FPC variances.50 tests pass; Ruff passes. The source
figure was visually inspected; all aliases and intervals are readable.

Source-domain normal coverage can be poor, especially with zero or very few
reference positives. The full report retains coverage, label counts, zero-query
rates, zero-variance rates and exact design RMSE at every budget. No exact
domain reference interval or clinical/generalization guarantee is claimed.

## Files and reproduction

Raw ignored root:`outputs/experiments/source-stress-e-20261108-v1`.
Tracked aggregate evidence:`docs/research/source-e-*`.
Report:[source-e/results.md](../reports/course-project/source-e/results.md).
Review branch:`codex/source-stress-e-v1`; main remains59fb784.

```powershell
.venv/Scripts/python.exe scripts/run_source_stress.py *> outputs/source-e-run-v1.log
.venv-mtgs/Scripts/python.exe scripts/report_source_stress.py *> outputs/source-e-report-v2.log
.venv/Scripts/python.exe -m pytest -q --basetemp outputs/pytest-source-e-v1
.venv/Scripts/ruff.exe check src scripts tests
```

The raw runner refuses existing output roots. Reproduce under a new versioned
config/output; the current runner entry point uses the registered config path.
The report-only first pass saved basic round-trip checks; v2 adds bootstrap
checks and the explicit positive-source qualification. Both verification files
and logs are retained. No numerical failure or policy repair occurred.

This analysis strengthens the explanation and limitations of the course result.
It does not increase the number of independent videos or remove repeated-test
development bias. A frozen evaluation on genuinely unseen sources is the next
stronger scientific step, not more selection on this corpus. No additional
experiment is queued at the timer checkpoint.
