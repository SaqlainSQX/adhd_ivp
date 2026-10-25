# Deep research assessment: is the idea worth pursuing?

Assessment date: 25 October 2026. Evidence: the supplied design, current methodology,
primary literature in the [evidence matrix](evidence-matrix.md), direct inspection
of the public VSGaze release, and reproducible planning calculations. No MTGS
inference, new human annotation, or proposed-method effectiveness experiment was
performed. All recommendations below are judgments drawn from that evidence.

## Verdict

**Conditional go for a focused measurement study and team project. The current
combination is insufficient as a claim of a new general inference method.**

The practical question is worthwhile: unreliable automated social-gaze labels can
distort aggregate measurements, and obtaining reference annotations costs effort.
Frozen predictions plus probability sampling are a sound way to study this.

However, model-assisted estimation, selective oracle queries, video aggregation,
temporal query acceleration, stratification and batching tradeoffs already have
substantial prior work. Applying them to ChildPlay is useful engineering but does
not by itself establish methodological novelty. The original emphasis on block
queries is also at risk: the observed labels are highly redundant within blocks.

The strongest candidate contribution is a reproducible study that isolates the
incremental value of temporal context for **error assessment and label selection**,
with realistic static baselines, valid uncertainty, measured annotation costs and
explicit limits on source transfer. Its research value remains conditional on
comparative results. An implementation cannot validate the claimed gain by itself.

| Dimension | Assessment | Confidence and missing evidence |
| --- | --- | --- |
| Importance of reliable social-gaze measurement | Worthwhile | Supported by gaze/clinical measurement papers; no claim of clinical validation for our pipeline |
| Corrected fixed-corpus prevalence estimation | Statistically sound under the stated randomization | High confidence in the fixed-population argument; practical intervals still need validation |
| New generic estimator/sampling method | Weak in the current proposal | High confidence in substantial prior overlap |
| Added value from temporal risk features | Plausible, unverified | Needs held-out prediction/reference caches and strong static/contextual-calibration controls |
| Benefit from contiguous label blocks | Doubtful at equal label count; possible under measured costs | Annotation-only diagnostics are unfavorable; actual MTGS residuals and human timing remain unknown |
| Available benchmark feasibility | Annotation work is feasible; media/inference remain unverified | Release was read; only six validation sources restrict development |
| Autism/ADHD or eye-specific clinical conclusion | Unsupported by this study | Requires an appropriate clinical population, endpoint and independent validation |
| Strong research-paper contribution | Possible after narrowing and evidence; not established | No defensible acceptance probability follows from the current evidence |

## 1. What the deeper search changes

The initial review focused on MTGS, SACF and the PPI/ASI family. That was too narrow
for the novelty question. Four overlooked database systems directly matter:

- **BlazeIt** estimates video aggregates using inexpensive model predictions as
  control variates and selected expensive evaluations. See §6 of the
  [primary paper](https://people.eecs.berkeley.edu/~matei/papers/2020/vldb_blazeit.pdf).
- **ABae** uses proxy-defined strata, pilot observations and variance-based sample
  allocation; it explicitly includes human labelers among possible oracles. Its
  predicate-conditioned aggregation differs from our simplest mean, but the
  general acquisition pattern overlaps. See §2.3–3.1 of
  [ABae](https://www.vldb.org/pvldb/vol14/p2341-kang.pdf).
- **InQuest** applies proxy-guided stratified querying to unstructured streams and
  includes defensive sampling to prevent catastrophic under-allocation. See
  [InQuest](https://www.vldb.org/pvldb/vol16/p2897-russo.pdf).
- **Seiden** uses temporal continuity and adaptive oracle calls for video queries.
  Its propagation strategy differs from our statistical estimator, but temporal
  sampling in video is not a new research direction by itself. See
  [Seiden](https://www.vldb.org/pvldb/vol16/p2289-kakkar.pdf).

There is also direct application-level overlap. A 2026 clinical study already
automatically measures dyadic social gaze, mutual-gaze proportions and temporal
features during conversations in autism. It distinguishes looking at the partner
from looking specifically into the partner's eyes. This validates the relevance
of measurement while blocking a broad first-automatic-social-gaze claim.
[Yankowitz et al.](https://pubmed.ncbi.nlm.nih.gov/42161147/),
[annotation/features/limitations](https://pmc.ncbi.nlm.nih.gov/articles/PMC13248665/).

The statistical baseline landscape remains demanding: [ASI](https://proceedings.mlr.press/v235/zrnic24a.html),
[StratPPI](https://proceedings.neurips.cc/paper_files/paper/2024/file/c9fcd02e6445c7dfbad6986abee53d0d-Paper-Conference.pdf),
[Robust ASI](https://arxiv.org/html/2511.08991v1), and
[Fixed-Size ASI](https://arxiv.org/html/2610.27389v1) already address central parts
of our acquisition/correction design. The last is a 19 October 2026 preprint and
must be considered in a current assessment. None supplies an automatic finite-sample
guarantee for a new mixture or block adaptation merely by resemblance.

Our search did not identify an identical, fully controlled ChildPlay study of
temporal context versus annotation batching. That is a candidate gap, not a
verified first-in-literature result. Even the general batching-versus-cost question
has precedents outside video, including [Yang et al.](https://arxiv.org/html/2503.00815v1).

## 2. Independent annotation verification

The public [VSGaze release](https://zenodo.org/records/17357752) was downloaded into
the ignored local data folder. The 103,425,122-byte archive matches its published
MD5 `c83980c07b349df3af84981721045d3b`; its SHA-256 is
`3bf42763c968b9684a3276e32b41403a43392282c67bdc8e461058ca949cb386`.

The scan reads the ChildPlay HDF5 tables, removes negative/placeholder IDs and
self-pairs, reconciles reverse pair orientations and rejects conflicting labels.
It reproduces the supplied presentation's counts:

| Split | Frames | Clips | Original source videos | Binary-known pair-frames | Positive | Unknown real-pair records |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Train | 100,209 | 330 | 68 | 285,585 | 6,396 | 129,441 |
| Validation | 10,283 | 26 | 6 | 33,568 | 259 | 11,741 |
| Test | 9,986 | 45 | 21 | 38,847 | 651 | 41,572 |

Source IDs were parsed from the release's clip naming convention; the parsed
source sets do not overlap across splits. This does not independently establish
different subjects/channels, present video availability, correct decoded frame
alignment or a checkpoint's training history. Some training clip names explicitly
indicate downsampling; adapters must preserve the actual frame/time mapping.

The VSGaze ChildPlay tables contain 120,478 frames in total, compared with 120,549
in the original ChildPlay release description. The reason for the 71-frame
difference has not been established here; do not silently mix release denominators.
Binary-known prevalence also differs across splits: 2.2396% train, 0.7716%
validation and 1.6758% test. This describes the benchmark splits and is not evidence
of a population trend; it makes development calibration and source transfer worth checking.

The validation set has **six source videos**, not 33,568 independent learning
examples. A large risk learner/hyperparameter search can overfit source-specific
patterns. Splitting it again into error-fit and policy-selection subsets may be
too fragile. Use a small predeclared grid and source-grouped nested validation;
inspect the concentration of positive events before choosing folds. An alternative
is new backbone-held-out development sources. Training on original MTGS-training
sources is a separately disclosed regime, not a repair for this shortage.

The observed binary-known test prevalence is 651/38,847 = **1.6758%**. Unknown labels
represent **51.69%** of all 80,419 real test pair-frame records. Excluding them is
legitimate for a clearly specified benchmark target, but it changes the question.
If those unknowns were assumed to have meaningful latent binary values without any
further restrictions, the full-record rate could lie between **0.8095% and 52.5038%**.
Those bounds are a hypothetical sensitivity calculation, not estimates of physical
eye contact. Repeated random queries of the known subset cannot identify the
unknown subset's mean.

The [ChildPlay collection protocol](https://publications.idiap.ch/downloads/papers/2023/Tafasca_ICCV_2023.pdf)
selected interesting interaction/gaze clips and annotated up to three selected
people per clip. Consequently even perfect audit estimates concern this curated
benchmark population, not an unbiased sample of everyday child behavior. Its
adult/child metadata may support a separately defined child–adult target, but that
mapping must be verified and declared before selecting the evaluation population.

## 3. A concrete test of the block assumption

We computed a label-only diagnostic for contiguous, nonoverlapping query units,
breaking at missing integer frame indices, clip/pair changes and unknown labels.
For a constant score q=p, define block residual E_b=Y_b-p*c_b. The following is

    R = S²(E_b) / [mean(c_b) * S²(y_i-p)].

For uniform block sampling at matched expected revealed-label cost, it is the
ratio to the frame-SRS variance formula at that same cost (using the continuous
sample-count reference where integer matching is unavailable). It is directly
computed from the fixed annotation population, not estimated by noisy audit trials.

| Maximum query length | Test query units | Mean labels per unit | Test variance ratio R |
| --- | ---: | ---: | ---: |
| 1 | 38,847 | 1.000 | 1.000 |
| 2 | 19,721 | 1.970 | 1.964 |
| 5 | 8,273 | 4.696 | 4.677 |
| 10 | 4,493 | 8.646 | 8.719 |

For length five, the corresponding validation diagnostic is 4.728. These are
unfavorable for buying contiguous labels under a label-count budget. They show
strong observed-label redundancy. They **do not show that MTGS residuals have the
same covariance**, that temporal features are useless, or that a learned block
policy must lose. Those require actual frozen predictions.

For equal-length blocks of k records the exact fixed-population variance ratio is
S²(E)/(k*S²(e)) at a matched sampling fraction. Under a simple common-correlation
working model it is approximately 1+(k-1)rho_e. Positive residual correlation raises
the price of contiguous batches. Temporal information may help the acquisition
model while adjacent labels remain redundant: these are distinct mechanisms.

With per-query overhead a and per-label cost b, a schematic equal-time comparison
has objective proportional to

    [1+(k-1)rho_e] * (a/k + b).

For k=5 and rho_e=.8, block variance is about 4.2 times larger at equal label count.
Even overhead a=10b does not offset that in this simple model; a=100b can. These
are explicitly hypothetical cost scenarios. Actual overhead is set-dependent:
opening a clip once may serve several independently selected frame queries. Both
methods must receive the same interface, contextual viewing and grouping of tasks.
Charging a fresh clip-opening cost for every isolated label would unfairly favor
blocks. The optimum block length is therefore an empirical cost/design question.

## 4. The predictor and acquisition model need stronger controls

### Correction to the earlier methodology

In native MTGS, the social decoder predicts directional learned LAH scores, and
§3.3 defines LAEO as their minimum. It has no separate LAEO loss. Calling this
minimum itself a distinct gaze-point post-processing variant was inaccurate.
Gaze-heatmap/head-box post-processing is the separate variant described in the
supplement. We corrected the main methodology accordingly.
[MTGS §3.3 and supplement A/B](https://www.idiap.ch/~odobez/publications/GuptaTafascaFarkhondehVuillecardOdobez-NEURIPS-2024-MTGazeSocial.pdf).

Supplementary Table 4 reports ChildPlay LAEO F1 of .426 for the native output and
.436 for post-processing; the listed Gupta baseline is .428 and ChongS is .470.
These published figures concern those configurations and do not evaluate current
DINO checkpoints or our estimator. They nevertheless show why pooled VSGaze
performance is insufficient to justify the chosen predictor. F1 alone cannot
predict prevalence bias or a sampling variance reduction.

### Static features cannot be artificially weak

The minimum compresses information: directional scores (.2,.2) and (.2,.9) produce
the same mutual-looking score. A static risk model should also receive both
directional scores, their imbalance and the permitted per-frame geometry; otherwise
an apparent temporal gain may reflect omitted static information. A min of calibrated
marginals is generally an upper bound on their joint probability, not a calibrated
joint probability by construction. The correction estimator can use an uncalibrated
fixed score, but efficiency depends on its errors.

### Squared-error scoring is not automatically the right SRS target

For binary y and a fixed q, the elementary identity

    E[(y-q)² | X] = q² + (1-2q) * E[y | X]

shows that frame squared-error prediction contains no more conditional information
than estimating the contextual label probability and using q. At q=.5 the squared
error is always .25, even if context distinguishes mostly-positive from mostly-negative
groups. A squared-residual forest can therefore miss useful **mean-based**
stratification in that case. This identity is our diagnostic derivation, not a
new inference theorem.

For Poisson sampling, uncentered residual second moments enter the variance
objective. For fixed-size stratified SRS, centered within-stratum variance matters,
and separating residual means can help. Estimate residual mean and variance on
held-out development sources; do not justify every acquisition rule with e².

Add a contextual-calibration control: train a predictor using the same temporal
features/development labels and apply **uniform residual correction** to it. If it
matches temporal active sampling, the gain is attributable to improved imputation
rather than a distinct acquisition mechanism. Keep this comparison separate from
the frozen-q acquisition ablation. This is essential to a credible contribution.

For uniform sampling a fixed-weight control-variate estimator has variance
proportional to

    S²(y-lambda*q) = S²(y) + lambda²*S²(q) - 2*lambda*S(y,q).

At lambda=1 assistance beats human-only sampling only if 2*S(y,q)>S²(q).
The best fixed lambda is S(y,q)/S²(q), but estimating it with scarce labels has a
cost. Use independent development tuning/cross-fitting and compare with an actual
tuned-weight baseline; [finite-sample PPI analysis](https://arxiv.org/html/2505.20178v1)
explains why asymptotic efficiency wording is insufficient.

## 5. Is the label-saving problem substantial enough?

The verified prevalence allows a useful sanity check. Under uniform frame-SRS,
the *true design standard error*, translated into a nominal normal half-width, is
approximately:

| Fraction of eligible labels | Labels | Expected positive frames | Nominal 95% half-width |
| --- | ---: | ---: | ---: |
| 5% | 1,942 | 32.54 | 0.556 percentage points |
| 10% | 3,885 | 65.11 | 0.383 percentage points |
| 20% | 7,769 | 130.19 | 0.255 percentage points |
| 40% | 15,539 | 260.40 | 0.156 percentage points |

These are planning calculations using complete benchmark labels, not realized
intervals or guarantees. The probability of zero positives in the 5% uniform-frame
sample is about 2.37e-15 under that exact sampling design, so describing the *overall*
frame audit as usually finding no positives would be wrong. Small strata, isolated
sources, small budgets and block queries can still have sparse-event failures.
Temporal clustering does not invalidate finite-population frame SRS.

Choose an application-relevant error tolerance before promising practical value.
A gain of .03 percentage points can be a research observation without being worth
a complicated workflow. Measure label savings at comparable error **and** coverage
against the strongest relevant baseline, rather than only against exhaustive labeling.

The full historical train+validation inventory has 319,153 eligible labels. For a
one-off test audit, newly purchasing all of those is very hard to justify. Even
if a method somehow eliminated all 3,885 labels of a 10%-budget baseline, it would
need at least 83 comparable future audits to repay that development count. Under
the illustrative small-sampling-fraction scaling RMSE proportional to 1/sqrt(B),
a 10% RMSE reduction corresponds to about 19% label savings, or 738 labels per
such corpus, requiring about 433 audits. This ignores finite-population corrections,
compute and time, and is **not a forecast of gains**.

The promising operating regime is reuse of genuinely available historical labels,
or a much smaller development set with an observed learning curve. Report that
regime honestly. A new-label total-cost experiment can lead to a different verdict
from a reused-label benchmark. The need for a full MTGS pass also belongs in the
compute/time ledger.

## 6. What can and cannot be validated now

**Validated here:** official annotation counts and hashes, parsed source-video
separation, the known/unknown population distinction, unfavorable constant-score
block redundancy, planning costs, and extensive prior-method overlap.

**Supported theoretically:** the fixed-population difference estimator is
design-unbiased under the specified probability design with fixed public inputs.
No i.i.d. frame assumption is needed. Normal-interval accuracy is a separate issue.
The existing small enumeration tests address the estimator, not project novelty.

**Still unknown:** current raw-media accessibility, decoded frame alignment, exact
checkpoint exposure, score calibration/correlation, temporal residual structure,
source-held-out score-learning gains, full comparator results, annotation time,
reference disagreement, and new-source transfer. No literature search can turn
those into observed results.

The supplied project has already inspected test-label summaries, and this review
now inspects the full reference tables for diagnostics. All current ChildPlay
test experiments should remain explicitly exploratory. A new untouched compatible
corpus is needed for confirmation. Do not redesign a policy on the observed test
diagnostics and then call its evaluation confirmatory.

## 7. Recommended decision and smallest decisive pilot

Continue with the working topic **“Auditing rare social-gaze measurements under
temporal dependence and annotation cost.”** Keep the target to benchmark-defined
mutual-looking prevalence. Avoid autism/ADHD diagnosis and eye-specific-contact
claims without the corresponding validation.

Run the following gates before broad implementation:

1. **Prediction gate.** Cache a pinned MTGS output with directional scores and
   source metadata. Confirm input hygiene/alignment and characterize backbone
   exposure. A second existing predictor is a valuable sensitivity comparison;
   do not assume the MTGS paper's pooled ranking transfers to ChildPlay.
2. **Information gate.** With source-held-out development evaluation, compare
   static/full-directional and temporal residual mean/variance models, plus
   smoothing/contextual calibration. Establish that temporal context adds useful
   information beyond those controls. Ranking accuracy alone is not enough;
   evaluate resulting estimator variance/accuracy.
3. **Sampling gate.** At the predeclared 10% budget compare uniform human-only,
   uniform corrected, tuned-weight corrected, strong static learned acquisition,
   temporal acquisition, and contextual-predictor uniform correction. Report error,
   design-appropriate coverage and all costs. Then add StratPPI/Robust ASI/CPS and
   the relevant video-aggregation comparator adaptations for a research claim.
4. **Batching gate.** Measure actual MTGS residual covariance before paying for
   blocks. Compare frame and block queries with matched expected label cost. Add
   measured time only with a shared interface and actual timing observations.
5. **Contribution gate.** Keep the earlier 10% relative-RMSE improvement target as
   a predeclared practical target, not a prediction or a universal publication
   threshold. If gains vanish against static/full-directional or contextual
   calibration, simplify the method. If blocks lose, retain that result. Replicate
   any claimed transfer gain on untouched compatible sources.

If these gates fail, the honest output is a reproducible benchmark and a negative
result about temporal querying or annotation cost. That can be a useful team
project, but its research strength depends on breadth, careful analysis and an
interesting finding; documentation alone does not make a publishable contribution.

If the gates succeed, the defensible claim concerns **measured improvement under
explicit conditions**, not the invention of PPI, temporal inference, or selective
video aggregation. A stronger new-method project would need a distinct acquisition
or uncertainty mechanism and another dedicated novelty/theory check.

## Reproduction and scope of artifacts

See [reproduction.md](reproduction.md). Aggregate checks are committed in
`annotation-inventory.json` and `feasibility-checks.json`. Raw archives, individual
labels, media, checkpoints and generated caches stay outside version control.
