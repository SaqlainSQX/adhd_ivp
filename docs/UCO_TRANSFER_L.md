# L: frozen downstream UCO transfer comparison

Registered8 November2026 after K4b eligibility acceptance and before UCO model
scores, prevalence or evaluation outcomes. This is an exploratory downstream
dataset-transfer study; it does not replace the locked ChildPlay study or prove
unseen backbone pretraining. UCO belongs to the checkpoint's VSGaze family.

## Population and inputs

Exactly5,219 eligible unordered person-pair frames across15 official test clips.
The public index and separate private oracle are in
data/processed/uco-eligible-k4-v2. Their SHA256 values, public geometry, trained
policy and runtime hashes are frozen in configs/uco-transfer-l-v1.json.
Use eligible CSV row order as the immutable population order. The index mapping
repair is original ordinal minus one, documented in UCO_ELIGIBILITY_K4B.md.
Unknown pairs never become negatives; original ambiguous frames are excluded.
No further exclusions, UCO training or validation fitting are allowed. A missing
score or demonstrated alignment error fails the run and requires new versioned
evidence, never silent denominator shrinkage.

## Inference and public preprocessing

Use the existing hash-pinned released temporal MTGS-DINO checkpoint, MTGS and
DINO commits,448 scene/224 head resizing, stored mean/std and offsets[-6,-3,0,3,6].
No augmentation or model fitting. Native q is min of the two directional sigmoid
LAH scores, not the model LAEO output. Use float16 autocast as in the accepted
cached ChildPlay inference; inference differences must be measured/disclosed.
Use only public paths, person IDs and head boxes as inference inputs.

Use the K2 mapped2366 public frames for temporal person correspondence, with
the existing runtime's zero-padding for missing annotation neighbors or tracks.
A JPEG without head annotations does not become a known tracked frame. Retain
original UCO border-extending boxes before the pinned square_bbox/PIL crop.
This intentionally preserves the reviewed UCO annotation geometry. The original
ChildPlay export clipped boxes at its normalization stage: disclose this upstream
dataset-preparation difference, even though square/crop and model settings are
fixed. Do not claim byte-identical full preprocessing across datasets.

Inference is only a few thousand anchors. Inspect actual local GPU/process state
before optional GPU work; never interrupt or compete with another agent's active
GPU workload. Prefer existing local checkpoint and CPU preparation; do not start
new Kaggle jobs or change credentials. Save complete cached scores and hashes
before evaluation. No oracle opens for score generation or allocation selection.

## Frozen methods, budgets and streams

Three methods: uniform difference estimator with prediction q; K4 allocation
with prediction q (weight1); identical K4 queries/allocation with prediction0.5q.
Cutpoints and residual SDs are copied unchanged from the saved ChildPlay
K4-training.json. No UCO residual-moment fitting. Use alpha1 allocation and the
existing allocate_counts minimum min(Nh,20), stable remainder ties, census caps,
SD floor1e-6. Omit empty strata without changing cuts. A failed budget gate stops.

Exact budgets **260,521,1043,2087**, corresponding to the K4/J-registered floor
rule for5/10/20/40%. Do not call integer_budget, whose round-to-nearest behavior
was used in the main study. Every method uses the same exact budget at each
external endpoint. No label-time or contiguous-query efficiency claim is made.

1,000 draws/method/budget. RNG is NumPy default_rng with
SeedSequence([200000+draw,budget_index,stream]); draw0..999, budget_index0..3.
K4 weights1/0.5 share stream61 and precisely the same queries; uniform uses62.
Generate and hash every query file using public scores/frozen settings before
opening oracle values for evaluation. Sample each stratum without replacement
in increasing present-stratum order with existing save_queries semantics.

## Endpoints and validation

Primary: RMSE ratio K4-weight0.5/K4-weight1 at budget521. Target improvement is
at least10% (ratio<=0.9); always report the observed ratio, including losses/ties.
Paired bootstrap2,000 resamples of the1,000 draw indices, percentile95% interval,
seed500000+budget_index. These intervals characterize Monte Carlo draw variation
on this fixed population, not new-source or new-person generalization.

Secondary: RMSE/bias/MAE at every budget, K4/uniform comparisons, exact design
variance using all references only in evaluation, variance-estimator reliability,
normal95% coverage/width and the existing equal-Bonferroni exact binary reference
interval coverage/width. Point estimate is mean(phi)+sum_h Nh/N*mean(y-phi)_h;
variance is sum_h (Nh/N)^2*(1-nh/Nh)*s_h²/nh, zero for a census stratum. Normal
intervals remain diagnostics; do not select a preferred interval after outcomes.
Exact binary intervals estimate the population reference mean, not a residual
interval centered on the model. No unregistered weight/strata/model search.

Independently replay all12,000 method draws, verify exact unique-label costs,
point/variance calculations and reference intervals, plus shared K4 query hashes.
Save every loss/tie and any numerical failure. Inspect report figures visually.
Keep raw scores, images, references, model weights and per-query logs ignored;
sync code/docs/aggregate results only. No report of ADHD diagnosis or natural
all-video prevalence is supported by this benchmark.
