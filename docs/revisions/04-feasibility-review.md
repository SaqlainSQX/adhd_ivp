# Pass 4: implementation, decision rules and final scope

This pass converts the corrected study from pass 3 into a sequence the team can
implement. It does not claim empirical improvement or certify publication novelty.

## Recommended project

Working title: **Label-Efficient Auditing of Mutual-Looking Prevalence in Video:
Temporal Context versus Annotation Batching**.

The primary research question is whether temporal context improves source-held-out
error-guided sampling at equal revealed-label cost, relative to a static risk model
and strong prediction-assisted baselines. The secondary question is when contiguous
queries become worthwhile under measured annotation overhead.

## Scope reductions

- Keep MTGS frozen. Training another gaze model or adding SACF is outside the
  first milestone. A second predictor is a later sensitivity test.
- Use one interpretable static score model and the same learner with temporal
  inputs. Start with ridge regression and a depth-4 random forest.
- Use up to four development-defined strata and stratified SRS first. Treat
  Poisson/CPS implementations as separate verified designs.
- Start with label count as cost. Add a timed study only if there is access to
  annotators, media and a consistent labeling protocol.
- Do not build a clinical interface or infer diagnosis, symptom severity, or
  treatment outcomes from these estimates.

## Acceptance gates

| Gate | Must be true before proceeding |
| --- | --- |
| A: inventory | Regenerate counts, unknown exclusions, canonical pairs and source manifests from the actual archive; reconcile differences with deck counts |
| B: inference | Confirm video/frame/track alignment and checkpoint exposure; cache scores with hashes and no hidden gaze annotations in input |
| C: estimator | Exhaustive small-population tests establish unbiasedness and expected variance; sampler only receives public features |
| D: development | Freeze feature definitions, hyperparameter grid, strata, allocation, label budgets, interval choices and seeds without evaluation tuning |
| E: benchmark | Run the factorial study plus the minimum baselines, 1,000 draws and all costs/failures; label previously inspected evaluation exploratory |
| F: contribution | A temporal advantage survives static learned-risk and smoothing controls; otherwise report the negative result and the simpler preferred method |
| G: transfer/time claims | Collect untouched compatible sources or actual time measurements before making the corresponding claims |

## Predeclared result interpretation

Use RMSE in percentage points as the primary point-estimation metric at the 10%
label budget. Report 5%, 20% and 40% as secondary budget results. These choices
are design decisions made now, not derived from observed performance.

A 10% relative RMSE reduction versus static learned-risk is a proposed practical
effect threshold. It is a target, not a predicted gain. Use a source-resampling
sensitivity analysis with paired method runs; report uncertainty and per-source
effects rather than treating audit draws as independent datasets. If too few
sources support credible transfer uncertainty, limit the claim to the fixed corpus.

Always report point accuracy and interval validity separately. The normal interval
has no finite-sample guarantee. Publish its empirical coverage with Monte Carlo
error; report a conservative finite-population interval as a validity reference.
An efficiency claim based on normal-interval width fails if coverage is materially
below nominal. No test-set-driven switching to a favorable interval method.

## Current scaffold versus the revised plan

The provisional code implements normalized cache checks, blocks, grouped risk
fitting, validation mixture selection, block sampling, the difference estimator,
approximate normal intervals, synthetic data, and initial block baselines.
It is a software exercise, not an implementation of the complete revised study.

Still required: explicit temporal features on frame queries, static/temporal
factorial scoring, real-data inventory and MTGS adapter, conservative intervals,
strong statistical comparators, immutable experiment locking, timed annotation,
and untouched-source evaluation. The scaffold must not be used as experimental
evidence for the final contribution.

## Final contribution wording

Proposed: “We develop and evaluate a reproducible audit protocol for mutual-looking
prevalence that separates temporal context used in label selection from temporal
batching used in label acquisition. We study its accuracy, interval coverage and
full annotation cost under explicit source and predictor-exposure controls.”

Replace “study” with a positive performance statement only after the relevant
experiment succeeds. Claim a new sampling method only if an additional distinct
mechanism, prior-work check and theoretical analysis support it.

The consolidated protocol is in [methodology.md](../methodology.md); the four pass
documents preserve the reasoning behind the revision.
