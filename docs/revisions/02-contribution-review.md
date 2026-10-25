# Pass 2: prior work and contribution

This pass challenges the novelty remaining after pass 1. Literature checked on
25 October 2026. This is a targeted search, not proof that no related study exists.

## What is already established

| Prior work | Overlap with the deck | Consequence |
| --- | --- | --- |
| MTGS, NeurIPS 2024 | Temporal multi-person social-gaze prediction | A frozen backbone is a component, not our detector invention |
| ASI, ICML 2024 | Prediction-assisted selective label collection | Uncertainty-driven querying and inverse weighting are prior work |
| StratPPI, NeurIPS 2024 | Stratification and allocation for prediction-assisted estimates | A few learned strata plus correction are insufficient as a new-method claim |
| Robust ASI, NeurIPS 2025 | Interpolation with uniform sampling and robust optimization | A tuned mixture must not be named Robust ASI |
| Conformal PPI, arXiv:2510.16166v1 | Inference extensions including temporal risk monitoring | Broad claims of being the first temporal PPI are untenable |
| PPITSAS, arXiv:2610.08715v1, 6 October 2026 | Time-series mean inference with dependence-aware uncertainty | Distinguish finite-corpus randomization from long-run future-mean inference |
| Fixed-Size ASI, arXiv:2610.27389v1, 19 October 2026 | Conditional Poisson sampling for prediction-assisted inference | Fixed query count is also prior work and deserves a strong comparator |

The last two references postdate or are close to the deck's 17 October inventory.
They materially change the positioning. Their relevance was checked in the primary
papers; do not describe them as clinical gaze methods.

## Revised contribution candidate

**A reproducible study of when temporal context helps select reference labels for
rare mutual-looking prevalence, disentangling context from annotation batching.**

The key comparison holds the predictor, available prediction context, inference
estimator, development labels, and annotation budget constant. It changes whether
the risk score sees neighboring predictions and whether a query requests one
pair-frame or a contiguous block.

This yields an actionable scientific question: do correlated model errors make
temporal context informative, while correlated labels make batches inefficient?
The answer may identify different preferred query units under label-count and
annotation-time budgets. Neither outcome is assumed.

## Claims we can work toward

1. A versioned gaze-audit benchmark with explicit eligibility, source splits,
   predictor provenance, oracle logs, and reproducible statistical comparisons.
2. Evidence isolating temporal context from the number and organization of queried
   labels, with negative results and sparse-event coverage failures retained.
3. A measured cost-versus-accuracy analysis if a timed annotation pilot is feasible.

The first is an engineering contribution. The second is the main research
contribution candidate. The third needs real timing observations. A depth-4 forest,
an estimator formula, or a list of combined papers alone is not sufficient novelty.

## Decision after this pass

Use a frame-first design and a controlled context-by-query-unit experiment. Add
fixed-size ASI to the literature and comparator plan. Position the project as a
measurement study unless experiments and a broader literature review establish a
distinct methodological advance. Pass 3 must make this comparison fair and falsifiable.

Primary sources:
[MTGS](https://github.com/idiap/MTGS),
[ASI](https://proceedings.mlr.press/v235/zrnic24a.html),
[StratPPI](https://proceedings.neurips.cc/paper_files/paper/2024/file/c9fcd02e6445c7dfbad6986abee53d0d-Paper-Conference.pdf),
[Robust ASI](https://arxiv.org/html/2511.08991v1),
[Conformal PPI](https://arxiv.org/html/2510.16166v1),
[PPITSAS](https://arxiv.org/html/2610.08715v1),
[Fixed-Size ASI](https://arxiv.org/html/2610.27389v1).
