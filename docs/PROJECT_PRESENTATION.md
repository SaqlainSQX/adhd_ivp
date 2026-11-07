# Course presentation walkthrough and likely questions

Suggested title: **Label-efficient auditing of social-gaze prevalence**.
Describe this as an experimental computer-vision/statistics course project.
The goal is a useful, explainable system and honest evaluation; the work does
not introduce a new gaze backbone or establish clinical validity.

## Presentation sequence

| Time | Topic | Evidence to show | Main message |
| --- | --- | --- | --- |
| 0:00–0:45 | Problem | Model mean 7.141% versus benchmark prevalence 3.519% | Averaging model scores can misestimate collection prevalence |
| 0:45–1:30 | Data and predictor | Verified subset diagram and provided-track frame | Same 53-source population and frozen temporal MTGS for every method |
| 1:30–2:15 | Audit estimator | Equation in the explorer Method panel | Query a fixed budget and use weighted residuals to correct the mean |
| 2:15–3:15 | Main controls | Main RMSE table and M5 control | Guided allocation helps versus uniform; extra temporal guidance does not beat static |
| 3:15–4:00 | Stronger simple baselines | `simple-guidance-controls.png` | Score quartiles outperform learned guidance at 5–20%; static wins at 40% |
| 4:00–4:45 | Uncertainty | Interval and variance figures, exact-reference table | Low error does not imply trustworthy normal intervals; show coverage and width together |
| 4:45–6:15 | Demonstration | Saved audit, head-track frame, query timeline, label toggle | The audit is reproducible and its label budget is explicit |
| 6:15–7:00 | Contribution and limits | Source exclusions, independent checks and costs | A controlled, verified pipeline with a useful simpler-control finding |

Use the [demo guide](DEMO_GUIDE.md) for the precise command and clicks. The
[main report](../reports/course-project/course-report.md) and
[strengthening report](../reports/course-project/strengthening-report.md) contain
the authoritative outcomes. Avoid choosing a single flattering audit example;
demonstrate the fixed draw and then return to aggregate results.

## Explain the method in plain language

“We first run an existing social-gaze predictor and cache its scores. We partition
the collection using public scores or a development-trained error model. A fixed
number of pair-frames is sampled without replacement from each stratum. We reveal
only those reference labels and correct the full model mean using weighted
sampled errors. We compare methods at identical label budgets and replay every
random plan.”

Static guidance and temporal guidance share the same temporal backbone. Their
difference is the extra neighborhood/transition features available to the error
learner. Score quartiles require no error predictor, but their allocation moments
still use historical training labels. They are not a zero-development-label method.

## Defensible headline findings

- The original primary-budget RMSE is 0.5529 pp for uniform residual correction,
  0.2603 pp for learned static guidance and 0.2765 pp for learned temporal guidance.
- The exploratory score control reaches 0.2079 pp at the same 1,032-label budget:
  62.4% below uniform residual correction and 20.1% below learned static guidance.
  This does not select a replacement winner for the locked main comparison.
- Normal coverage is method- and budget-dependent. The score control has 96.0%
  coverage at 10% labels but only 45.9% at 40%; report both.
- Student-t and development calibration did not resolve the main undercoverage.
  The separate exact binary reference trades interval width for fixed-population
  design coverage. It is established statistical machinery, not a new theorem.
- All original losses/ties and source exclusions remain visible. Extra complexity
  is not supported simply because it was the initial hypothesis.

## Questions an examiner may ask

**What is original here?** The implemented data-verification and cache-to-audit
pipeline, controlled application comparison, exact label budgets, independent
replay, contextual-surrogate control and the systematic examination of when
simpler guidance works. Residual correction, stratification and exact intervals
are existing ideas.

**Why did you keep a temporal method that loses?** Testing whether context helps
was the hypothesis. The result is informative: under this development recipe and
available subset, additional features did not demonstrate a primary advantage.
Three validation sources and distribution shift limit any broader explanation.

**Why does the estimator work?** Within each fixed stratum, the sampled residual
mean has expectation equal to that stratum's population residual mean. Weighting
by its population fraction and adding the full q mean recovers population y mean
in expectation under the sampling design. This requires correct inclusion and
weights, not perfectly calibrated model scores.

**Does it identify ADHD or diagnose anything?** No. Its target is benchmark-defined
mutual-looking prevalence for provided tracks in an offline collection. Diagnosis
and clinical screening require different data, outcomes and validation.

**Does the simpler control use no labels?** Its cuts are public-score quartiles,
but residual SD allocation moments use training labels and alpha uses validation.
We disclose 191,956 training and 25,139 validation labels reused historically.

**Why not trust a narrow normal interval?** A few large residuals can dominate
variance in a lightly sampled stratum. Missing those records can make estimated
variance too small on that draw, even when the average variance estimator is
close to correct. The post-hoc tail diagnostic illustrates this; it did not tune
the sampler.

**Why can an exact binary interval have a different center?** It bounds stratum
binary totals using the queried success counts and finite-population sampling.
The point estimator also uses all q scores. They are separate constructions;
the reference interval must not be called an exact residual-centered interval.

**Do these confidence guarantees apply to new videos?** The exact reference is a
design statement for the fixed binary population under the specified sampling
plan. It does not cover new-source distribution shift, incorrect annotations,
unavailable media or clinical validity. Monte Carlo method comparisons also
describe this corpus rather than a new-source replication.

**Did you save annotation time?** We demonstrated label-count efficiency using
existing references, not observed human-time savings. No annotator timing pilot
was performed.

**Can a teammate reproduce it?** Git contains source, locked configurations,
registered protocols and aggregate evidence. Raw media/references, query arrays,
fitted models and environments remain local. With the matching local artifacts,
the scripts and explorer reproduce saved queries, estimates and variances.
