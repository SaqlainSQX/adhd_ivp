# M: post-hoc explanation of the locked transfer loss

Registered8 November2026 after L outcomes. This is explicitly descriptive,
reference-using interpretation, not a new held-out performance experiment or
permission to tune a predictor after test inspection. Reuse frozen caches and
query designs; no new inference, model fit, query stream or weight search.

For the frozen full-weight K4 allocation at each existing budget in ChildPlay D
and UCO L, compute the finite-population quadratic
V(lambda)=A-2*lambda*B+lambda²*C, where A=sum_h f_h*Var(y),
B=sum_h f_h*Cov(y,q), C=sum_h f_h*Var(q),
f_h=(Nh/N)^2*(1-nh/Nh)/nh and within-stratum variances/covariances use ddof1.
Census strata contribute zero. Verify V(1) and V(0.5) against previously saved
exact design variances; diagnose any discrepancy before accepting the explanation.

Report A,B,C by stratum and their sums, the fixed-weight variance difference
V(0.5)-V(1)=B-0.75*C, and squared-error Monte Carlo versus exact-design ratios.
Use the existing four budgets only; include primary10% results for both corpora.
Do not select or evaluate an optimal lambda, fit new residual moments for a
policy, remove difficult sources, rerun a lucky RNG stream or advertise a new
performance gain. Explain algebra and observed variance components with a
standalone aggregate figure and candid limitations. This decomposition diagnoses
the finite populations; it does not prove a causal effect of prevalence, dataset
identity or backbone exposure. Keep the raw-box preparation difference disclosed.

If the interpretation is complete, the next useful task is to incorporate the
accepted UCO findings into a separate additive course/demo appendix, preserving
the immutable earlier explorer and its evidence. Keep the standing10-minute
research prompt active until the user stops it.
