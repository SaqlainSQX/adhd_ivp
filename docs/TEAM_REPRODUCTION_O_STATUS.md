# O source-only reproduction accepted

8 November2026, branch `codex/team-repro-o-v1`. The staged source baseline was
commit `b8a08212b477f75da625f8364f55a341f6ba80d2`. Creating the additive review
branch changed no source contents or checked-out commit. Input hashes and the
three cases were recorded before execution. No previous output was overwritten.

The13 tracked inputs include the appendix module, package initializer, builder,
server, static UI and exactly the three aggregate sources/manifests needed by
the builder. They omit root data/, outputs/, external/, checkpoints/ and both
environments. Package initialization was inspected and needs no scientific stack.

The success case ran with Python `-I -S`, an explicitly staged src path, no
inherited PYTHONPATH/PYTHONHOME, and a staged module-origin assertion. The child
confirmed isolated/no-site flags, no site/numpy/pandas/torch/sklearn imports and
matching aggregate JSON/JS checksums after normalized line endings. Its observed
staged file opens were recorded, including harmless generated Python bytecode.
No dataset, prediction cache, oracle or model file was supplied in that tree.

Two separate controlled negative trees also behaved as registered: appending
whitespace to a pinned source failed the hash assertion; omitting the UCO source
failed with FileNotFoundError. Neither generated data.json/data.js exports.
These expected failures test evidence validation, not statistical performance.

Reproduction SHA256 after CRLF-to-LF normalization:

- data.json: `79551273633b365c28714493d0270b8a305cd387f5d7e9576bc20e008aef9dac`
- data.js: `4708088df448a86a30f90b6a3ed9605437bd0ad449261aafcef643cb17b71bd2`

The scoped check used the existing Python3.13 interpreter, not a freshly
installed runtime. No Linux/macOS test, new dependency installation or full
vision-experiment reproduction is claimed. The N browser-download capture
limitation is unchanged; the HTTP JSON export remains verified.

Runtime originals: outputs/team-reproduction-o-v1 (registration, result,
success/tampered/missing trees and logs). Tracked aggregate proof is under
docs/research/o-*. Ruff passed for the new standalone helper. Existing83-test
coverage remains intact; no production module changed, so the same regression
suite was not repeated. No GPU, Kaggle, network acquisition or new query was used.

See TEAM_QUICKSTART.md. The next bounded reliability check is registered in
AGGREGATE_INTEGRITY_P.md; do not use the inspected ChildPlay/UCO outcomes to
restart a weight/model search. Keep the10-minute continuation active.
