# U: training-only control-variate coefficients

Registered after T outcomes and before calculating any U coefficients or results.
This is a bounded exploratory method extension, motivated by M's variance identity.
It is not a new theorem or independent test: ChildPlay and UCO results have already
been inspected. No UCO/reference-test labels may fit or select coefficients.

Use the existing ChildPlay static feature CSV, eligible training split only,
joined one-to-one by record_id to the frozen oracle. Require the registered
training population to match191956 eligible rows and40 training sources; if that
contract fails, diagnose publicly and register a repair before fitting. Reuse
the frozen D K4 cuts and exact query designs. No new cache/inference/GPU work.

The extension uses fixed stratum-specific prediction phi_i=lambda_h*q_i. Fit
lambda_h=clip(Cov_train,h(y,q)/Var_train,h(q),0,1), with centered sums and no
ddof difference in the ratio. If a stratum has fewer than2 training records or
q sum-of-squares<=1e-12, use lambda_h=0. The prespecified global-coefficient
ablation fits that same ratio on all eligible training rows and clips to[0,1].
Do not search regularization, shrinkage, cut points or weights using outcomes.
Record stratum counts, centered sums and source hashes before test evaluation.

Compare four fixed coefficients on identical existing K4 queries: full1, D's
half0.5, global training fit, stratum-specific training fit. All use the existing
frozen K4 allocation, budgets, source population and prediction q. Full/half
must exactly reproduce accepted D/L point, variance and interval controls.
No validation or test labels select between these four reporting arms. Training
labels are an additional cost; do not call this annotation-free or total-cost
matched against a method without training data.

Evaluate ChildPlay budgets516/1032/2063/4126 and UCO260/521/1043/2087,1000 saved
draws each. Pin all input hashes, query hashes, streams and these settings in a
new U config before fitting. Reuse each design's exact saved selections rather
than resampling. Primary: stratum-specific/full RMSE ratio on ChildPlay1032 and
UCO521; secondary: stratum-specific/half and global/full plus all four methods'
bias, RMSE, normal95% coverage/width and exact design variance. Keep all32 cells,
including every loss/tie. Exact binary reference intervals are unchanged by phi;
do not imply they validate the new residual-based normal intervals.

For ratios use paired draw bootstrap2000 resamples with default_rng SeedSequence
([820000+dataset_code*100+budget_index,1,93]), dataset codes1 ChildPlay/2 UCO and
budget_index0..3. Ratios quantify fixed-corpus Monte Carlo uncertainty, not
source generalization. Validate the piecewise-phi estimator on small synthetic
finite populations first; independently verify the fitted coefficients from
centered cross-products, every32000 draw calculation, exact variance and the
registered bootstrap endpoints. Visually inspect any figure. No extra model,
weight selection or tuning after outcomes. Preserve failed stages versioned.

The coefficients minimize training residual variance within the fixed groups;
transfer mismatch can still produce a loss. Report as a simple course-project
extension. Do not replace the locked main study or use the already inspected
test labels to choose the final headline method.
