# K4 eligibility-only preparation registration

Registered8 November2026 after K3's sampled public visual acceptance and before
reading original UCO ambiguity values or unified pair-reference fields. This
stage defines the population and exclusion audit; no prevalence or performance
evaluation is authorized here. No external-label tuning is allowed.

## Fixed inputs

- Original supplied-frame archive SHA256
  `a34f65a1f2d836bac8b748fcb458c6fe735f166128cd46248bd148bbf94611b2`.
- VSGaze archive SHA256
  `3bf42763c968b9684a3276e32b41403a43392282c67bdc8e461058ca949cb386`;
  UCO test HDF SHA256
  `3c3120ace0bb5f1be1e93673cbc1ef30e687d4db359d5748a0bfac88b3899a46`.
- Public table SHA256
  `7d5aba5fc7ef73b83dfe31f99a3094525c75645ef3ccaf9e12c3e37d1418281e`.
- Exactly15 official test clips in pinned J split metadata,2,366 mapped unified
  frame rows. Keep K2's original coordinates and frozen square/padding convention.

## Ordered implementation and allowed readout

1. Inspect original author parser and annotation-file schemas; safely access only
   selected test `annotations_frame` text files from the hashed archive. Verify
   the original frame-index column explicitly. Never assume row index equals
   frame index; zero-based filenames are already established by public mapping.
2. Read original frame codes solely to derive `ambiguous = (code == 9)` and
   validate allowed codes. Do not report positive/negative code frequencies or
   select clips based on them. Save an ignored Boolean mask keyed by clip/frame.
3. Access unified `pairs` and `laeo_pairs` with the existing restricted-array
   reader, validate lengths/ID mapping and allowed labels[-1,0,1], and separate
   binary/unknown eligibility. Never infer a negative pair from absent or unknown
   annotation. Remove zero-placeholder/invalid-ID/self pairs. Canonicalize
   unordered IDs; require duplicate directions to agree or fail rather than
   silently choose a value. Geometry is not repaired or used to choose outcomes.
4. Exclude every original ambiguous frame regardless of unified binary values.
   Record mask disagreement counts, absent original-frame codes, duplicate
   conflicts, unknown/placeholder exclusions and counts by clip. A missing code,
   frame-mapping ambiguity or conflicting duplicate is a failed gate requiring
   diagnosis/versioning, not automatic exclusion. Do not report class prevalence.
5. Export only a separate ignored oracle table and eligible public pair index.
   Record file hashes, exact N and four candidate budgets floor(.05/.10/.20/.40*N).
   No model score, fitted policy, positive count or reference mean is computed.
   Merely preparing an oracle does not authorize opening it for performance.
6. Write the final evaluation protocol before inference/results: freeze q and
   checkpoint/runtime hashes, ChildPlay-trained K4 cutpoints/residual moments,
   allocation/minimum rules, weight1 versus0.5 on identical queries, exact budgets,
   seeds, a new stream and all RMSE/coverage endpoints. No UCO validation training,
   test-label allocation tuning or favorable subset selection. Report all losses.

Output under new ignored `data/processed/uco-eligible-k4-v1` and
`outputs/uco-eligibility-k4-v1`; code/docs/aggregate eligibility evidence only in
Git. This is downstream dataset transfer within the backbone's VSGaze family,
not proof of unseen pretraining scenes, natural-video prevalence or ADHD validity.
