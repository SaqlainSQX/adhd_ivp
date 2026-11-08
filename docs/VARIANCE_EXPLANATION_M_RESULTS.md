# Why the fixed half-weight comparison reverses

8 November2026. This is the registered post-hoc interpretation of the already
locked ChildPlay D and UCO L results. No new model, weight, query or allocation
was fitted or selected. It explains these finite populations; it is not another
independent generalization result.

Both difference estimators are design-unbiased: changing the prediction from q
to0.5q changes the residual sampling variance, not the target reference mean.
Under the frozen stratum sample counts,

`V(lambda) = A - 2 lambda B + lambda² C`,

where A aggregates within-stratum reference variances, B aggregates reference–q
covariances, and C aggregates q variances, with the exact finite-population
sampling factors. Therefore

`V(0.5) - V(1) = B - 0.75 C`.

Half weight helps if this difference is negative and hurts if it is positive.
This is an identity for the two fixed comparisons, not a fitted decision rule
for choosing a new weight on test labels.

## Primary10% interpretation

| Quantity | ChildPlay,1032 labels | UCO,521 labels |
| --- | ---: | ---: |
| A, pp² |0.0463495|1.2934088|
| B, pp² |0.0190955|0.8803343|
| C, pp² |0.0384910|0.8327570|
|0.75 C, pp²|0.0288683|0.6245677|
|Half minus full variance, pp²|−0.0097728|+0.2557665|
|Exact design RMSE ratio, half/full|0.889104|1.303755|
|Saved Monte Carlo RMSE ratio, half/full|0.894677|1.269481|

On ChildPlay, the reduction in q's variance contribution outweighs the lost
covariance benefit. On UCO, reducing q loses more covariance benefit than it
saves in that variance term. Thus the reversal persists in exact design
variance; it is not explained away by choosing a different random audit seed.
The observed Monte Carlo values fluctuate around these exact quantities.

This does not establish that prevalence caused the difference. Annotation
geometry preparation, score/reference association, scene content and pretrained
backbone exposure also differ. Do not use this analysis to select another weight
on either inspected test population and call it a confirmed improvement.

## All frozen budgets

| Dataset | Exact labels | Exact half/full RMSE ratio | Saved MC half/full RMSE ratio |
| --- | ---: | ---: | ---: |
|ChildPlay|516|0.887857|0.903219|
|ChildPlay|1032|0.889104|0.894677|
|ChildPlay|2063|0.897732|0.891040|
|ChildPlay|4126|0.985511|0.985320|
|UCO|260|1.304516|1.351397|
|UCO|521|1.303755|1.269481|
|UCO|1043|1.303407|1.338761|
|UCO|2087|1.301691|1.299567|

Exact half-weight variance is lower on all four ChildPlay designs and higher
on all four UCO designs. The two corpora use their stored budgets and query
streams; no paired cross-corpus sampling claim is made. The full-weight K4
allocation benefit over uniform on UCO remains in the L report and is distinct
from this fixed-weight interpretation.

## Validation and artifacts

All16 fixed-weight algebraic variances matched directly calculated residual
variances and the previously saved exact-design quantities; maximum difference
was1.36e-19. An independent centered-dot-product calculation checked96 stratum
A/B/C values across eight budget cells. Input hashes and the implementation were
recorded before the descriptive readout. No policy parameters or old outcomes
changed. Ruff passed; no GPU or new queries were used.

Aggregate per-stratum components, checks and registration are in
`docs/research/m-*`; runtime originals are in outputs/variance-explanation-m-v1.
The standalone PNG/PDF at reports/course-project/variance-explanation-m was
rendered and visually inspected. This can support a course explanation of why
the method is useful but its correction weight is domain-dependent. It does not
add a new performance win, clinical interpretation or unseen-backbone claim.
