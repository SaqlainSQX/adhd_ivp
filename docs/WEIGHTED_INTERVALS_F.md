# Registered public-weight exact intervals F

8 November2026, after main/B/C/D/E outcomes. Exploratory fixed-query extension;
no new data/model/point estimate, sampler or test-selected policy. Main exact
equal-error intervals and failing normal intervals stay unchanged.

Question: can conservative fixed-population reference intervals be narrower
using a public, unequal error budget? Weighted Bonferroni is established; see
[Roeder and Wasserman, Weighted Hypothesis Testing](https://www.stat.cmu.edu/tr/tr830/tr830.pdf).
Our construction uses exact hypergeometric stratum intervals and the union
bound. For noncensus strata choose positive fixed weights summing1, alpha_h=.05w_h.
Each marginal interval misses its fixed stratum total with probability at most
alpha_h. Therefore simultaneous coverage is at least.95 and summing integer
total endpoints covers the population total whenever all strata cover. No
independence assumption is needed. Census strata use their known sampled totals
and consume zero error budget. This claim is conditional on fixed population,
valid SRS within frozen strata and fixed counts; it is not a clinical guarantee.

Predeclare three recipes, normalize on noncensus strata only:

- equal: raw weight1, reproducing the accepted reference.
- inverse-fraction (primary): raw N_h/n_h. For rare positives/zero-success
  bounds the leading weighted width is approximately proportional to
  (N_h/n_h)log(1/alpha_h), motivating this public allocation. This heuristic is
  not claimed optimal for the exact discrete interval.
- inverse-sqrt-count (secondary): raw N_h/sqrt(n_h), a separate public recipe.

Use existing1,000 saved draws at budgets516/1032/2063/4126 for main M3/M4,
D K4/power-score (identical query sets; report one interval per design and both
point-outside rates) and D power-uniform. No new query streams or labels.
Primary endpoint: inverse-fraction/equal mean-width ratio for score K4 atB1032;
practical descriptive gain threshold<=.9. Report empirical coverage, width
quantiles, integer endpoints, missed-total counts and point-outside rates for
all designs/recipes/budgets. Report every loss and no winner selection.

Save all public error allocations before opening references for this stage.
Check equal endpoints against saved accepted references, check census and
single-stratum cases, enumerate every possible binary population total on a
small two-stratum design to verify coverage>=.95 for every recipe, and verify
all accepted exact endpoint tails and adjacent integer boundaries. Recompute
saved integer-grid coverage/width summaries and bootstrap primary paired width
ratio with2,000 draws seed400006. Monte Carlo uncertainty is on this fixed corpus,
not new-source uncertainty. No intersection of multiple95% intervals or
after-the-fact choice of a favorable recipe is reported as a95% interval.

Raw outputs must be new/versioned, with original evidence preserved on failure.
Track config/protocol/code/query hashes, logs, gate outcomes, runtimes and all
aggregates; inspect figures visually before marking complete. Reuse CPU caches,
never print or commit credentials/raw queries/labels/model weights.
