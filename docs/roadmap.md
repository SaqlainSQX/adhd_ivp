# Implementation roadmap

These are repository work items, not assignments to named teammates. Choose one
owner per item and use a feature branch plus review. Methodology decisions are in
[methodology.md](methodology.md). All research-result tasks below are pending.

| ID | Task | Depends on | Acceptance condition |
| --- | --- | --- | --- |
| M0 | Four-pass method review | supplied deck | Completed: four recorded passes and consolidated protocol |
| D1 | Archive inventory and eligibility adapter | access to annotations | Reproduces or reconciles supplied counts, rejects conflicts, logs exclusions |
| D2 | Source/subject/session manifests | D1 | Stable source-group splits and known exposure/overlap documented |
| P1 | Pin MTGS checkpoint and output variant | checkpoint choice | Code/config/weights hashed; hidden annotation fields excluded |
| P2 | Media/track alignment and cache exporter | D2,P1,media access | Visual sample inspection and full ID/time checks; failed alignments counted |
| S1 | Verified frame/block sampling and estimation | D1 | Enumeration tests for unbiasedness, variance, census, positive inclusion and costs |
| S2 | Static and temporal frame features | P2 | Same base predictions and learner; context has no hidden labels |
| S3 | Factorial scoring and allocation | S1,S2 | Four matched static/temporal by frame/block variants |
| S4 | Conservative interval and rare-event audit | S1 | Bound derivation checked, exhaustive small-case tests, approximate/formal outputs distinct |
| B1 | Minimum baseline suite | S1,S4 | Human-only, residual-uniform, entropy, static-risk, calibrated model and tuned weight |
| B2 | Strong statistical comparators | B1 | StratPPI, ASI, Robust ASI and CPS checked against author implementations/assumptions |
| E1 | Lock experiment | D2,S3,S4,B1 | Config, access history, development costs, seeds and primary comparison versioned |
| E2 | Exploratory benchmark | E1 | 1,000 draws per budget, all failure/coverage/cost metrics and ablations |
| E3 | Untouched-source confirmation | E2,new sources | Policy frozen before access, compatible target and no hidden evaluation tuning |
| C1 | Annotation-time pilot | media and annotator access | Randomized tasks, observed setup/decision time and reliability measurements |
| R1 | Contribution assessment and report | E2; E3/C1 for related claims | Claims match observed evidence; negative outcomes retained |

The existing code partially exercises S1 and a block-only learning pipeline with
synthetic data. It does not complete D1–R1. In particular its train/validation/test
directory naming is a software contract, not an approved source partition.

Recommended parallel team workstreams once the method is accepted: data/provenance,
predictor/cache, sampling/statistics, feature/ablation experiments, baseline
replication, annotation cost/reliability, and reproducibility/reporting. Coordinate
interfaces before dividing implementation.
