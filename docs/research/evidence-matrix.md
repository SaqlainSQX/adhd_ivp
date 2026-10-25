# Evidence matrix for the idea assessment

Checked 25 October 2026. This is a targeted critical review, not a systematic review
with exhaustive database coverage. Primary papers, author repositories and official
dataset releases support the conclusions. Search-result summaries from third-party
paper services were discovery leads only, not evidence.

Reading depth below distinguishes detailed method checks from narrower abstract
screening. The overlap assessments are our interpretation, not statements by the
original authors about this project. Published gains are not transferable effect
sizes for our dataset.

| ID | Primary source | Evidence inspected | Relevance and limit |
| --- | --- | --- | --- |
| G1 | [MTGS, NeurIPS 2024](https://www.idiap.ch/~odobez/publications/GuptaTafascaFarkhondehVuillecardOdobez-NEURIPS-2024-MTGazeSocial.pdf) | §3.3, §4, supplement B/C and Table 4; [author code](https://github.com/idiap/MTGS) | Frozen social-gaze predictor exists. Native LAEO is min of directional learned LAH scores. ChildPlay-specific LAEO F1 is substantially below the pooled score; F1 does not identify prevalence bias or residual variance |
| G2 | [ChildPlay, ICCV 2023](https://publications.idiap.ch/downloads/papers/2023/Tafasca_ICCV_2023.pdf) | §3 collection/annotation/statistics; [official release](https://zenodo.org/records/8252535) | Dense gaze and adult/child labels; curated clips and partial-person annotations limit population interpretation. Annotation-only release does not establish present media availability |
| G3 | [VSGaze official release](https://zenodo.org/records/17357752) | Schema, checksum and direct scan of ChildPlay train/val/test HDF5 tables | Independently confirms counts and source split; does not verify video alignment, identity independence or model exposure |
| G4 | [Deng et al., AGT/SACF, AAAI 2026](https://ojs.aaai.org/index.php/AAAI/article/view/41177) | Primary abstract and paper details inspected during earlier methodology review | Motivates rare face-directed gaze in an autism dataset. Its gaze-target/face endpoint cannot validate our mutual-looking endpoint |
| G5 | [Yankowitz et al., J Psychiatric Research 2026](https://pubmed.ncbi.nlm.nih.gov/42161147/) and [author manuscript](https://pmc.ncbi.nlm.nih.gov/articles/PMC13248665/) | Abstract; indexed full-text annotation, detector, features and limitations sections | Already automatically quantifies dyadic social gaze and mutual-gaze proportion in autism. Authors distinguish social gaze from eye-specific contact; new independent sample and eye-tracking validation remain relevant. No general first-automatic-autism-gaze claim is available to us |
| S1 | [Prediction-powered inference, Science 2023](https://pubmed.ncbi.nlm.nih.gov/37943906/) | Primary abstract and paper exposition | Prediction-assisted correction and statistical inference are established; this is background rather than project novelty |
| S2 | [PPI++, arXiv:2311.01453](https://arxiv.org/abs/2311.01453) | Abstract and relationship to the inspected finite-sample analysis S7 | Predictor weighting is an existing efficiency refinement; abstract wording should not be read as a blanket finite-sample guarantee |
| S3 | [ASI, ICML 2024](https://proceedings.mlr.press/v235/zrnic24a.html) | Problem/estimator reviewed with Robust ASI §1.2–2 | Error-guided sampling plus inverse-probability correction is prior work. Its acquisition objective is inference, distinct from improving a detector by active learning |
| S4 | [StratPPI, NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/file/c9fcd02e6445c7dfbad6986abee53d0d-Paper-Conference.pdf) | Introduction, sampling/allocation and variance setup | Learned strata and optimized labeling allocation do not establish a new method by themselves. Adapt its original population setting explicitly to finite video corpora |
| S5 | [Robust ASI, arXiv:2511.08991v1](https://arxiv.org/html/2511.08991v1) | §1.2–2 and Theorem 1 | Uniform/active interpolation and robust optimization already exist. The no-worse comparison is asymptotic with stated consistency conditions, not a guarantee for our validation-selected mixture |
| S6 | [Fixed-Size ASI, arXiv:2610.27389v1](https://arxiv.org/html/2610.27389v1) | §3.1–3.2 and theoretical framing | Conditional Poisson sampling removes random query count for equal-cost units. Correct marginal inclusion probabilities and computational setup matter. Does not automatically impose fixed label cost on unequal-size blocks |
| S7 | [No Free Lunch, arXiv:2505.20178v1](https://arxiv.org/html/2505.20178v1) | Introduction and finite-sample results | Tuning predictor weights can cost efficiency with scarce labels. Supports checking finite-sample performance rather than importing an asymptotic slogan |
| S8 | [Imberg et al., Active Sampling, Technometrics](https://arxiv.org/html/2212.10024v3) | §3–4 and method framing | ML-assisted finite-population sampling, adaptive importance sampling and variance estimation substantially predate our proposal |
| S9 | [Kossen et al., Active Testing, ICML 2021](https://proceedings.mlr.press/v139/kossen21a.html) | Primary abstract and supplementary sampling/cost discussion | Testing labels are a known budget problem; risk-estimation methods need explicit adaptation to estimating label prevalence |
| S10 | [Conformal PPI, arXiv:2510.16166v1](https://arxiv.org/html/2510.16166v1) | Method scope and temporal risk-monitoring application | Broad “first temporal PPI” wording is unsupportable; sequential monitoring is not identical to our fixed-corpus target |
| S11 | [PPITSAS, arXiv:2610.08715v1](https://arxiv.org/html/2610.08715v1) | Introduction, target and HAC framing | Addresses temporal mean inference across space; its future/long-run mean differs from design-based inference on fixed records |
| Q1 | [BlazeIt, PVLDB 2019](https://people.eecs.berkeley.edu/~matei/papers/2020/vldb_blazeit.pdf) | §6 control variates, stopping and sample-complexity discussion | Video aggregation using predictions and selectively evaluated expensive references already exists. Its oracle is usually a detector; replacing it with a human does not create generic estimator novelty |
| Q2 | [ABae, PVLDB 2021](https://www.vldb.org/pvldb/vol14/p2341-kang.pdf) | §2.3–3.1 query formalism and two-stage algorithm | Proxy-defined strata, pilot labels and variance-based allocation are close prior work. The paper explicitly permits human labelers as oracles. Its predicate-conditioned average is not always our unconditional label mean |
| Q3 | [InQuest, PVLDB 2023](https://www.vldb.org/pvldb/vol16/p2897-russo.pdf) | §2–4, defensive allocation and temporal updating | Video/text stream aggregation with proxy-guided allocation and uniform defensive sampling predates the project. Offline and streaming assumptions differ |
| Q4 | [Seiden, PVLDB 2023](https://www.vldb.org/pvldb/vol16/p2289-kakkar.pdf) | §1, temporal propagation/acquisition and related work | Temporal continuity plus adaptive oracle calls for aggregate queries is already studied. Do not assume its propagation answers have our design-unbiased guarantee |
| C1 | [Yang et al., arXiv:2503.00815v1](https://arxiv.org/html/2503.00815v1) | Abstract, study design and batch-size question | Sampling efficiency versus wall-clock batching is studied outside gaze. Supports a cost-measurement study; weakens claims that the general tradeoff is new |
| Q5 | [González et al., DMKD 2024](https://link.springer.com/article/10.1007/s10618-024-01014-1) | Quantification definition, ACC and shift assumptions | Label prevalence estimation has an established quantification literature. Historical confusion correction relies on shift assumptions unlike fresh target-label randomization |

Additional search leads, not decisive evidence: [Transfer Calibrated PPI](https://arxiv.org/abs/2609.34156),
[multi-task PPI](https://arxiv.org/abs/2605.29249),
[active-testing benchmark in NLP](https://arxiv.org/abs/2603.21840), and
[nonuniform-sampling PPI](https://arxiv.org/abs/2501.18577).
These need deeper comparison if the project expands into adaptation, multiple
endpoints, or sequential querying.

## Search coverage and limitations

Search families included mutual gaze/eye contact with prevalence, sampling and
quantification; prediction-powered inference with video/time series; active testing
and finite-population inference; approximate video aggregation and expensive
oracles; ChildPlay/VSGaze/MTGS; and automatic naturalistic social-gaze measurement
in autism. References in the database papers led to the main overlooked overlap.

Some primary pages returned a timeout, a large-PDF limit, or a browser challenge.
The author-hosted MTGS PDF and indexed primary manuscript sections supplied the
needed evidence. The original Science/PPI++ references were screened more narrowly
than the closest method papers. No paywall was bypassed. Absence of an identical
gaze-specific audit paper in these searches does not establish novelty.

Our initial four-pass review omitted Q1–Q4 and G5. The deep review therefore lowers
the novelty assessment and corrects the native MTGS score description. It preserves
the usefulness of a tightly controlled applied measurement study.
