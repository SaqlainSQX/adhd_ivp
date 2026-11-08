# T: uncertainty in empirical interval coverage

Registered after the S reporting build and before T calculations. This is a
bounded reliability analysis of existing results, not a new prediction method,
fresh held-out confirmation or a rerun of scientific experiments.

The question is whether reported normal-interval coverage departures can be
explained by Monte Carlo uncertainty from a finite number of audit draws.
Use exactly these saved aggregate rows, all with1000 draws per row:

- Main: normal coverage of M1-M5 at budgets516/1032/2063/4126 (20 cells).
- UCO L: normal coverage of uniform, K4 and power-score at260/521/1043/2087
  (12 cells).
- Q: normal clean-target coverage of all24 dataset/method/rate cells.
- R: normal clean-target coverage of all18 dataset/method/directional cells.

This creates a fixed family of74 cells. Pin the four source-file hashes, exact
selectors, n=1000, alpha=0.05, family size74 and this protocol in a new T config
before calculating endpoints. Reconstruct integer k=round(n*coverage); require
the saved proportion to agree with k/n within1e-12 and reject any missing or
extra cell. Do not choose budgets or cases based on their coverage outcomes.

Primary endpoints: main M3 and M4 coverage at the primary budget1032. Report
their observed coverage plus individual95% and simultaneous-family95% exact
binomial intervals for the coverage probability over random audit draws on
this fixed corpus. Secondary: every one of the74 rows, with the same outputs.
Bonferroni uses alpha/74 per cell for family coverage without assuming cells
are independent. Per-cell intervals use Clopper-Pearson equal tails; k=0 and
k=n use the exact boundary values. Flag an upper endpoint below0.95 as evidence
of undercoverage under that Monte Carlo experiment. An interval containing0.95
does NOT establish reliable nominal coverage. Preserve overcoverage as well.

Use beta quantiles for the primary implementation, independently check the
interior endpoints against binomial tail probabilities and boundary cases
against their elementary expressions. Check all74 integer counts, endpoints,
family allocation, flags and source hashes. Include simple exact boundary and
interior reference cases before reading scientific endpoints; save failures
and version any repair. Create a complete table and, if a new figure is made,
inspect it visually. No new query seeds, model training, labels or GPU work.

These intervals describe repeated-query/noise Monte Carlo coverage for each
already studied population. They are not prevalence intervals, source-domain
generalization intervals, annotation-noise estimates or corrections to the
original intervals. Shared queries/noise make cells dependent; the Bonferroni
family statement remains conservative under dependence. Q/R's corrupted-label
target limitations remain unchanged. Do not tune or replace any locked policy.
