# Registered course-project follow-ups

Registered 7 November 2026, after the main comparison completed and before these
follow-up experiments were run. These two interpretation checks were already
recommended in COURSE_PROJECT_PLAN.md, E05. They are exploratory ablations and
cannot replace the locked main result or provide independent confirmation.

## Prerequisite and current evidence

The main run is `outputs/experiments/course-20261107-v1`. Its 20,000 sampled
method evaluations have completed, and `independent-validation.json` records a
passed independent replay of every query stream and recomputation of every
estimate, finite-population variance and RMSE summary. Figures and the query
timeline still require visual inspection before E06 is marked complete.

Preserve the main policies, query plans, results and all losses or ties. The
selected main static policy is alpha 1; the selected temporal policy is window 11,
alpha 1. Both use the same frozen temporal MTGS predictor. No backbone retraining
or additional image inference is needed for the following checks.

## A1: window 5 versus window 11

For each existing window-specific error model, choose alpha from {0, 0.5, 1} using
only its saved validation candidate MSEs in the main policy lock. Apply the same
1% relative-MSE tie rule, selecting smaller alpha within that window. Do not use
test outcomes to choose a window or alpha. Save this two-window lock before
revealing follow-up test queries.

Use the same verified population, reference version, predictions, original
source folds and error-model settings as the main run. Evaluate at B=1,032
(10% of 10,316 eligible test labels), with 1,000 draws. Use
SeedSequence([200000+draw,1,4]), exact bounded allocation and the same estimator
and intervals. The selected window's result should reproduce its corresponding
main M4 draws; this reuse is a reproducibility check, not a new independent run.

Report both RMSEs, their paired-draw bootstrap ratio (2,000 resamples, seed 400001),
bias, interval coverage and width, exact budgets, sparse/zero-variance rates and
validation-selected alphas. Neither window may replace the main winner afterward.

## A2: neighborhood summaries without ordered transitions

Keep the main selected window, 11. Remove exactly these columns before fitting:

```text
f_t_q_adjacent_change_mean
f_t_q_previous_difference
f_t_q_next_difference
f_t_previous_context_missing
f_t_next_context_missing
f_t_head_a_area_change_mean
f_t_head_b_area_change_mean
f_t_pair_center_distance_change_mean
```

Retain all static features, neighborhood q mean/SD/min/max, available context
count, and directional-imbalance mean/SD. This checks the added value of these
ordered transition and boundary features relative to neighborhood summaries;
it does not isolate every possible definition of temporal order.

Refit signed-residual RandomForestRegressor with 64 trees, maximum depth 4,
minimum leaf size 100 and seed 42. Use the existing five training-source folds,
OOF quartiles and centered residual SD shrinkage. Choose alpha from {0,0.5,1} on
validation only using 100 draws at 10%, the existing seed derivation and 1% tie
rule. Freeze the resulting policy, feature list, cuts, SDs and selected alpha.

Then evaluate 1,000 test draws at B=1,032 with the same seed scheme as A1/main M4.
Compare with the already locked full-feature temporal method and static method.
Report the same metrics and paired-draw Monte Carlo uncertainty. A tie or loss
is retained; do not add features, windows, learners or model variants to rescue it.

## Execution and monitoring

Active chat follow-up: `continue-eye-contact-course-experiments`, every 20 minutes.
On completion/failure, read actual files and logs, update the tracker, and advance
to the next prerequisite-satisfied stage without duplicating jobs. Use new output
folders, save configurations and hashes, preserve raw data and credentials outside
Git, and sync only code/docs/aggregate evidence to the team repository.

Next order: main figure/replay QA and results assessment; A1; A2; final course
interpretation/report update. Keep updates quiet while progress is unchanged.
Disable the check after this evidence package and both follow-ups are complete.
