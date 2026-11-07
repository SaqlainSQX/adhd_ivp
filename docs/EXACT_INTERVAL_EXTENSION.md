# Registered exact binary-reference interval extension (B2b)

Registered on 7 November 2026 after B1/B2 outcomes and before computing this
interval's outcomes. Motivation: the newly evaluated score-quartile control's
normal 95% coverage fell to 45.9% at the 40% budget. This exploratory follow-up
preserves that failure, all original point estimates and every existing result.
It adds an established finite-population reference interval, not a new sampler
or a statistical-novelty claim.

## Fixed construction

For each fixed stratum h, use only its queried binary successes k_h, sample
size n_h and public population size N_h. Invert the hypergeometric distribution
with the existing `hypergeometric_interval` function. Census strata contribute
their exactly observed prevalence with zero width. If L strata are not censused,
use alpha_h=0.05/L in each of those intervals. Add weighted lower and upper
endpoints with weights N_h/M. If L=0, return exact census prevalence.

By the union bound, coverage of every stratum interval implies coverage of the
weighted population prevalence. Under the recorded SRS-without-replacement
design and fixed binary benchmark population, the resulting simultaneous
reference interval has at least nominal 95% design coverage, assuming the
individual exact inversions are correctly implemented. It can be conservative.
This does not guarantee correctness of human labels, data alignment or transfer.

This interval uses binary labels directly, ignores q, and is generally centered
differently from the retained residual-corrected point estimate. Report it as an
**exact stratified binary reference interval**, not an exact residual interval.
Report the frequency with which the original point estimate lies outside it.
Do not clip or replace the original point estimate to manufacture compatibility.

## Evaluation registered before this interval's results

Use all existing 1,000 saved draws at B=516,1032,2063,4126 for main M3/M4 and
new q-quartiles/entropy-quartiles: 16,000 existing method/draw/budget cases.
No new queries, labels, development tuning, GPU inference or policy changes.
Validate query-file hashes before accessing sampled binary labels. Retain
original normal and bounded intervals alongside this added reference.

Primary endpoints at B=1,032: coverage and mean width for all four methods.
Secondary endpoints: all budgets, mean/median width, Monte Carlo SE, original
point-outside-reference-interval rate, and exact budget checks. Show all outcomes,
including over-wide intervals. Check exact coverage exhaustively on small
two-stratum finite populations, census and zero-success cases before running.
Independently check the saved interval endpoints against a fresh inversion and
recompute aggregate coverage/width from saved per-draw endpoints.

Results go to a new `B2b-exact-reference` directory under the strengthening root.
Update the report with this extension's post-outcome registration timing and
limitations. It must not be described as an independently confirmed new method.
