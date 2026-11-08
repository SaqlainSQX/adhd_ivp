# UCO transfer: useful score allocation, failed half-weight transfer

Accepted8 November2026. This is the first locked evaluation of the course
estimator on this UCO population. It is exploratory downstream dataset transfer:
UCO is a VSGaze component used by the pretrained backbone, and upstream UCO
head boxes were retained while the ChildPlay export clipped its boxes. It is
not an independent backbone-pretraining, new-person or clinical evaluation.

The full-weight frozen score-stratified design beats uniform difference
sampling at every budget. The half-weight correction that helped on ChildPlay
loses to full weight at every UCO budget. No weight, model, allocation or subset
was retuned after observing these outcomes. The old ChildPlay study and all
earlier losses/ties remain intact.

## Locked primary result

At521 queried pair-frame labels, full-weight K4 RMSE is0.592311 percentage
points, half-weight K4 is0.751927, and uniform difference sampling is0.795989.

- Primary half/full ratio: **1.269481**, draw-bootstrap95% interval
  **[1.220213,1.319341]**. The half-weight method is26.9% worse; the registered
  target of at least10% improvement failed.
- Secondary full-weight K4/uniform ratio: **0.744119**, interval
  **[0.700975,0.792257]**:25.6% lower RMSE at the same exact label budget.

The primary methods use identical queries. Uniform uses its separate registered
stream. Bootstrap intervals describe1,000 simulated audit draws on a fixed
finite population; they do not measure uncertainty over new videos or people.

## All budgets and losses

| Exact labels | Uniform RMSE pp | Full-weight K4 RMSE pp | Half-weight K4 RMSE pp | Half/full ratio |
| ---: | ---: | ---: | ---: | ---: |
|260|1.163361|0.947330|1.280219|1.351397|
|521|0.795989|0.592311|0.751927|1.269481|
|1043|0.554482|0.362877|0.485805|1.338761|
|2087|0.339252|0.176287|0.229096|1.299567|

Full-weight K4/uniform ratios are0.8143/0.7441/0.6544/0.5196. The half-weight
method also loses to uniform at the smallest budget. This negative result
narrows the contribution: frozen score-guided allocation is useful here, while
the specific ChildPlay half-weight gain is not a universal improvement.

The reference prevalence is27.380724% among5,219 eligible annotated pair-frames
in15 test clips. This is a benchmark-defined target, not prevalence throughout
TV footage or a general social/clinical population. It is substantially different
from ChildPlay's3.518806%, but that contrast alone does not explain the variance
loss or establish causation. Four TV-show sources and related clips limit
independent domain evidence.

## Interval reliability

At the primary budget, normal95% coverage is95.1% for full-weight K4,95.9% for
half weight and95.9% for uniform. Across all budgets, normal coverage spans
94.1–96.2%. These are fixed-population audit simulations, not a guarantee of
normal intervals for every corpus.

The equal-Bonferroni exact binary reference interval has99.4% primary coverage
for the shared K4 queries but a mean width of16.0359 percentage points. Uniform
exact coverage is95.5%, width7.4136 pp. The two K4 weights share exactly the same
binary reference interval; changing the point predictor cannot tighten it.
At the largest budget, K4 exact coverage is99.0%, width6.4252 pp. Conservative
validity and practical precision remain distinct. Do not substitute a normal
interval because it looks tighter after observing results.

## Execution and independent evidence

The previous K4 index failure and its author-supported ordinal normalization
are preserved. All5,219 eligible references were prepared before score inference.
The frozen model processed2,357 anchors in295.95 seconds, using no oracle.
Cached/uncached first-window tensors matched exactly; first-window FP32/AMP
probability discrepancies were0.000420 LAH and0.000078 LAEO, below0.002.
All prediction files were hashed and matched the unique eligible population.

All eight public query files were created and hashed before evaluation opened
the oracle. All12,000 method draws passed independent RNG/unique-budget replay,
point/variance and normal-bound recomputation. Maximum point and variance
differences were1.67e-16 and1.00e-16. A separate validator exhaustively enumerated
feasible integer totals for515 cached hypergeometric cases, confirming every
saved exact interval; all12 bootstrap comparisons were reproduced. No failed
draw was dropped.81 implementation tests had passed before inference; Ruff
passed on the new evaluation/validation/report scripts.

The aggregate figure was rendered and visually inspected, including the primary
loss, all budgets, coverage, interval widths and geometry/exposure footnotes:
`reports/course-project/uco-transfer-l.png` (PDF alongside it). It contains no
raw media or per-person records. Complete aggregate JSON/proof are under
`docs/research/l-*`; raw scores, oracle and per-query logs remain ignored.

## What to present for the course

Keep the main submission and show this as a transfer/limitations appendix:
"Score-guided sampling helped on a second benchmark, but the half-weight
residual correction did not transfer." This is stronger evidence than hiding
the loss or claiming a universally improved gaze model. No new ADHD or temporal
recognition claim follows. Next, use the registered post-hoc variance decomposition
to explain the fixed comparison; do not use UCO outcomes to pick another weight
and then call that an independent confirmation.
