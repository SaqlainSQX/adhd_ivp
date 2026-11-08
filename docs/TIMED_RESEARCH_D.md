# Timed research round D — registered 8 November 2026

Exploratory follow-up after inspecting main, A, B and C test outcomes. Start
05:24 UTC; 30-minute checkpoint about 05:55 UTC. No additional GPU inference,
new backbone, test-driven search or replacement of the locked main comparison.
Keep every candidate, tie and loss. Stop launching work at the checkpoint.

## Research rationale

[Angelopoulos, Duchi and Zrnic, PPI++ (2024), sections 2.2 and 6](https://arxiv.org/html/2311.01453v2)
introduce a weight on prediction correction. We test a development-selected
finite-population control-variate adaptation, not an exact replication of their
iid setup, not a novel estimator, and not their asymptotic efficiency guarantee.
For any weight fixed before test labels, use
`lambda*mean(q) + sum_h (N_h/M)*mean_sample(y-lambda*q)`.
Its design expectation is the finite-population label mean. The usual stratified
FPC variance uses sampled residuals `y-lambda*q`; normal coverage is empirical,
not guaranteed by tuning. lambda=0 is stratified human-only estimation.

Score quantile strata are a simple model-assisted control. More strata can
reduce within-stratum variance but spend more minimum allocations. Rather than
claiming novelty, test this engineering tradeoff with a fixed candidate grid.

## Registered queue and endpoints

D1: select lambda from {0, .25, .5, .75, 1} separately for uniform sampling and
the existing q-quartile policy. Keep the q-quartile cuts, residual SDs and alpha
frozen from B1. All lambda candidates use identical saved validation queries.
Select by validation MSE at 10% with 1,000 draws; within 1% of minimum prefer
larger lambda (retain the original if tied). Lock before new test outcomes.

D2: train-score quantile strata K={2,4,8,16}; deduplicate equal cuts and omit
the maximum cut. Use all training labels for centered signed residual moments,
the existing prior20/floor1e-6, and lambda=1. Select alpha from {0,.5,1} for
each K, within 1% prefer smaller alpha. Select one K on validation only, within
1% prefer smaller K then smaller alpha. Report every K on test; do not choose
a different winner using test. D1 and D2 are separate, never combine after test.

Reuse train191956/validation25139/test10316 eligible pair-frames and original
feature tables. Test budgets516/1032/2063/4126; 1,000 draws per method/budget.
Validation seed start100000, test200000, SeedSequence([start+draw, budget_index,
stream]); primary budget index1. Uniform stream1; all score policies stream21.
Common stream means aligned random seeds, not identical queries across designs.
D1 score and D2 K4 use identical test queries if alpha matches. All validation
plans precede validation labels; all test plans precede test labels.

Primary endpoint: RMSE in percentage points at B1032. D1 score and the
validation-selected D2 policy compare with D2 K4 (same new stream); D1 uniform
also compares with original M2 (same stream1). Practical improvement threshold:
at least10% RMSE reduction and draw-bootstrap ratio upper95% endpoint<1.
Bootstrap2,000 seed400004, fixed-corpus Monte Carlo uncertainty only. This
threshold is descriptive after prior test inspection, not confirmatory evidence.
Secondary: bias, MAE, all budgets, normal/bounded and exact binary reference
coverage/width, zero variance, failures. Binary reference ignores q, sums integer
total endpoints, and need not contain the residual point estimate.

Freeze config/protocol in Git before execution. Save policy locks, query hashes,
all per-draw outputs, independent RNG/point/variance/interval/summary checks,
runtime and original hashes. Use a new output version after any failure. No
raw queries, labels, models or credentials in Git. No extra grid after outcomes.
