# Q v2: clean-control interval reference repair

Registered8 November2026 after v1 stopped in the eta0 gate, before any nonzero
noise outcome. Preserve outputs/query-noise-q-v1 and its original implementation.
The exhaustive24-case toy check passed. Point/variance and normal bounds matched
clean baselines. The only interval mismatch was1,000 missing ChildPlay uniform
M2 endpoint fields: the main study saved binary intervals on M1 only.

The original frame_study.py runs M1/M2 on the same uniform query file. The main
uniform-b1032 query SHA and D's power-uniform-b1032 SHA are both
`8b0082959b8da96165e1b108e1c11eb29be5bb59e120e5ae4c56c7512925323e`.
The v2 must verify exact saved selection-array equality and equal per-draw
queried positive counts before taking binary endpoints from M1. Continue to use
M2's point/variance/normal bounds as the clean uniform difference control.
Reference-only binary intervals depend on the queried labels/design, not phi.

No method, population, rate, seed, query, budget or endpoint changes. Create a
separate run_query_noise_v2.py and configs/query-noise-q-v2.json, new output
outputs/query-noise-q-v2. Record the extra main query file/manifest hashes.
Repeat all six eta0 controls before any nonzero corruption. Any other mismatch
fails the gate. Original reference tables/results remain immutable.
