# K3 visual and temporal geometry review

8 November2026. No UCO reference fields or model predictions were inspected.
Code and aggregate evidence are on `codex/uco-visual-k3-v1`.

## Observed visual evidence

The assistant visually inspected all three locally generated2100×1300 contact
sheets: five clips per sheet, five frames per clip,75 panels total. Selection
used first/last and three evenly spaced indices in the sorted public annotation
rows, as registered in K2. Raw sheets remain ignored/local; no media enters Git.

- got05/got06: two main head boxes remain on the same visible people; got06 has
  a head near the top border.
- got08: foreground people and small/background detections align; background
  auxiliary IDs change as detections enter/leave, without reassigning the main IDs.
- mr04/mr05: close and partly overlapping heads remain boxed consistently.
- mr06/mr10: two main heads track the visible people; small peripheral detections
  are present and are not evidence of fully annotated identity ground truth.
- sv03: two main people remain consistent; small background IDs vary.
- sv06: the two main people stay aligned through movement.
- sv10: three people remain boxed as the camera/heads move near image borders.
- twd03/twd04: two main foreground people remain consistent, with additional
  small background detections.
- twd05/twd06: people enter/leave and occlude each other; visible identities and
  IDs are consistent in the sampled panels, including new foreground heads.
- twd07: two main head boxes stay aligned throughout the sampled frames.

This is sampled visual acceptance, not proof that every frame/identity is perfect.
No new physical-person identities were inferred or names recorded.

## Geometry convention and screen

The actual pinned `square_bbox` implementation preserves box center, takes the
maximum of width/height and returns a square. Despite its docstring's recentering
description, the function body does not clamp/recenter to the image. Our existing
runtime uses PIL.crop on that square. A local synthetic check confirmed black
padding for out-of-image pixels. Thus the360 strictly out-of-[0,1] rows are
retained as supplied, with the unchanged frozen crop convention; none is dropped
or clamped. All boxes remain finite and nondegenerate. This resolves the strict
bounds flag for input preparation, not a claim of perfect head annotation.

A public-only diagnostic compared same-ID head-box IoU at positive offsets3/6.
It flagged an alternative ID only if its IoU exceeded0.5 and was at least0.2
above same-ID IoU. There were10,757 comparisons, zero such flags and456 missing
positive-offset frame neighbors. This geometric screen was coded before its
readout; it is a heuristic, not labeled identity verification. A fast crossing,
large motion or repeated erroneous IDs could escape it. Missing annotations and
new/disappearing IDs must continue to use the frozen missing-context behavior;
the existence of a JPEG alone does not supply a head track.

The public spatial mapping and sampled temporal screen are accepted for the
next eligibility-preparation gate. Any later demonstrated mapping error must
trigger a new version; do not overwrite K2/K3 evidence. Do not tune parameters
or drop difficult frames after inspecting external evaluation outcomes.

## Next

Run [UCO_ELIGIBILITY_K4.md](UCO_ELIGIBILITY_K4.md): original ambiguous-frame versus
unified unknown-mask reconciliation and public pair eligibility. Freeze exact
population and budgets before a separate performance protocol. No inference,
fitting, score comparison, positive prevalence or performance gain is reported.
The old main result, losses and all source-sensitivity limitations remain intact.
