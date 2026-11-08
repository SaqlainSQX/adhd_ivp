# Team quickstart: aggregate transfer appendix

This path lets a teammate inspect the accepted course findings without
downloading ChildPlay/UCO, model weights or environments. It reproduces the
aggregate appendix, not the full computer-vision experiment.

## Open the checked-in appendix

With Git and Python available, fetch the repository and use the review branch
`codex/team-repro-o-v1`. The branch contains the earlier work as well; main is
still the locked course baseline. No merge or branch reset is required.

From the repository folder, run:

```powershell
python -I -S scripts/serve_transfer_appendix.py --port 8768
```

Open http://127.0.0.1:8768. If the local service is already running, use it
instead of starting a duplicate. The server uses Python's standard library
and a fixed aggregate-asset allowlist. No pip installation, model import,
Kaggle account or raw data is needed for this appendix.

The checked-in `demo/transfer/data.json` and `data.js` already contain the
project's frozen aggregates. Read TRANSFER_APPENDIX_N_GUIDE.md for a five-minute
presentation. All UCO budgets and the half-weight loss are included; the original
research explorer and earlier negative results remain separate and unchanged.

## Reproduce and check the aggregate build

```powershell
python scripts/reproduce_transfer_appendix.py
```

This creates `outputs/team-reproduction-o-v1` from a13-file tracked allowlist,
then runs the builder with `-I -S` using the staged src directory. It creates
three separate trees: normal reproduction, changed evidence and missing evidence.
The latter two must fail and produce no exports. The successful JSON and JS
outputs must match the registered aggregate checksums after newline normalization.

Reruns deliberately refuse to overwrite evidence. To repeat under a new name:

```powershell
python scripts/reproduce_transfer_appendix.py --output outputs/team-reproduction-o-v2
```

Read the saved registration, result and per-case logs. No existing files,
services or checkout contents are deleted or moved. Only the new output tree
is written. The helper requires Git to record the source commit and validate
the tracked-file allowlist.

## Scope and export

Verified on this Windows PC with Python3.13: isolated/no-site child execution,
staged module origin, no scientific/GPU imports, no raw/model directories,
byte-equivalent aggregate products after newline handling, and both negative
controls. This is not a fresh Python installation or a cross-platform test.
The explicit staged-src bootstrap is part of the verification; an arbitrary
uninstalled `python scripts/build_transfer_appendix.py` invocation is not claimed.

The JSON endpoint http://127.0.0.1:8768/data.json is the verified portable export.
The in-app browser's download-capture helper timed out; a physical browser
download remains unverified. View/save the JSON directly rather than repeating
that helper. Full experiment replay still requires separately obtained local
datasets, private reference tables and the pinned inference setup.
