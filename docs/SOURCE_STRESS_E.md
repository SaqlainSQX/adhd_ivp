# Registered source sensitivity E

8 November 2026, after round-D outcomes and before this diagnostic. Authorized
by the user's instruction to continue. This is a frozen-policy robustness
analysis, not another learner/grid, an independent test, or source cross-validation.

Question: does the D1 power-score improvement depend on particular test sources?
Use the accepted D run and no new queries. Compare K4/lambda1 with the locked
power-score/lambda0.5 on identical queried records. Keep all ten sources and
all original budgets516/1032/2063/4126, each1,000 saved draws. No refit,
allocation change, weight selection, source exclusion or result replacement.

For each source domain and each leave-one-source-out domain use its known
public size N_D and fixed public surrogate total Q_D. Estimate
`[lambda*Q_D + sum_h(N_h/n_h)*sum_sample_h I_D*(y-lambda*q)]/N_D`.
Keep original N_h/n_h weights, even when no queried record lies in the domain.
Do not renormalize by realized domain queries. This domain estimator remains
design-unbiased. FPC variance uses the stratum variance of `I_D*(y-lambda*q)`
including zeros outside the domain, scaled by N_h^2/N_D^2.

This follows standard design-based domain estimation using known domain sizes;
see [Brus, Spatial Sampling with R, chapter14](https://dickbrus.github.io/SpatialSamplingwithR/SmallAreaEstimation.html).
Our indicator-weighted residual adaptation is an engineering application, not
a claim to that source's additional small-area modeling procedures.

Primary: all ten leave-one-source-out RMSE ratios at B1032, mean/worst ratio,
number with ratio<1 and ratio<=.9. Also per-source ratios, absolute errors,
bias and MAE. Secondary: other budgets, realized domain label counts, normal
coverage/width and exact design RMSE using full labels for evaluation only.
Paired draw-bootstrap2,000 seed400005; fixed-corpus Monte Carlo interpretation,
not source-generalization confidence. Do not hide zero-positive or small-source
cases. Zero baseline RMSE: report explicit zero/undefined status without division.
No multiple-comparison or confirmatory claim. No required positive threshold.

Save all per-draw outputs locally, aggregate source aliases/counts/metrics in Git,
and raw source alias mapping locally. Check domain/source sums and leave-out
complements against the saved full-population estimates for every draw. Verify
all queries/hashes, reproduce scalar domain estimates independently, compare
sample variance and exact design variance against an exhaustive synthetic test,
and visually inspect figures. No GPU/Kaggle work. Stop launching additional
research at the existing timer checkpoint; finish verification of in-flight work.
