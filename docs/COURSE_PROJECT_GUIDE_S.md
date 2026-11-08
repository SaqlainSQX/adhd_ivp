# Budgeted estimation of mutual-looking prevalence with frozen gaze predictions

Course project guide through stage R. This is an additive synthesis; the original
[course report](../reports/course-project/course-report.md) and every registered
result remain unchanged. Numeric claims are resolved from the accepted aggregate
JSON files in [the claim map](research/s-claim-map.json); hidden claim markers
allow the checker to verify the displayed values against their exact selectors.

## Contribution to present

We built and audited a reproducible system for estimating benchmark-defined
mutual-looking prevalence using a frozen vision model and a limited random
sample of reference labels. The project combines score-guided stratified
sampling, a model-assisted difference estimator, uncertainty diagnostics,
replayable query plans and an aggregate demonstration. A fixed prediction-weight
extension improves the ChildPlay comparison but reverses on UCO; analytical
variance and synthetic label-error studies explain important limits. The
contribution is the working system and careful empirical analysis. It does not
depend on claiming a new statistical theorem, uniform benchmark superiority or
an ADHD diagnostic capability.

## What the system measures

The unit is an eligible person-pair at an annotated frame. Its binary reference
indicates benchmark-defined mutual looking. The estimand is the mean of those
binary references over the frozen eligible population. It is not the percentage
of people with ADHD, a clinical attention score, duration over all video time or
the prevalence among unavailable videos.

ChildPlay contains 10316<!-- s:child_n --> eligible test pair-frames from 10<!-- s:child_sources -->
test sources. Across the media acquisition, 53<!-- s:retained --> of 95<!-- s:attempted -->
attempted original sources were retained. The test reference mean is 3.5188<!-- s:truth -->%,
whereas the uncorrected frozen model mean is 7.1412<!-- s:model_mean -->%: bias 3.6224<!-- s:model_bias -->
percentage points. These populations reflect availability and eligibility rules.

The UCO evaluation contains 5219<!-- s:uco_n --> eligible pair-frames with reference mean
27.3807<!-- s:uco_truth -->%. Its eligibility, person/frame mapping and context preparation are
documented in [the transfer results](UCO_TRANSFER_L_RESULTS.md) and
[the geometry review](UCO_VISUAL_K3_STATUS.md). This is a transfer evaluation
with a frozen recipe, subject to shared backbone/pretraining-family and crop
adapter limitations; it is not proof of wholly independent pretraining or a
natural-video population estimate.

## Method pipeline and assumptions

1. Freeze the data population, source splits, eligibility rules, model checkpoint
   and inference cache. Exclude unknown references under the documented rules.
2. Compute a fixed per-pair score q using the released gaze model. Error-guidance
   models use training-source fitting/cross-fitting; policy selection uses
   validation sources. Static and temporal variants differ in guidance features.
3. Freeze strata, allocation, label budgets, seeds and comparison endpoints.
   Save random query plans before opening evaluation references. Sample without
   replacement within each stratum, with the registered minimum allocations.
4. Reveal the sampled benchmark references. For fixed prediction phi=lambda*q,
   estimate the population mean with
   `mean(phi) + sum_h (Nh/N) * mean_sample_h(y-phi)`.
5. Estimate design variance with the stratum residual sample variances and
   finite-population corrections. Keep approximate normal intervals separate
   from conservative bounded/binary-reference intervals. Exact binary intervals
   need not be centered on, or contain, the model-assisted point estimate.
6. Compare bias, RMSE, interval coverage/width and label cost across repeated
   saved query draws. Independently replay the RNG, estimates and intervals.

Unbiasedness of the difference estimator relies on its random query design and
accurate observed references for the target population; it does not require q
to be perfectly calibrated. Prediction quality affects variance. Lambda and
allocation must be frozen before evaluation labels are used for that comparison.
Later explanations of already inspected test labels are explicitly exploratory.
Full fitting and validation labels are additional costs: an audit budget is not
the total cold-start annotation cost. No measured human annotation-time savings
are claimed.

## Original main comparison: retain the non-win

At the primary budget, static M3 RMSE is 0.2603<!-- s:main_static --> pp and temporal M4 RMSE
is 0.2765<!-- s:main_temporal --> pp. Temporal/static ratio is 1.0623<!-- s:main_ratio -->, with fixed-corpus
draw-bootstrap interval [0.9889, 1.1421]<!-- s:main_ci -->. This does not establish a temporal gain.
There are 1000<!-- s:draws --> query draws per method/budget and 20000<!-- s:main_checks --> sampled
main cases. The full main table, all budgets and original interval failures remain
in [the original report](../reports/course-project/course-report.md).

These intervals describe Monte Carlo uncertainty over random audits on a fixed
population. They do not quantify uncertainty over future source domains. The
bootstrap interval for an RMSE ratio is also different from the confidence
interval produced by an individual audit for prevalence.

## Prediction weighting: local gain and transfer reversal

The fixed half-weight extension uses the same K4 queries as full weight. On
ChildPlay at 1032<!-- s:child_budget --> labels, half/full RMSE ratio is 0.8947<!-- s:child_ratio -->,
with paired draw-bootstrap interval [0.8712, 0.9190]<!-- s:child_ci -->. It is an exploratory gain
after repeated inspection of the same corpus, rather than fresh confirmation.

ChildPlay D: RMSE in percentage points. These rows preserve the full registered
budget curve for this comparison; they do not substitute the original main study.

| Labels | Full K4 | Half K4 |
|---:|---:|---:|
| 516<!-- s:child_budget_516 --> | 0.3338<!-- s:child_K4_516 --> | 0.3015<!-- s:child_power-score_516 --> |
| 1032<!-- s:child_budget_1032 --> | 0.2199<!-- s:child_K4_1032 --> | 0.1967<!-- s:child_power-score_1032 --> |
| 2063<!-- s:child_budget_2063 --> | 0.0969<!-- s:child_K4_2063 --> | 0.0863<!-- s:child_power-score_2063 --> |
| 4126<!-- s:child_budget_4126 --> | 0.0124<!-- s:child_K4_4126 --> | 0.0122<!-- s:child_power-score_4126 --> |

The UCO primary half/full ratio is 1.2695<!-- s:uco_half_ratio -->, interval [1.2202, 1.3193]<!-- s:uco_half_ci -->:
the half-weight extension loses. Conversely, full K4 versus uniform+q has ratio
0.7441<!-- s:uco_guided_ratio -->, interval [0.7010, 0.7923]<!-- s:uco_guided_ci -->. Both findings must be reported.
The full/half comparison shares queries; the full/uniform comparison has equal
label budgets but different sampling designs and query streams.

UCO L: RMSE in percentage points. Every evaluated budget and method is shown.

| Labels | Uniform + q | Full K4 | Half K4 |
|---:|---:|---:|---:|
| 260<!-- s:uco_budget_260 --> | 1.1634<!-- s:uco_uniform_260 --> | 0.9473<!-- s:uco_K4_260 --> | 1.2802<!-- s:uco_power-score_260 --> |
| 521<!-- s:uco_budget_521 --> | 0.7960<!-- s:uco_uniform_521 --> | 0.5923<!-- s:uco_K4_521 --> | 0.7519<!-- s:uco_power-score_521 --> |
| 1043<!-- s:uco_budget_1043 --> | 0.5545<!-- s:uco_uniform_1043 --> | 0.3629<!-- s:uco_K4_1043 --> | 0.4858<!-- s:uco_power-score_1043 --> |
| 2087<!-- s:uco_budget_2087 --> | 0.3393<!-- s:uco_uniform_2087 --> | 0.1763<!-- s:uco_K4_2087 --> | 0.2291<!-- s:uco_power-score_2087 --> |

At UCO's primary full-K4 budget, normal coverage is 95.1<!-- s:uco_normal_coverage -->%
with mean width 2.3687<!-- s:uco_normal_width --> pp; conservative binary-reference coverage
is 99.4<!-- s:uco_binary_coverage -->% with width 16.0359<!-- s:uco_binary_width --> pp. High coverage
with broad intervals is a precision tradeoff, not evidence that every interval
construction is equally useful.

## Why the weighting effect can reverse

For a fixed stratified design and fixed phi=lambda*q, design variance has form
`V(lambda)=A-2*lambda*B+lambda^2*C`. Hence
`V(0.5)-V(1)=B-0.75*C`. In the post-hoc M explanation this difference is
-9.772775e-07<!-- s:m_child_delta --> proportion-squared on ChildPlay and 2.557665e-05<!-- s:m_uco_delta --> on UCO.
The corresponding exact design-RMSE ratios are 0.8891<!-- s:m_child_ratio --> and
1.3038<!-- s:m_uco_ratio -->. These are analytical finite-population quantities; the empirical
Monte Carlo ratios above need not match them exactly.

This explains the two fixed choices. It is not a newly selected optimal weight,
an independent test, or a justification for optimizing lambda on these labels.
See [the complete M explanation](VARIANCE_EXPLANATION_M_RESULTS.md).

## Robustness results that qualify the gain

Source sensitivity E: only 3<!-- s:source_improved --> of 6<!-- s:source_positive --> sources
with positive references improve. Although 10<!-- s:loo_improved --> of 10<!-- s:loo_total -->
overlapping leave-one-source-out aggregates improve, the worst ratio is
0.9876<!-- s:loo_worst -->. This shows influence and heterogeneity, not unseen-source
cross-validation. See [source sensitivity](../reports/course-project/source-e/results.md).

Interval weighting F: the primary width ratio is 0.9741<!-- s:f_width_ratio -->. For the
registered full-K4 primary comparison, equal versus inverse-fraction mean widths
are 8.6978<!-- s:f_equal_width --> and 8.4725<!-- s:f_weighted_width --> pp. The improvement is small and
the intervals remain broad. See [all F results](../reports/course-project/weighted-f/results.md).

Uniform contiguous-block pilot G: the primary longer-block/frame RMSE ratio is
2.1089<!-- s:g1_ratio -->, interval [1.9782, 2.2382]<!-- s:g1_ci -->, at matched expected label cost. Guided-block
follow-up G2: temporal/static ratio is 1.1139<!-- s:g2_ratio -->, interval [1.0389, 1.2034]<!-- s:g2_ci -->, again a
loss. Actual realized block label costs vary, can exceed their nominal expected
budget and must not be presented as exactly matched realized costs. See
[G](../reports/course-project/block-g/results.md) and
[G2](../reports/course-project/block-guidance-g2/results.md).

## Label quality: synthetic sensitivity, not annotator accuracy

Q applies a fixed symmetric flip probability of 0.0200<!-- s:q_rate -->. At that setting full-K4
ChildPlay bias is 1.7807<!-- s:q_child_bias_pp --> pp, RMSE 1.9959<!-- s:q_child_rmse_pp --> pp and normal
clean-target coverage 33.9<!-- s:q_child_normal_coverage -->%. UCO values are
0.9788<!-- s:q_uco_bias_pp --> pp, 1.5334<!-- s:q_uco_rmse_pp --> pp and 93.6<!-- s:q_uco_normal_coverage -->%.
All 24000<!-- s:q_checks --> cases passed independent replay.

R separates class-conditional error probabilities 0.0200<!-- s:r_fp_rate --> and 0.0200<!-- s:r_fn_rate -->
into false-positive and false-negative mechanisms, respectively. Full-K4 results are:

| Dataset | Error direction | Bias pp | RMSE pp | Normal clean-target coverage % |
|---|---|---:|---:|---:|
| ChildPlay | False positive | 1.9382<!-- s:r_child_fp_bias_pp --> | 2.1562<!-- s:r_child_fp_rmse_pp --> | 26.4<!-- s:r_child_fp_normal_coverage --> |
| ChildPlay | False negative | -0.0689<!-- s:r_child_fn_bias_pp --> | 0.2316<!-- s:r_child_fn_rmse_pp --> | 92.9<!-- s:r_child_fn_normal_coverage --> |
| UCO | False positive | 1.4248<!-- s:r_uco_fp_bias_pp --> | 1.7985<!-- s:r_uco_fp_rmse_pp --> | 80.5<!-- s:r_uco_fp_normal_coverage --> |
| UCO | False negative | -0.5363<!-- s:r_uco_fn_bias_pp --> | 0.8272<!-- s:r_uco_fn_rmse_pp --> | 88.5<!-- s:r_uco_fn_normal_coverage --> |

All 18000<!-- s:r_checks --> cases passed independent replay. The directional settings do
not have equal overall corruption counts: rates condition on different reference
classes. Rare positives make false-positive errors particularly consequential.
These synthetic independent errors do not estimate human accuracy, correlated
mistakes or clinical reliability. Benchmark labels are treated as clean only for
the simulation. Naive binary intervals target corrupted references and have no
guaranteed coverage for the clean target under these errors. No known-noise
correction or validated annotation-quality policy is claimed. Preserve all cells
in [Q](QUERY_NOISE_Q_RESULTS.md) and [R](DIRECTIONAL_NOISE_R_RESULTS.md).

## Recommended report structure

- Problem and target: estimate eligible pair-frame mutual-looking prevalence
  under an audit-label budget; define the finite population and exclusions.
- Related work and ingredients: frozen gaze prediction, stratified random
  sampling, model-assisted estimation, temporal guidance and uncertainty.
  Use the original project bibliography; do not describe established ingredients
  as invented here.
- System and methodology: frozen inputs, training/validation/test separation,
  policy lock, audit design, estimator, interval assumptions and replay evidence.
- Main results and controls: show the temporal non-win before exploratory gains.
- Extensions: same-query weighting, source sensitivity, interval/block tradeoffs,
  UCO reversal, post-hoc variance explanation and synthetic label-error checks.
- Demonstration, reproducibility, limitations and future work. Genuine future
  source data and measured annotation reliability would add stronger evidence
  than further optimization on repeatedly inspected test labels.

## Demonstration and team reproduction

Use the checked-out additive review branch containing this guide. The locked
main branch remains a historical baseline; it has not been silently replaced.
The original explorer is http://127.0.0.1:8766 and the aggregate transfer appendix
is http://127.0.0.1:8768. Reuse an existing service rather than starting a duplicate.

From the repository root, the preferred aggregate rebuild is:

```powershell
python -I -S scripts/build_verified_transfer_appendix.py
```

If the appendix server is absent:

```powershell
python -I -S scripts/serve_transfer_appendix.py --port 8768
```

This rebuilds only accepted aggregate presentation data. It needs neither raw
videos nor model weights. The original N/O builder and evidence remain preserved;
P adds explicit checksum exceptions that remain active under optimized Python.
The O/P checks used staged copies on this PC; they do not establish a fresh
installation or cross-platform reproduction. Full inference and scientific replay
require the separately obtained data, prediction cache and pinned environments.
See [the verified builder addendum](TEAM_VERIFIED_BUILD_P.md),
[team quickstart](TEAM_QUICKSTART.md), [run instructions](RUN_EXPERIMENTS.md)
and [appendix walkthrough](TRANSFER_APPENDIX_N_GUIDE.md).

The browser's physical in-app download-capture helper timed out. Its JSON endpoint
and payload were checked; this limitation remains disclosed. Do not repeat the
hanging helper to make a demonstration appear complete.

## Likely viva questions

**What is novel enough for a course?** The implemented, reproducible audit
system, controlled evaluation and diagnostic extensions are the contribution.
We do not claim to invent stratified sampling or a generic difference estimator.

**Why use the model if reference labels are needed?** Scores guide allocation
and act as control variates. Good residual structure can lower audit variance,
while random reference corrections address aggregate prediction bias.

**Did temporal features help?** The primary comparison does not show a temporal
gain. We retain it and investigate simpler controls rather than hiding the loss.

**Does half-weighting generalize?** It improves the ChildPlay same-query
comparison but loses on UCO. The frozen-design variance decomposition explains
why a universal improvement is not expected.

**Does a small label budget mean cheap end-to-end training?** No. Training and
validation reference use and pretrained-model costs remain additional costs.
No timed human annotation study was performed.

**Are exact intervals always better?** Their clean-reference design guarantees
depend on the sampling/label assumptions and can be conservative. Broad intervals
may cover while being uninformative; noisy observations change the target.

**Why not diagnose ADHD?** The dataset target and experiments concern
benchmark-defined mutual looking. No clinical labels, diagnostic validation or
causal evidence establish an ADHD test.

**What cannot be recovered from these results?** Human annotator sensitivity,
specificity, disagreement, effort savings, causal clinical relationships,
missing-source prevalence and future-domain performance. These require new data
or appropriately designed studies, not guesses from the aggregate outputs.
