# Registered X01 pilot G: uniform contiguous blocks

8 November2026, after F, before this pilot's outcomes. This is the first part of
X01, not the full static-versus-temporal block comparison. G2 remains queued
after this estimator/cost gate; a G1 loss does not authorize changing G1.

Use the same eligible population, cached q and all source boundaries. Public
geometry only: sort by source, clip, unordered person pair and original clip
frame index; split runs on changed keys or any index gap; partition each run
into nonoverlapping prefixes of requested lengthL={1,2,5,10}, retaining shorter
terminal blocks. Never bridge unknown/unavailable anchors. Verify every eligible
frame appears exactly once. Block length is in original frame indices, not an
annotation duration. Keep original public row positions; sort completed blocks
by minimum original position so L1 is identical to original frame indexing.

First save a label-free block inventory on train/validation/test: block counts,
length histograms, partial-block rates, eligible-frame totals and average size.
Then evaluate uniform block SRS at expected unique-frame label budgets
516/1032/2063/4126 on test. If K blocks cover M frames, targett=B*K/M blocks.
Draw n=floor(t)+Bernoulli(t-floor(t)), then uniform n blocks without replacement.
Require floor(t)>=2 unless census. Counts are selected independently of labels.
Conditional inclusion is n/K. Estimate mean(q_lambda) + K/(M*n)sum_sample
(Y_block-lambda*Q_block). Conditional FPC variance is
(K/M)^2*(1-n/K)*sample_var(block residual totals)/n. Conditional unbiasedness
holds for every allowed n, so averaging conditional variance over rounding gives
the unconditional design variance. Do not replace n with its expectation in the
estimator. Expected cost is t*M/K=B; realized unique-label cost varies. Never
truncate queries to a hard cap.

Two fixed prediction weights, lambda1 and lambda0.5 (the latter transferred
unchanged from D uniform validation selection), use identical block queries.
No new parameter selection. Primary endpoint: lambda1 L5/L1 RMSE ratio at
B1032. Secondary: all lengths/weights/budgets, mean/bias/MAE, realized label-cost
quantiles and excess-budget rate, queried-block counts, normal coverage/width,
zero variance, and exact design variance from evaluation-only full references.
Report ratios, losses and all costs. No promised positive threshold. No exact
binary confidence claim for nonbinary block totals and no measured human-time
or clinical claim. Context viewing overhead is not counted as an extra label.

Each design uses1,000 draws, SeedSequence([200000+draw,budget_index,stream]);
L1 stream1 and skip the count RNG draw when target is integer, reproducing
original M2 queries/estimates at lambda1. L>1 stream41+L, independent count
rounding only when target is noninteger. All plans saved before this stage reads
test references. Bootstrap2,000 seed400007 for fixed-corpus RMSE-ratio simulation
uncertainty; streams differ across L, common queries across weights. These are
exploratory outcomes on a repeatedly inspected corpus.

Validate partition/gap/pair boundaries and exact frame-label costs. Exhaustively
check unbiasedness/variance for unequal-cost synthetic blocks at randomized
counts; verify L1 reproduces M2 and independently recompute points/variances
from frame-level residual sums for every run. Check saved outputs, report
figures visually and preserve failed versioned attempts. Reuse CPU caches only.

Cluster sampling trades collection convenience against correlation and precision;
see [Statistics Canada, probability sampling](https://www150.statcan.gc.ca/n1/edu/power-pouvoir/ch13/prob/5214899-eng.htm).
We measure statistical label cost and query-task count, not actual collection time.

G2 will compare uniform, block-q strata, static and temporal score aggregates.
Reuse frozen main per-frame signed-error OOF scores for training-block cuts and
frozen fitted scores for validation/test; sum frame scores within blocks. Learn
centered block residual SDs on train only; choose alpha on validation only.
Register exact G2 config/seeds/endpoints before opening its outcomes. No new
backbone/risk learner or post-test choice of a favorable length is authorized by G1.
