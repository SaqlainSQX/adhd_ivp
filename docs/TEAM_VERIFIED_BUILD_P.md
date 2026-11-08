# Verified aggregate build: teammate addendum

Use the additive `codex/aggregate-integrity-p-v1` review branch. The original
N/O builder and reproduction evidence remain preserved. To rebuild the existing
appendix with integrity validation that stays active under optimized Python:

```powershell
python -I -S scripts/build_verified_transfer_appendix.py
```

This explicitly checks the same three aggregate source checksums against the
existing manifests before creating data.json/data.js. It uses only the standard
library plus the repository's staged package path; no datasets, scientific
packages, prediction caches or model weights are needed. Intact output hashes
match the original appendix after line-ending normalization.

Then serve the existing appendix with the standard-library server described in
TEAM_QUICKSTART.md, or use the already running8768 service. No second server is
needed. The live page was not rebuilt or modified during the P tests: all tests
ran on separate staged copies.

To repeat the repaired six-case check in a new output folder:

```powershell
python scripts/check_aggregate_integrity.py verified --output outputs/aggregate-integrity-p-repeat
```

It tests intact, missing and numerically changed source files under normal and
optimized isolated/no-site Python. Both intact builds must match, and changed
or missing inputs must fail without exports. Use a new output name each time;
evidence is never overwritten. The baseline bypass and registered repair are
documented in AGGREGATE_INTEGRITY_P_RESULTS.md.

This concerns stale/changed aggregate validation, not adversarial security or
scientific novelty. The browser-download capture limitation is unchanged; use
the verified JSON endpoint if a portable file is needed. Full vision runs need
the separately obtained raw data and pinned inference environment.
