# R: directional query-label error sensitivity

Registered after Q outcomes; exploratory assumption check, not confirmation or
an improved method. Q's independent symmetric flips are an artificial assumption.
For a rare positive outcome, false-positive and false-negative errors can have
very different consequences. This bounded follow-up separates those mechanisms.

Reuse exactly Q v2's two populations, source hashes, six method/design cases,
1000 existing queries each, primary budgets1032 and521, weights1/0.5, and no
model fitting. Q is not rerun or replaced. Before outcomes, create an R config
pinning Q's config, result, query hashes and this protocol.

Three settings only: (a,b)=(0,0), (0.02,0), (0,0.02), where a is the probability
of flipping reference0 to1 and b of flipping reference1 to0. These are artificial
class-conditional rates, not matched total corruption rates or estimates of
human accuracy. Equal queried label budgets across methods remain required.
No sweep, selected optimum, extra model or ideal correction competitor.

For dataset codes ChildPlay1/UCO2 and draw d=0..999 use NumPy default_rng with
SeedSequence([810000+d,1,dataset_code,92]). Draw N record-indexed uniforms shared
across methods and the three settings. For reference y, flip if U<a when y=0,
or U<b when y=1. Full/half K4 share identical queries and noisy observations.

Primary endpoint: full K4 signed bias for each directional setting on both
corpora. Expected bias is a*(1-mu)-b*mu; no correction is applied. Secondary:
all methods' RMSE, normal95% clean-target coverage/width, mean queried flips,
and naive exact-binary clean-target coverage/width, explicitly without a clean
truth guarantee. Save all18000 method/setting/draw cases, including6000 clean
controls. Do not use outcomes to change methods, weights, rates or seeds.

Let m_i=a+(1-a-b)*y_i and v_i=a*(1-a) for y_i=0 or b*(1-b) for y_i=1.
Joint sampling/error variance is
sum_h (Nh/N)^2 * [(1-nh/Nh)*Var_h(m-phi)/nh + mean_h(v)/nh].
The second term has no finite-population correction. Verify this identity by
exhaustively enumerating the same Q four-record toy population, all possible
queries/errors and census cases before corpus outcomes. Reproduce all eta0
Q clean controls, then independently replay all18000 outcomes/RNG/exact integer
intervals and summary cells. Inspect standalone figures visually. Preserve any
failed stage under versioned output roots and register repairs before restart.

Interpret directional asymmetry only within this simulation. Benchmark labels
are the simulation reference, not verified error-free human truth. There is no
new held-out test, human annotation reliability estimate, causal claim, diagnosis
or universal robustness claim. No GPU/Kaggle work. Stop this bounded stage after
the prescribed cells; subsequent work needs a distinct registered question.
