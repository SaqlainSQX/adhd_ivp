# K4 eligibility acceptance and L handoff

8 November2026. v1 stopped on a missing original index; its failure, partial
mask, original script snapshot and metadata diagnosis are preserved. All original
frame-file ordinals were1..N while JPEG/unified indices were zero-based. The
author loader ignores those ordinals and indexes row-order labels by JPEG frame.
The separately registered K4b repair maps original ordinal minus one, changes
no media frames, and exports to new v2 folders.

Accepted v2 has5,219 eligible pairs from2,366 unified frames across15 test clips.
The gate removed12,262 placeholder/invalid directed rows, collapsed5,701 duplicate
directions without conflict and retained482 unknown canonical pairs as exclusions.
No mapped unified frame is original-code9 ambiguous, so there are zero binary
pair/ambiguity disagreements in this mapped subset. This does not assert that
the entire original release has no ambiguous frames.

All3,010 original rows map by the documented ordinal convention. Got06 has one
extra original code beyond the261 supplied JPEGs; no unified row references it.
No original code is missing for a unified frame. All5,219 private oracle entries
were independently recomputed and compared without summing class labels or
reporting positive counts/prevalence. Four candidate budgets, verified using
integer division, are260/521/1043/2087. Hashes are in the aggregate result.

No score, trained UCO policy, reference mean, GPU job or performance comparison
has been produced. The new [L protocol](UCO_TRANSFER_L.md) freezes the downstream
comparison, inputs, budgets, streams and endpoints before inference/results.
Next implement its public inference adapter/CPU preparation, inspect actual
GPU/process availability, and then compute the frozen score cache if resources
permit. No Kaggle account access or another agent's workload modification.

Both preparation scripts pass Ruff after formatting long lines. The v1 snapshot
saved before formatting is hashed locally; formatting changed no logic. K2/K3
evidence and the locked main study remain unchanged. Keep the10-minute prompt
active and advance the registered queue; a completed gate is not a new gain.
