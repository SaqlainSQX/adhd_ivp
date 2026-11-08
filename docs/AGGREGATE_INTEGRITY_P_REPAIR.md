# P repair registration: explicit aggregate validation

Registered8 November2026 after baseline P's six staged cases and before repair
outcomes. Preserve outputs/aggregate-integrity-p-v1. Normal Python rejected
the copied numerical change, but `-I -S -O` exported the changed value because
N's checksum condition uses assert. Neither live sources nor scientific outcomes
were changed. Intact and missing-source cases behaved as expected in both modes.

Add src/gaze_audit/verified_transfer_appendix.py and a separate
scripts/build_verified_transfer_appendix.py entry point. The new validator must
check the same three source hashes against the same existing tracked manifests
with explicit if/raise conditions, before producing any artifact. Reuse N's
existing projection only after those checks. Keep N/O modules, builder, exports
and evidence manifests unchanged; this is an additive entry point, not a rewrite.

Use the original P harness, same copied numerical change and six fixed cases,
with --phase verified and new output outputs/aggregate-integrity-p-v2. Register
new source and repair-protocol hashes before each case. Both intact builds must
reproduce accepted JSON/JS hashes after newline normalization; both modes must
reject missing and numerically changed sources without generating either export.
No unrelated schema/dependency changes, network, model, oracle or GPU work.

On success, provide a new teammate addendum recommending the verified entry
point. Preserve the baseline bypass and explicitly retain the scope: accidental
stale/changed evidence validation under tested interpreter modes, not an
adversarial security audit or a fresh scientific result.
