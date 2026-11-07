# Registered course-project strengthening round

Registered 7 November 2026 after the completed main study and A1/A2, following
the user's request to strengthen the course project. This is an exploratory
extension on an already inspected test corpus. It does not replace the locked
main comparison or supply independent confirmation. Preserve every loss/tie.

## Scope and immutable prerequisites

Reuse `outputs/experiments/course-20261107-v1`, verified-population-v2 and its
frozen MTGS cache. Train/validation/test eligible counts remain
191,956 / 25,139 / 10,316. Main result SHA-256:
`b7dba06392233572b3d1a40a96d0c260f0a42d18d5827cbab35666e46a3aead9`.
Main policy-lock SHA-256:
`15dacc805bd3f1e525ac32ace89578d51c44016ead2e4b986ceafe06cc074c4e`.
Check hashes and completed independent validation before use. No further GPU
inference or backbone fitting is required. Use new, non-overwriting output roots.

## B1: simple score and entropy guidance

Question: does the learned static error policy improve on simpler score-based
stratification at the same target-label budget?

Two controls: `q-quartiles` using native f_q and `entropy-quartiles` using the
existing f_q_entropy. Compute quartile cuts from original training public features
only. Remove duplicate/trailing cuts and preserve equal-score ties; no test
distribution or labels select cut points. Estimate centered residual y-q SD per
training stratum with the same prior-count-20 global-variance shrinkage and 1e-6
floor used by the main policies. There is no fitted predictor and no OOF learner;
the stratum score is a fixed public feature. Historical training labels used to
estimate allocation moments remain a disclosed cost.

Select alpha from {0,0.5,1} separately for each control using 100 validation draws
at the primary 10% budget (2,514 labels). Minimum validation MSE; within 1% choose
the smaller alpha. Save all candidate queries before validation oracle access.
Use SeedSequence([100000+draw,1,stream]), streams 7 and 8 for q and entropy.
Freeze cuts, SDs, feature names, candidates, selected alphas and policy hashes
before any new test query. Use the same fixed alpha at every test budget.

Evaluate 1,000 draws at each of B=516,1032,2063,4126, with exact bounded
allocations and the unchanged residual estimator/intervals. Seeds are
SeedSequence([200000+draw,budget_index,stream]), index 0..3, streams 7/8 as above.
Save all test plans before test oracle access. Total: 8,000 control evaluations.
Independently replay RNG and recompute every point, variance and RMSE.

Primary endpoints at B=1,032: RMSE(M3)/RMSE(q-quartiles) and
RMSE(M3)/RMSE(entropy-quartiles). Report also each control versus M2 and M4,
all four budget curves, bias/MAE, coverage/width, failures, zero-positive and
zero-variance rates. Bootstrap aligned draw IDs 2,000 times, seed 400002; the
interval describes Monte Carlo uncertainty on the fixed corpus. Different
method streams are not identical queries. Do not select a new main winner.

## B2: diagnose and probe interval undercoverage

Keep M3/M4 partitions, policies and alphas unchanged. Register the same four
budgets, with 1,000 fresh validation draws per policy/budget, using
SeedSequence([600000+draw,budget_index,stream]), streams 3 and 4. Save every
validation query plan before reading validation references.

For each method/budget derive a development-only multiplier c from
abs(p_hat-p_validation)/sqrt(V_hat). Sort 1,000 values; take one-based rank
min(1000,ceil(0.95*(1000+1)))=951, then c=max(1.959963984540054,selected value).
Zero-SE/exact estimates contribute zero; zero-SE/nonzero errors contribute
infinity and are explicitly reported. Freeze all eight c values and validation
diagnostics before computing new test diagnostics. This is an empirical
development-calibration probe, not a distribution-free coverage guarantee;
the validation corpus also participated in original policy selection.

On the existing 8,000 saved M3/M4 test draws (no new test-query selection), report:

1. Original normal and bounded intervals, retained unchanged.
2. Student-t intervals with Welch-Satterthwaite degrees of freedom:
   V_hat=sum_h v_h; df=V_hat^2/sum_h(v_h^2/(n_h-1)), ignoring census components;
   use t.ppf(0.975,df). Zero variance gives a point interval. This is approximate.
3. Development-calibrated intervals p_hat +/- c*sqrt(V_hat), raw/unclipped.
4. Evaluation-only normal intervals using exact design variance computed with
   all test residuals. These are diagnostic and unavailable to a real auditor.

Primary endpoints: M3/M4 coverage and mean width at B=1,032. Secondary: all
budgets, binomial Monte Carlo SE, effective df, mean/quantiles of V_hat relative
to exact variance, empirical sampling variance versus exact variance, and
standardized-error tails. Per stratum record population/counts, census status,
true residual variance, sampled-positive counts, zero-positive rates and variance
underestimation. Diagnostic full references must never influence policy or c.
Keep original undercoverage even if a wider interval improves coverage. Report
non-transfer or over-widening of validation calibration rather than tuning on test.

The generic approximation is documented by
[NIST](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/welchsat.htm);
quantiles use [SciPy's Student-t implementation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.t.html).
Neither source establishes exact coverage for this finite population.

## B3: presentation and demonstration

Build a local, CPU-only interactive results/audit explorer with method, budget and
saved draw controls, exact query replay, estimated prevalence and intervals, and
an example public score/query timeline. Display downloaded frames with supplied
head tracks when local media are present. Reveal only queried labels in the
demonstration; keep benchmark truth in a separate evaluation view. Clearly label
cached predictions, benchmark tracks and offline replay. Make no live-webcam,
new-inference, clinical, or measured human-time claim.

Provide a quick-start command, course presentation walkthrough, interpretation
of negative results and limitations, and a reproducibility/evidence manifest.
Check the interface in a browser and visually inspect all new report figures.
Sync code/docs/aggregate figures to the existing team repository; credentials,
raw media/labels, query arrays, weights and environments remain ignored.

## Completion and stopping

Order: B1 registration/implementation/checks, B1 evaluation; B2 validation lock,
B2 test diagnostics; figures/report; B3 functional and visual QA; GitHub sync.
Use durable status/logs and do not duplicate jobs. Stop this round after these
deliverables. X01, alternate learners, development-label learning curves and timed
human annotation remain deferred rather than expanding the search after outcomes.
