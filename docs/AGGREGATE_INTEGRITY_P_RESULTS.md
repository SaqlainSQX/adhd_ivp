# P: optimized-mode integrity issue demonstrated and repaired additively

8 November2026. Baseline source commit95b7154; branch
`codex/aggregate-integrity-p-v1`. No live data, old module, scientific result,
model or running service was changed. All tests used source-only copies.

The registered six-case baseline found that normal Python rejected a copied
numeric change, while optimized Python (`-I -S -O`) accepted it and exported
the doubled copied primary full-weight RMSE. The old checksum guard used assert,
which is omitted under that interpreter flag. Both intact outputs matched and
both missing-source cases failed. This is a demonstrated reliability issue in
that mode; it is not a new result about gaze estimation.

The baseline remains under outputs/aggregate-integrity-p-v1 with registration,
all six trees and logs. Nothing from those altered test copies was served or
committed as accepted scientific data.

After registering AGGREGATE_INTEGRITY_P_REPAIR.md, added a separate explicit
if/raise validator and build entry point. It validates all three pinned sources
before calling the old projection. N/O code and manifests are unchanged. The
same six cases were repeated under outputs/aggregate-integrity-p-v2:

| Interpreter | Intact source | Missing source | Numerical source change |
| --- | --- | --- | --- |
|Normal isolated/no-site|Identical accepted output|Rejected; no export|Rejected; no export|
|Optimized isolated/no-site|Identical accepted output|Rejected; no export|Rejected; no export|

All six repaired cases passed. Both accepted JSON/JS hashes match the original
N/O artifacts after CRLF-to-LF normalization; changed and missing sources never
generated either export. Source/protocol hashes were registered before each
phase. Ruff passed for all three new Python files. These are six end-to-end
repair controls, not a repeat of the unchanged83-test suite.

See TEAM_VERIFIED_BUILD_P.md for the new preferred build command. This scoped
check is not an adversarial security audit, a fresh dependency installation or
a cross-platform test. Users who edit code and manifests together remain
outside this accidental-staleness check. The browser export-capture limitation
is unchanged, while the HTTP payload remains verified.

Scientific claims and all losses/ties remain unchanged. The next registered
scientific robustness question is QUERY_NOISE_Q.md: synthetic query-label error
at fixed primary budgets, using the frozen caches/queries. No new model/weight
search, GPU work or human annotation-accuracy claim is implied.
