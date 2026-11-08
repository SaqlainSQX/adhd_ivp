# K1 completion and K2 public-input gate

8 November2026, branch `codex/uco-archive-k2-v1`. K1's complete download is
4,066,161,261 bytes with SHA256
`a34f65a1f2d836bac8b748fcb458c6fe735f166128cd46248bd148bbf94611b2`.
The downloader exited successfully; no second download or GPU job was started.
The archive hash was independently recomputed before member inspection.

The complete member scan found22,879 entries,22,741 regular files and22,436
JPEGs. No traversal, absolute/drive paths, links or special-file entries were
found. Only two README documents were read; no original label files were opened.
The release README states v1.1 updated annotations to match extracted frames.
The annotation README excludes ambiguous frame code9 and treats occlusion code2
as positive. The future reference protocol must reconcile those semantics with
the unified release; do not silently count ambiguous frames as negative.

No additional redistribution permission is stated in the package README. Keep
the research download/media local, retain source attribution and do not commit
or publish frames. No package code has been executed.

K2 is registered in UCO_PUBLIC_INPUTS_K2.md. Member metadata independently implies
3,009 JPEGs /646,552,910 bytes in the15 official test clips. All supplied images
are retained for possible temporal context, while the unified test table has
2,366 rows. Different counts alone do not establish a mapping failure: missing
annotations and unknown-label eligibility must be audited separately.

The preparation script accesses only path, person IDs and head boxes from the
existing restricted-array reader. Mixed HDF object records are necessarily
deserialized together; social/gaze reference fields are not accessed or reported.
Do not claim zero label bytes entered memory. Mapping and geometry checks are
saved in outputs/uco-public-k2-v1/result.json once the process finishes. If no
result exists yet, inspect the actual process before starting anything else.

The run has now finished: all2,366 rows mapped uniquely with zero missing
paths;3,009 JPEGs /646,552,910 bytes were extracted and all mapped images
decoded/verified. The strict normalized-bounds check flagged360 rows. A separate
public-only diagnosis found179 rows with a coordinate below0 and193 above1
(overlapping categories); zero nonfinite or degenerate rows. Coordinate range
was[-0.094551,1.064910]. No geometry was repaired and no rows were dropped.
Border-extending head crops may be legitimate, but acceptance requires checking
the supplied boxes visually and the pinned runtime's square/crop semantics.
Do not call the geometry gate passed solely because filenames match.

Remaining gates: inspect deterministic head-box contact sheets for all15 clips,
check ID correspondence across context frames, register any mapping repair under
a new version if needed, then freeze the external evaluation population,
ambiguous-label mask, label budgets, RNG stream and comparisons before outcomes.
No inference or new performance claim is accepted at this stage. Preserve all
existing gains/losses and keep the10-minute standing prompt active.
