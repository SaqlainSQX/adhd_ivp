# Registered G2: frozen-score block guidance

8 November2026. G1/F outcomes already observed; all new G2 results exploratory.
This completes X01's static-versus-temporal question without replacing the main
frame experiment. G1's poor uniform-block result and every G2 loss stay reported.

## Frozen features and training

Use exactly G1's gap-safe partitions and all eligible train191956,
validation25139/test10316 frames. Lengths1,2,5,10, no test-selected length.
No new model/backbone fit. All estimates use lambda1; do not select the better
weight0.5 after G1. Required Q/S/T policies:

- Q: score is block sum of frozen native q.
- S: score is block sum of main static signed-residual predictions.
- T: score is block sum of main temporal-window11 signed-residual predictions.

For train S/T use saved five-source-fold OOF frame scores, aggregating only
within a source; check row alignment and source/fold manifests/hashes. For
validation/test use the already frozen final fitted main policies and their
original feature sets. Do not use in-sample fitted training predictions for cuts.
For each length/policy, use training-score quartile cuts, deduplicate/remove
trailing max. Estimate centered training block residual-total SDs, shrink
within-bin variance toward global block variance with prior20, floor1e-6.
Public partial-block costs and score sums are allowed; no hidden test labels.

## Sampling and selection

Within each public score stratum h, use K_h blocks, mean unique-frame cost c_h.
Uniform expected counts solve clip(k*K_h, min(K_h,2),K_h) under sum(t_h*c_h)=B.
Neyman cost-aware expected counts use weightsK_h*SD_h/sqrt(c_h), same bounds.
Blend targets `(1-alpha)*uniform + alpha*active`, alpha={0,.5,1}. This reuses the
existing block allocation contract in policy._continuous_counts. Lower2 blocks
is common across all G2 lengths; G2 L1 is not the main exact-budget/min20 method.

Independently round each expected t_h with floor+Bernoulli(fraction), then SRS
n_h blocks within that stratum. Skip a count RNG draw when target is integer.
All counts are label-independent and at least2 unless census. Estimator is
mean_all(q)+sum_h K_h/(M*n_h)*sum_sample_h(Y_block-Q_block). Use realized n_h,
not target t_h. Conditional stratified FPC variance uses block residual totals.
Unconditional exact design variance averages conditional factors over each
floor/ceil lottery. Expected label cost sum(t_h*c_h)=B, realized unique-label
cost variable; never cut queries at a hard cap. Keep every tail and cost overrun.

For each of12 length/policy combinations choose alpha on validation only at
B2514 using100 draws and original1% relative-MSE tie rule preferring smaller
alpha. Save all validation plans before reference access for this stage. Freeze
each winner before saving all test plans and accessing test references. No
selection across lengths, learners, weights or formulas.

RNG SeedSequence([seed_start+draw,budget_index,stream]); validation100000,
test200000, stream=700+100*L+policy_code where Q/S/T codes1/2/3. Reuse common
seed streams across alpha candidates, not identical query arrays when counts
change. Test1,000 draws ×4budgets516/1032/2063/4126 ×4lengths ×3policies=48,000
method evaluations, plus3,600 validation candidate evaluations.

Primary: T/S RMSE ratio atL5/B1032, predeclared descriptive10% gain threshold
ratio<=.9 and fixed-corpus bootstrap upper95%<1. Bootstrap2,000 seed400008.
Secondary: all lengths/budgets, Q/S/T versus same-length G1 uniform/lambda1,
G2 L>1 versus G2 L1, bias/MAE, realized labels and queried blocks, cost quantiles,
normal coverage/width, zero variance, exact design variance and failure rates.
Different Q/S/T streams mean aligned draw indices, not same queried records.
This Monte Carlo range is not unseen-source or multiple-comparison evidence.

Also report a conservative residual-total Hoeffding reference, separately from
normal intervals. In each noncensus stratum use public residual envelope
[-max(Q_block), max(cost_block-Q_block)]. With H_noncensus strata, the bound
radius is sum_h(K_h/M)*range_h*sqrt(log(2*H_noncensus/.05)/(2*n_h)); census radius0.
Intersect its interval with[0,1], retain original point and any empty-interval
event. This is a standard bounded-SRS reference; not an exact binary interval
and not a claim of narrow/useful uncertainty. No test-selected intersection or
choice among reported interval families.

## Gates and continuation

Pin main result/policy/features, model and OOF files and G1 partition hashes.
Check public/train-only boundaries, G1 partition reproduction and source-fold
integrity. Exhaustive synthetic allocation/rounding tests must verify expected
cost and unbiased point/variance for multiple strata and unequal block costs.
Recompute all queries/RNG, points, FPC variances and summaries independently,
check alpha choices and raw saved outputs, inspect figures visually, sync only
code/docs/aggregates. Preserve any failed attempt in a new-version repair.

Current implementation is pending. Read X01_BLOCK_STATUS.md and actual output
state/processes before starting. After accepted G2 results, extend the separate
demo/course presentation per the standing research queue; do not start another
ad-hoc grid solely because temporal guidance fails. No actual human-time benefit
or clinical/new-method claim follows from a simulated query-task count.
