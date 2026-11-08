# O: raw-data-independent appendix reproduction

Next bounded reproducibility task after N. This is an engineering check, not a
new numerical result or another parameter search. The team should be able to
rebuild the aggregate transfer appendix without credentials, raw datasets,
prediction caches, model weights, GPU libraries or old local output folders.

Stage a new source-only tree under outputs/team-reproduction-o-v1 using an exact
allowlist of tracked appendix/builder/module files and their pinned aggregate
sources/manifests. Record source commit and hashes before the check. Do not
delete or move user files or change the current checkout. Omit data/, outputs/,
external/, checkpoints/ and environments from the staged tree. No network or
GitHub private data access is needed.

Run the builder using a standard-library-only Python path where practical
(`-S` skips site packages; explicitly point to the staged src directory).
Inspect package initialization first; do not accidentally import the installed
working tree. Verify that both JSON/JS products exactly reproduce the pinned
aggregate artifact after normalized newline handling, including every loss and
provenance checksum. Confirm the staged tree has no oracle/model/raw-media
directory and that missing/tampered source evidence is rejected. Do not claim
a fresh dependency installation or cross-platform reproduction unless tested.

Save a small teammate quickstart and the exact scoped reproduction evidence.
If a missing import/bootstrap assumption is found, fix it additively and rerun
under a new version, preserving the failure. Keep the N in-app download-capture
limitation explicit; do not invoke the known-hanging download helpers. The
read-only JSON endpoint is the verified export route. Preserve existing services.

When finished, choose a bounded reliability/reproducibility task or a separately
registered meaningful scientific question. Do not retune weights or choose
favorable sources on the repeatedly inspected ChildPlay/UCO test populations.
Keep the10-minute continuation active until the user stops it.
