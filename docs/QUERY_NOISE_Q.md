# Q: synthetic query-reference error sensitivity

Registered8 November2026 before any noisy-label outcomes. This is an exploratory
stress test on already inspected finite populations, not new held-out evidence,
measured annotator accuracy or a new method/weight search. Keep all original
references, score caches, query streams, results and losses immutable.

## Question and background

Can imperfect queried references erase the precision benefit of the frozen audit
estimators? Prediction-powered inference combines predictions with trusted
reference data; correcting prediction error does not by itself establish that
erroneous queried labels are gold-standard observations. The original paper
provides background, not a new theorem for this finite-population noise model.
[Angelopoulos et al., Science2023, author copy](https://www.stat.ubc.ca/~john/papers/AngelopoulosScience2023.pdf).

Use the benchmark labels as synthetic clean truth only for this controlled test.
Do not claim they are error-free human measurements. The corruption rates below
are chosen stress settings, not estimates of real annotation error.

## Fixed populations, methods and budgets

ChildPlay D:10,316 pair-frames at1,032 labels; UCO L:5,219 at521 labels. These are
the existing primary10% endpoints. No other budgets or subsets are selected.
Methods: uniform difference with prediction q, frozen K4 full weight, and the
same frozen K4 queries with0.5q. Use D K4/power-score files and D power-uniform's
uniform query file with prediction q; verify this reproduces the original main
M2 control at eta0. For UCO, use the saved L K4/uniform files. Keep all frozen
counts, source order, allocation moments and predictor settings unchanged.

Use1,000 existing draws. Eta values are exactly0,0.01,0.02,0.05, each flipping
queried binary labels symmetrically. For dataset code1=ChildPlay,2=UCO, draw d,
generate N uniforms with default_rng(SeedSequence([800000+d,1,dataset_code,91])).
The same record-indexed uniforms apply across methods/rates; flip when U<eta.
Shared K4 queries therefore receive identical noisy labels at either weight;
rates are nested, while different draws receive fresh independent error vectors.
Generate/persist noise-seed registration and frozen source/query hashes before
the noisy readout. Never corrupt the saved reference table itself.

Total24,000 method/rate draws:6,000 eta0 controls and18,000 synthetic noisy cases.
No new queried record is added; each method retains exactly its old label budget.
Errors are independent random observation flips, not systematic or correlated
annotator behavior. No flip rate is fitted and no ideal known-noise correction
is added as an unregistered competitor.

## Endpoints and checks

Primary: signed bias against the original reference mean at eta0.02 for full-weight
K4 on both corpora, compared with its eta0 result and analytical expectation.
Secondary: every fixed method/rate's bias, RMSE, normal95% coverage/width, and
naive binary-reference interval coverage for the clean target. Label the latter
explicitly: the old exact algorithm is not guaranteed for clean truth under
these corrupted observations. Conditional on a fixed corrupted population it
targets that corrupted mean, which differs from our clean target.

Independently verify eta0 point/variance/interval outputs against saved clean
results before interpreting any nonzero rate. Verify noisy RNG/costs and every
point/variance calculation. For fixed phi=lambda*q, symmetric independent flips
imply expected bias eta*(1-2*mu) and joint sampling/noise variance

`sum_h f_h Var_h((1-2 eta)y - phi) + eta(1-eta) sum_h (Nh/N)^2 / nh`,

where f_h=(Nh/N)^2*(1-nh/Nh)/nh and sample variances use ddof1. The independent
observation-noise term has no finite-population correction. Verify this derived
identity by exhaustive enumeration on a fixed small synthetic population before
running corpus outcomes; it is not taken from the PPI paper. Compare Monte Carlo
means/MSE with analytical quantities without choosing a different rate or seed.

Save all cells and failures, hashes, independent validation and a standalone
figure under a new Q output. Do not tune weights, train models, estimate real
annotator noise, infer diagnosis or replace the locked main submission. This
tests an accuracy assumption of the audit, not a claim of improved performance.
