# Pass 1: scientific and statistical validity

Reviewed 25 October 2026. Input: the supplied 32-slide SRS/design deck. This is a
review of a proposal; archive counts, media alignment, and experimental gains have
not been independently reproduced in this workspace.

## Assessment

The useful problem is measuring an aggregate rate from imperfect video predictions
and a limited number of reference labels. The deck already correctly distinguishes
this from training a gaze detector. Its main weaknesses are the sampling target,
cost assumptions, and interval reliability.

| Issue in the proposed design | Revision | Reason |
| --- | --- | --- |
| Title suggests clinical eye contact in autism | Primary target is benchmark-defined mutual looking on eligible ChildPlay pair-frames | Head-box gaze labels do not validate eye-to-eye contact or a clinical construct |
| Binary-known subset can look like the entire corpus | Define the eligible population and publish unknown-label exclusions | Random sampling cannot remove selection bias from missing reference labels |
| Pair-frame prevalence can sound like time prevalence | Define the denominator explicitly | Multiple pairs in crowded frames receive more weight |
| Squared aggregate residual is used to justify stratified allocation | Separate Poisson second-moment targeting from fixed-size centered-variance allocation | These designs optimize different variance expressions |
| Temporal blocks appear intrinsically better | Make single-frame queries with temporal features the primary comparator | Adjacent labels can be redundant at equal label cost |
| Uniform/active mixture sounds robust by theorem | Call it validation-selected interpolation | Robust ASI's guarantees do not automatically transfer to a heuristic mixture |
| Two samples per stratum appear sufficient for a CI | Retain as a variance-computability minimum only | Sparse positive observations can produce severely optimistic normal intervals |
| Repeated draws could imply independent experimental replications | Distinguish design repetitions from new-source replications | More seeds do not create more videos |

## Statistical check

For fixed blocks and fixed predictions, stratified simple random sampling without
replacement gives an unbiased residual-corrected total with weights N_h/n_h.
The standard finite-population variance formula uses centered block residual
variance S_h², not their uncentered second moment. Temporal dependence among fixed
records does not itself invalidate this randomization-based result. It does matter
for learning transferable scores and for inference about future videos.

Under independent Poisson inclusion, the variance instead contains
sum_b (1-pi_b)e_b²/pi_b. A squared-residual predictor fits that objective, but
Poisson and stratified SRS results must not be interchanged.

## Decision after this pass

Keep the frozen predictor and difference estimator. Treat block sampling as an
experimental factor, make the eligible target explicit, and separate exact point
estimation claims from approximate normal-interval claims. The next pass must
establish what remains beyond existing inference methods.

Sources: [VSGaze schema](https://www2.idiap.ch/en/dataset/vsgaze),
[MTGS paper](https://papers.nips.cc/paper_files/paper/2024/file/1caf09c9f4e6b0150b06a07e77f2710c-Paper-Conference.pdf),
[Robust ASI, §1.2–2](https://arxiv.org/html/2511.08991v1),
[StratPPI](https://proceedings.neurips.cc/paper_files/paper/2024/file/c9fcd02e6445c7dfbad6986abee53d0d-Paper-Conference.pdf).
