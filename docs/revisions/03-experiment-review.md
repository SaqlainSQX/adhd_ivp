# Pass 3: adversarial review of the experiment

Starting point: pass 2's proposed contribution is the effect of temporal context
independent of annotation batching. This pass asks how an apparently positive
result could be misleading.

## Failure scenarios and controls

| Apparent result | Alternative explanation | Required control |
| --- | --- | --- |
| Temporal sampler beats uniform | Any learned risk model would help | Static learned-risk sampler using the same learner and development labels |
| Blocks win | More labels were bought | Match expected revealed pair-frame labels and report realized distributions |
| Blocks save annotator time | A guessed cost function favors blocks | Timed pilot with randomized order and separate setup/per-label times |
| Temporal features help | Temporal method received extra context or geometry | Give the same unlabeled cache to all methods; ablate only scoring features |
| Risk forest generalizes | Source or person appears in both development and evaluation | Split original source videos before extracting clips; inspect subject/session overlap where IDs exist |
| Grouped risk cross-validation is clean | Frozen MTGS already trained on these same sources | Audit backbone exposure separately; grouped risk CV cannot repair predictor exposure |
| Tight intervals look good | Rare positives were missed | Report coverage, zero-positive draws, and a conservative interval benchmark |
| One thousand trials prove transfer | These trials reuse the same fixed labels | Use new sources/corpora as transfer replications |
| Five-frame batches are a temporal mechanism | Smoothing alone gave the benefit | Include moving-average score and label-order-shuffle diagnostics |
| Better error per test label proves savings | Development annotation was omitted | Plot existing-label reuse and total purchased-label regimes separately |
| New corpus improves performance | Budget or policy was retuned after looking at it | Freeze a versioned policy and log source/corpus access chronology |

## Revised factorial experiment

Cross two scoring feature sets with two query units: static/frame,
temporal/frame, static/block, temporal/block. Use identical base predictions and a
common stratified difference estimator. Compare context within a query unit first.
Compare query units under matched cost second. Do not interpret their effects as
one mechanism.

Temporal input windows may overlap because predictions are already available.
Queried label units must not overlap or be counted twice. Permuting prediction
order within a source-pair is a secondary diagnostic, not an assumption-free
causal test: it also changes transition features and their distribution.

Use frame queries as the primary experiment so n is an exact label count. Block
draws constrain expected pair-frame label count unless all costs are identical.
Never truncate an oversized random sample; that changes inclusion probabilities.

## Revised development protocol

Use source-separated error-fit and policy-selection sets, then lock evaluation.
Prefer development sources unseen during backbone fitting when enough are
available. If the released checkpoint saw the original training sources, do not
mistake its in-sample prediction errors for unseen-source errors. Keep that regime
explicit and run a held-out-development sensitivity analysis.

The deck discloses prior test-label inspection. Therefore the official ChildPlay
test analysis is exploratory for this project. Reserve an untouched source set or
additional corpus before making confirmatory claims. If none is available, retain
the exploratory designation in every result table.

Do not force VAT, UCO-LAEO, or AGT into a transfer test merely because they are
available. First verify a compatible mutual-looking endpoint, reference-label
construction, source separation, and checkpoint exposure. AGT face-directed gaze
is a different task; its paper supplies motivation, not endpoint validation.

## Decision after this pass

Make the factorial comparison the core experiment; add an explicit predictor
exposure audit, conservative intervals, total-cost reporting and confirmatory-data
gate. Pass 4 must turn these decisions into acceptance criteria rather than adding
more possible architectures.

Sources: [VSGaze schema](https://www2.idiap.ch/en/dataset/vsgaze),
[AGT/SACF primary paper](https://ojs.aaai.org/index.php/AAAI/article/download/41177/45138),
[finite-sample PPI analysis](https://arxiv.org/html/2505.20178v1),
[Fixed-Size ASI](https://arxiv.org/html/2610.27389v1).
