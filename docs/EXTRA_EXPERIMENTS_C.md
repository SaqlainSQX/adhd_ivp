# Registered exploratory round C

Registered 7 November 2026 following the user's explicit request for additional
results. This round follows the prespecified X02/X03 questions. The test corpus
has already been inspected repeatedly: every outcome is exploratory, with no
independent-confirmation or general-novelty claim. Keep every method, budget,
failure, loss and tie in the aggregate appendix. The current course submission
and frozen main comparison remain available without these extensions.

## Frozen inputs and common protocol

Use the same verified-population-v2, cached MTGS scores and eligible
191,956 / 25,139 / 10,316 training/validation/test pair-frames. No new media,
GPU inference, backbone fitting or Kaggle work is required. The exact hashes
are pinned in `configs/extra-experiments-c-v1.json`: main evaluation/policy lock,
B1 simple-control result/policy lock and original source-fold assignments.
Refuse changed input hashes and preserve all original artifacts.

All methods use the existing residual difference estimator, the same four
exact test label budgets 516/1032/2063/4126, 1,000 draws per policy/budget,
original normal and bounded intervals, and the previously checked exact
stratified binary reference interval. The latter ignores q and may be centered
differently from the residual estimate; report point-outside-reference rates.

For each new policy, choose allocation alpha from {0,0.5,1} using 100 validation
draws at 10% (2,514 labels). Minimum validation MSE; within 1% prefer smaller
alpha. Save all candidate query plans before validation references are retrieved.
Freeze model/feature/cut/SD hashes and selected alpha before any new test queries.
Use a fixed selected alpha across all test budgets. Save every test plan before
test reference access. No evaluation outcome selects a new main winner.

Use SeedSequence([100000+draw,1,stream]) for validation and
SeedSequence([200000+draw,budget_index,stream]) for test, budget index 0..3.
Registered streams: Ridge-static 11, Ridge-temporal-w11 12, squared-RF-static 13,
squared-RF-temporal-w11 14; every C2 training-label fraction uses stream 15 to
share the same random-number recipe under its different frozen allocation.
Use 2,000 aligned-draw bootstrap resamples with seed 400003. These intervals
summarize Monte Carlo uncertainty on the fixed corpus; method streams differ.

## C1: signed-residual Ridge, static and temporal

Use StandardScaler followed by Ridge(alpha=1, fit_intercept=True,
solver='cholesky'); one CPU/BLAS thread. Fit scaling inside each training fold,
never on held-out fold, validation or test. The target is signed residual y-q.
Use exactly the original five training-source folds. Form quartile cuts from
OOF predictions and centered signed-residual SDs with the original variance
prior count 20 and SD floor 1e-6. Fit the final pipeline on all training rows.

Compare static public features with the already selected window-11 temporal
features. No new windows, regularization values, feature subsets or threshold
search. Freeze both final policies separately; validate alpha separately.
Primary comparisons at B=1,032: Ridge-static/M3 and Ridge-temporal/M4, and each
versus the frozen B1 score-quartile control. Retain all four budget curves.

[Official Ridge documentation](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html)
and [StandardScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html)
were checked against the installed scikit-learn 1.9.1 parameters.

## C2: development-label cost of score-quartile allocation

Reuse the frozen B1 public-score cut points. For training label fractions
1%,5%,20%,100%, estimate the centered residual moments using only the sampled
training labels, with the same prior-count-20 shrinkage toward that sampled
training set's global residual variance. This is moment calibration, not a
new learned error model. No test data choose cut points or moment estimates.

Create a deterministic random permutation independently within each original
training source after sorting its record IDs. Use SeedSequence([710000,h]),
where h is the unsigned integer given by the first eight hexadecimal digits of
SHA256(source_id UTF-8). For each fraction take the first
max(1,floor(fraction*N_source+0.5)) records. Fractions are nested. Save the exact
selected IDs and source counts before retrieving their labels. Return selected
rows to the original frozen row order before moment calculations. Assert that
the 100% cuts/SDs reproduce the B1 full-training policy within 1e-12.

Select alpha separately on validation under the common protocol and evaluate
all four fractions at all test budgets. Primary endpoints at B=1,032:
RMSE(fraction)/RMSE(100%) and actual training labels used; secondary endpoints
coverage/width, failure flags, full-budget curves and total reused development
labels (sampled training count plus 25,139 validation labels).

This is masking of an already available benchmark, not a measured purchase
of fewer labels. Public scores for all training rows remain available. Validation
labels remain fully reused, so this is not a cold-start annotation-free result.
The C2 100% stream-15 evaluation is a new Monte Carlo replay on the same corpus,
not independent replication of B1's stream-7 result. Do not overwrite B1.

## C3: squared-residual Random Forest score, static and temporal

Use the original RandomForestRegressor settings: 64 trees, maximum depth 4,
minimum leaf size 100, seed 42, n_jobs=1. Change only the score-learning target
to (y-q)^2. Compare static with fixed window-11 features, using the same five
training-source folds and final full-training fitting.

Define cuts from OOF squared-residual predictions. For allocation SDs, still
estimate **centered signed residual y-q variance** within OOF score strata;
do not substitute RMS error or predicted squared error directly as the SD.
Use the same shrinkage, alpha selection, budgets, seeds and exact query policy
as the other methods. Primary comparisons at B=1,032: squared-RF-static/M3,
squared-RF-temporal/M4, and each versus frozen score quartiles. Retain all losses.

## Outputs, acceptance and stopping

Run order: C1, C2, C3, independent recomputation, aggregate figures/report,
GitHub synchronization. Total new test evaluations: 32,000 (8,000 C1 + 16,000 C2
+ 8,000 C3), plus 2,400 validation selection evaluations. Keep per-stage logs,
progress, package/source hashes, elapsed CPU time, model locks and query arrays.
Do not duplicate active jobs. Any failed run gets a new versioned output folder.

Report bias/MAE/RMSE in pp, exact label counts, failure/zero-positive/zero-variance
rates and coverage/width for all intervals. Independently replay every RNG
stream, recompute points/finite-population variances/RMSEs and interval summaries.
Inspect exported figures visually. Raw data/labels, query arrays, models and
environments remain excluded from Git; track code/config/docs/aggregate evidence.

A prespecified practical signal is at least a 10% primary RMSE reduction versus
the frozen score control, or a C2 reduced-label policy within 10% of its full-label
reference while using fewer training labels. These are descriptive practical
thresholds, not a grading requirement or a test for new-source superiority.
Do not select a lucky seed or suppress failures to cross them. No multiplicity-
adjusted scientific discovery claim is planned across these exploratory comparisons.

Stop after this registered queue regardless of outcomes. If improvements are
uncertain or absent, retain the existing course narrative and report these
checks as limitations/appendix evidence. Further variants require a separate,
explicitly registered round rather than continuing a search after these results.
