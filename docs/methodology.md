# Methodology v1: mutual-looking prevalence audits

Date: 25 October 2026. Status: proposed protocol following four revision passes;
not preregistered, not an empirical result. Read the [revision record](revisions/01-validity-review.md)
for the sequence of corrections. Changes after any evaluation access must be
versioned and marked exploratory.

## 1. Project decision and contribution

Working title: **Label-Efficient Auditing of Mutual-Looking Prevalence in Video:
Temporal Context versus Annotation Batching**.

Estimate an aggregate mutual-looking rate from frozen predictions and a limited
random sample of reference labels. Investigate whether temporal context helps
choose which labels to reveal, independently of whether annotations are requested
in contiguous batches. The core output is a reproducible measurement study and
audit pipeline. The proposed forest, stratification, residual correction, and
uniform/active interpolation are established components, not claimed inventions.

The candidate scientific contribution is evidence about when temporal error
structure is useful for querying and when label redundancy outweighs annotation
overhead savings. A negative result is informative if the controls and cost
measurements identify when a simpler method is preferable. No improvement or
publication outcome is assumed.

## 2. Research questions and hypotheses

- **RQ1, primary:** Does a risk model with temporal prediction context reduce
  prevalence-estimation RMSE versus an otherwise identical static risk model when
  both query individual pair-frames at the same label budget?
- **RQ2:** Does changing the query unit from a frame to a nonoverlapping contiguous
  block improve the cost–accuracy tradeoff after controlling for context features?
- **RQ3:** How do rare positives, predictor bias, source shift, development-label
  volume and annotation overhead affect accuracy and interval coverage?

H1 is that temporal context can reveal persistent error patterns. H2 is that blocks
may lose under label-count budgets but become competitive with meaningful setup
overhead. Both are falsifiable hypotheses. Temporal coherence is not evidence of
correctness: confidently wrong predictions can remain coherent.

## 3. Estimand and eligibility

Let U be the fixed set of eligible, unique, unordered person-pair/frame records and
M = |U|. The reference y_i is the binary VSGaze LAEO annotation. The primary target is

    p_U = (1/M) sum_{i in U} y_i.

Exclude placeholder IDs, self-pairs, and unknown LAEO labels. Canonicalize unordered
person pairs and reconcile reverse orientations before deduplication. Conflicting
duplicates cause a validation error. Preserve a ledger of every exclusion. Keep
the eligibility mask separate from the hidden binary values; its use is permitted
for this explicitly binary-labeled benchmark population.

This target gives more influence to frames with more eligible pairs. It is neither
an equal-clip mean nor a duration or event-count estimate. Unknown-label exclusions
can cause selection bias relative to all real pair-frames; report coverage of that
larger set, but do not extrapolate without a missingness study. Do not use labels to
select only child–adult pairs unless independent role metadata defines that target.

VSGaze's head/gaze-derived mutual-looking convention does not establish physical
eye-to-eye contact, joint attention, autism status, or ADHD status. The repository
name does not define the scientific endpoint. Autism-related work motivates the
application; clinical validity requires separate data and assessment. [R1–R3]

The supplied deck reports 38,847 eligible test records and 651 positives. Treat
these as supplied inventory claims until code reproduces them from the same archive
and schema. This workspace currently has neither the archive nor raw media.

## 4. Data and predictor provenance

Use ChildPlay within VSGaze first. Record annotation archive hash, release, frame
index/time conventions, source video ID, clip boundaries, person IDs, pair IDs and
reference-label construction. Audit one-to-one alignment of cached scores to
reference IDs. Verify representative frames visually and publish alignment
failure counts; a CSV join alone cannot prove media alignment.

Freeze one MTGS checkpoint and exact upstream commit, configuration, preprocessing,
temporal window, and output interpretation. Keep decoder and gaze-point/head-box
post-processing outputs separate. A min of directional LAH scores is an explicitly
named post-processing variant; do not silently substitute it for decoder LAEO.
Do not pass reference gaze points or other hidden annotations into inference.
Read the selected checkpoint's actual output code before writing the adapter. [R1,R2]

Create a backbone-exposure manifest: which sources trained the predictor, selected
its checkpoint, fitted any calibration, fitted the risk score and selected the
sampling policy. Grouped risk cross-validation does not undo MTGS's exposure to a
source. Prefer error-fit and policy-selection sources excluded from backbone
fitting. If using original training sources, disclose that exposure and add a
held-out-development sensitivity analysis. Baselines receive identical information.

No model download or code vendoring is necessary for the methodology milestone.
Keep upstream model dependencies separate until the exact checkpoint is chosen.

## 5. Splits and access protocol

1. Group clips by original source video before all error-model splits. Where subject
   or recording-session IDs are available, inspect and prevent corresponding
   overlap for subject/session generalization claims.
2. Use D_error to fit the risk learner and grouped out-of-fold development moments.
   Use a source-separated D_select for policy/hyperparameter selection. Prefer
   suitable backbone-held-out development sources, subject to actual inventory.
3. Use D_eval for frozen-policy offline audits. The deck discloses prior test-label
   inspection, so current ChildPlay test results are exploratory for this project.
4. Reserve D_confirm from untouched, compatible sources before a confirmatory
   claim. If access is unavailable, complete the exploratory study and state that
   limitation; do not rename a repeatedly inspected subset “untouched.”

If the available development sources/positives cannot support D_error and D_select,
use nested source-grouped development validation and explicitly reduce model/grid
complexity. Do not split neighboring frames at random to manufacture sample size.
Fix and record all partitions before evaluation.

The sampler sees IDs, eligibility, predictions and permitted geometry. The oracle
holds reference values and releases only the fully pre-drawn sample. The estimator
sees those selected values and the full known prediction totals. The evaluator
may read complete truth after policy locking. Log seeds, costs, first/second-order
inclusion information required by the chosen design, and access chronology.

## 6. Features, query units and factorial comparison

The base predictor already uses time. “Static scoring” means that the error-risk
learner uses per-frame outputs only; it does not mean a different gaze backbone.

| Risk features | Query one frame | Query one block |
| --- | --- | --- |
| Static outputs | Static/frame | Static/block |
| Temporal context added | Temporal/frame, primary candidate | Temporal/block |

Static features: frozen score q_i, binary entropy, independently available head
geometry and frame occupancy. Temporal features: mean/std of neighboring scores,
adjacent variation, lagged score differences and geometry changes. Use symmetric
windows for this offline study; a streaming claim would require a causal window.
Missing/unknown pair-frames break query blocks. Unlabeled context is allowed only
where scores and valid tracking genuinely exist. Never fill unavailable context
using reference gaze values or unknown-label guesses.

For block scoring, summarize per-frame static features without ordering. The
temporal version adds order-dependent features. Size is present in both. Fix
maximum block lengths in {2,5,10}; preserve short final blocks. Query units form
a nonoverlapping partition. Context windows may overlap, reference labels may not.

Use the same learner/grid across the feature comparison: ridge regression and a
64-tree random forest with max_depth=4 are initial candidates. Model training uses
development labels only. Compare an explicit moving-average score and a temporal
order-shuffle diagnostic to distinguish context utility from simple smoothing.

## 7. Sampling design and estimator

The first implementation uses stratified SRS without replacement, allowing an
auditable finite-population analysis. A query unit u contains c_u pair-frames,
Q_u = sum_i q_i and Y_u = sum_i y_i. For frame queries, c_u=1. Let e_u=Y_u-Q_u.
Partition all units into H<=4 strata using development-defined cut points.

Within stratum h, preselect n_h units uniformly without replacement from N_h units,
independently across strata. Maintain positive inclusion probability and take a
census of any stratum smaller than its minimum sample. The estimator is

    p_hat = [sum_{all units} Q_u + sum_h (N_h/n_h) sum_{sample h} e_u] / M.

Conditional on fixed population, predictions, strata and sample counts, its design
expectation is p_U. No independence between neighboring reference labels is needed
for this statement. This does not imply validity for a population of future videos.

Its design variance is

    Var(p_hat) = (1/M²) sum_h N_h² (1-n_h/N_h) S²_e,h / n_h.

For non-census n_h>=2, replace S²_e,h by the sample variance for an unbiased
variance estimator. At census the contribution is zero. Having two observations
makes the variance computable; it does not make a normal approximation reliable.

Estimate centered residual SD by source-held-out development folds. The classical
cost-adjusted allocation is n_h proportional to N_h sigma_h / sqrt(mean_c_h).
It is a continuous interior optimum before integer/cap/minimum constraints.
Compare it with proportional allocation. Interpolate between separately
budget-normalized feasible allocations; select mixture in {0,.25,.5,.75,1} on
D_select, without a “never worse” guarantee. [R4–R6]

For frames, round to fixed integer counts that sum to B and record actual weights.
For unequal-size blocks, randomized rounding can preserve expected label cost,
but realized cost varies. Condition the estimator on the realized n_h. Do not
truncate samples or stop after reaching a label cap with the same weights.

Squared residual prediction is a possible stratification score, not the same as
centered within-stratum variance. Under independent Poisson queries the relevant
variance is (1/M²) sum_u (1-pi_u)e_u²/pi_u; second moments and cost-adjusted
inclusion then have a different derivation. Keep Poisson ASI, CPS, and SRS adapters
distinct. Weighted choices without replacement do not generally have inclusion
probability equal to normalized score weight. [R5,R6,R9]

## 8. Confidence intervals and rare-event safeguards

Report the standard normal interval p_hat +/- 1.96 SE as an **approximate** interval
and audit empirical coverage. Save raw estimates/endpoints. Label optional bounded
presentation separately. Zero observed positives, zero sample residual variance,
and tiny samples are reported failure modes rather than evidence of certainty.

Also implement a conservative design-valid bounded-residual interval. For each
stratum let a_h=min_u(-Q_u), b_h=max_u(c_u-Q_u), computed from public quantities.
Every residual lies in [a_h,b_h]. For non-census strata use

    t_h = (b_h-a_h) sqrt[log(2H/alpha)/(2n_h)], alpha=.05.

Hoeffding's finite-population sampling bound and a union bound give simultaneous
stratum mean-residual intervals. Propagate their endpoints through the positive
N_h/M weights around the known prediction total. Census strata have t_h=0.
Intersect the resulting interval with [0,1]; preserve and flag an empty intersection.
This basic interval can be very wide. It supplies a validity reference, not an
invented efficiency guarantee. A verified Serfling/empirical Bernstein refinement
may be added as a separately specified method. [R10]

For the binary, frame-level human-only baseline, invert the finite-population
hypergeometric distribution as an additional reference. Never switch between
approximate and conservative intervals after seeing evaluation labels to select
the narrower one. Changes in interval strategy require development-only selection
or simultaneous guarantees.

## 9. Baselines and fairness

| Baseline | Purpose and implementation boundary |
| --- | --- |
| Raw model-only and development-calibrated mean | Quantify uncorrected prediction bias; neither alone provides an audit CI |
| Uniform human-only frames | Primary annotation-only reference at exact B |
| Uniform residual-corrected frames | Isolate the value of selective querying |
| Development-tuned control-variate/PPI weight | Ensure an overly aggressive fixed predictor weight is not a weak baseline |
| Entropy-guided randomized queries | Compare generic uncertainty with learned error risk |
| Static learned-risk queries | Primary control for temporal information |
| StratPPI | Strong stratification and power-tuning comparator; distinguish original and finite-corpus adaptation |
| ASI and Robust ASI | Use verified author code/settings where compatible; name finite-corpus/block adaptations explicitly |
| Fixed-Size ASI/CPS | Check gains beyond eliminating random sample size; use correct design inclusion probabilities |
| Active testing | Additional acquisition/estimation comparator where its risk objective is adapted and justified |

For all comparisons record prediction access, geometry/context access, development
labels, calibration labels, expected and realized test labels, inference cost and
source exposure. Provide paper-faithful experiments where assumptions match, and
separately label adaptations; one shared formula is not a faithful implementation
of every named method. Frame ASI/CPS needs actual inclusion probabilities under
its design, not preconditioning Bernoulli probabilities. [R4–R9,R11]

## 10. Evaluation and decision rules

Use 1,000 audit draws on each frozen corpus at 5%, 10%, 20%, 40% of eligible
pair-frame labels, and a census sanity check. Primary comparison: temporal/frame
versus static/frame at 10%. Report bias, RMSE and absolute error in percentage
points, approximate/conservative 95% coverage, interval width, zero-positive draws,
infeasible strata/budgets, and realized cost quantiles. Normal-interval width is
only an efficiency outcome together with adequate observed coverage.

Coverage Monte Carlo SE is sqrt(C(1-C)/R); at C=.95 and R=1000 it is about .0069.
Also report uncertainty for RMSE or paired squared-error differences. Reusing the
same seed can couple methods but is not itself an independent-source replication.
Use paired source-resampling sensitivity analyses and show source-level outcomes;
with few sources do not turn a bootstrap into a strong transfer claim.

Proposed practical effect threshold: >=10% relative RMSE reduction against static
learned-risk at the primary budget, supported by uncertainty estimates and source
sensitivity. This threshold is a planning choice. An effect that vanishes against
smoothing, strong inference baselines, or an alternate held-out source set does not
support a general temporal advantage. Do not select the best evaluation budget or
subgroup after inspecting all results and label it primary.

Required ablations: temporal feature removal, moving-average score, query length,
mixture strength, development-label budgets, predictor calibration, and source-held-out
error training. Secondary robustness: rare-event prevalence and burst-length
simulations; report them as simulations, not ChildPlay findings. Freeze the primary
checkpoint, with a second compatible predictor only in a separately planned sensitivity.

## 11. Cost and annotation time

Separate reused development labels from newly purchased labels. Report D_error,
D_select, calibration and per-corpus audit label counts; include subsampled
development-label curves. Break-even over K future corpora requires

    K * (baseline labels per corpus - proposed labels per corpus) > development labels,

under comparable unit costs. Inference/compute costs are reported separately.

Before claiming time savings, run a small timed pilot with identical labeling
instructions, random query order and repeated items for reliability. Measure clip
opening/setup, navigation, per-frame decision time, skipped/ambiguous items and
adjudication. Then fit the proposed time model T(S)=sum_{opened clips} setup +
sum_{queried labels} decision_time on those observations. Compare label-count and
measured-time frontiers separately. If timing is unavailable, publish label savings
only; adjacent queries do not automatically prove time savings.

Reference labels define the benchmark truth. A separate double-annotation and
adjudication study is needed to investigate human agreement or construct validity.
Do not describe existing archive labels as error-free clinical ground truth.

## 12. Implementation gates and current status

Sequence: (A) regenerate inventory; (B) audit media and backbone exposure;
(C) cache pinned predictions; (D) verify sampler/estimator; (E) freeze development
policy; (F) run factorial and baseline audits; (G) add confirmatory sources/time study.
The concrete tasks and acceptance conditions are in [roadmap.md](roadmap.md).

Current repository code is a provisional block-only synthetic scaffold. It is not
the completed methodology. In particular frame-context features, the full factorial
design, formal conservative interval, real-data adapter, full comparator suite and
immutable policy locking remain to implement. No empirical performance claim is
currently supported.

## References checked

- R1. [MTGS official repository](https://github.com/idiap/MTGS) and
  [NeurIPS 2024 paper](https://papers.nips.cc/paper_files/paper/2024/file/1caf09c9f4e6b0150b06a07e77f2710c-Paper-Conference.pdf).
- R2. [VSGaze official schema/media links](https://www2.idiap.ch/en/dataset/vsgaze).
- R3. [Deng et al., AGT/SACF, AAAI 2026](https://ojs.aaai.org/index.php/AAAI/article/download/41177/45138).
- R4. [Fisch et al., StratPPI, NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/file/c9fcd02e6445c7dfbad6986abee53d0d-Paper-Conference.pdf).
- R5. [Zrnic and Candes, ASI, ICML 2024](https://proceedings.mlr.press/v235/zrnic24a.html).
- R6. [Li et al., Robust ASI, arXiv:2511.08991v1](https://arxiv.org/html/2511.08991v1).
- R7. [Csillag et al., Conformal PPI, arXiv:2510.16166v1](https://arxiv.org/html/2510.16166v1).
- R8. [Rizvi et al., PPITSAS, arXiv:2610.08715v1](https://arxiv.org/html/2610.08715v1).
- R9. [Skalnes and Oberst, Fixed-Size ASI, arXiv:2610.27389v1](https://arxiv.org/html/2610.27389v1).
- R10. [Bardenet and Maillard, concentration without replacement, Bernoulli 2015](https://arxiv.org/pdf/1309.4029).
- R11. [Kossen et al., Active Testing, ICML 2021](https://proceedings.mlr.press/v139/kossen21a.html).
- R12. [Mani et al., finite-sample PPI analysis, arXiv:2505.20178v1](https://arxiv.org/html/2505.20178v1).
- R13. [Vadlamani et al., Transfer Calibrated PPI, arXiv:2609.34156](https://arxiv.org/abs/2609.34156).
  Relevant if predictor adaptation is introduced; not a claim that all transfer is solved.

Literature screening is targeted. Candidate novelty remains contingent on a wider
related-work search and actual comparative evidence. Paper-specific guarantees
apply under their stated assumptions; this protocol does not inherit them merely
by combining their components.
