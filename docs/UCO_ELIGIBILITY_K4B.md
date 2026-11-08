# K4b: original annotation index normalization

Registered8 November2026 after K4v1 failed its missing-original-index gate,
before the repaired ambiguity/pair eligibility readout. Preserve v1's failure,
partial Boolean mask, index diagnosis and implementation snapshot. No population
or performance result from v1 is accepted.

Evidence: all15 original frame files use consecutive first-column ordinals1..N;
supplied image filenames and unified paths are zero-based. The pinned author
`parseFileLAEOframe` ignores the first column and returns the second column in
row order; its demo indexes that returned vector directly by the JPEG's frame
number. Therefore JPEG frame f corresponds to original ordinal f+1 (row f).
This is a metadata/schema correction, not an offset chosen using label values
or model performance. Exact-match v1 missed frame0 in the applicable clips.

The repaired v2 must assert every original first-column sequence is exactly1..N
before mapping `original_ordinal - 1` to the zero-based frame key. Keep original
JPEG/unified frame names and head boxes unchanged. Assert every unified row maps.
Report extra original ambiguity rows beyond supplied images, without inventing
images or modifying the unified population. Got06 has262 original ordinals but
261 supplied images; this difference is disclosed and must not trigger an
arbitrary resynchronization. Any nonconsecutive index or further mismatch stops
the gate for separate diagnosis.

All K4 rules remain: code9 excludes frames, unknown pairs never become negative,
duplicate directions must agree, and no class prevalence or model performance
is computed. New outputs: data/processed/uco-eligible-k4-v2 and
outputs/uco-eligibility-k4-v2. Implement in a separate v2 script, preserving v1.
