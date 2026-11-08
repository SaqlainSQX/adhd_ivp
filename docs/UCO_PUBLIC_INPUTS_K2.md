# K2 public-input mapping registration

Registered8 November2026 after K1 integrity/member inspection, before public
mapping outcomes or any UCO performance readout. Frozen archive SHA256:
`a34f65a1f2d836bac8b748fcb458c6fe735f166128cd46248bd148bbf94611b2`.
K1 checked22,879 safe members with no links/special/traversal entries. Supplied
README describes v1.1 as aligned to extracted frames; annotation README says
frame code9 is ambiguous and must not enter evaluation. This rule must be
reconciled with VSGaze's unknown mask before any performance registration.

Use only the15 official test clips in pinned J metadata. Safely extract their
JPEGs under a new `data/processed/uco-public-k2-v1/images/<clip>/<six digits>.jpg`.
Limit selected extraction to8 GiB and total archive plus extraction to20 GiB.
Only fixed regular JPEG member names matching the selected clips are allowed;
copy bytes manually, never use archive.extractall or execute supplied code.

Read the checksum-pinned VSGaze test HDF with the existing array-only unpickler.
Its object table jointly stores labels and public fields, so deserialization
loads that mixed container into memory. Access/export only path, person_ids and
head_bboxes; do not access, summarize, print or export social/gaze label fields.
Do not describe this step as zero label bytes deserialized. It is public-input
preparation with no outcome inspection, not a blind binary-label evaluation.

Candidate mapping: take the final clip/file components of each public path,
lowercase clip names, retain the exact six-digit frame index without offsets.
Require all2366 table rows to map uniquely to supplied images in the15 clips.
Do not repair a mismatch by searching offsets or choosing favorable labels.
Record missing paths and stop acceptance until a versioned repair is registered.
Validate decoded dimensions, normalized non-placeholder head box coordinates,
person/box lengths and duplicate IDs without accessing reference columns.

Preserve all supplied images in each test clip for temporal context. At the
next gate, select first/last and three evenly spaced public frame indices per
clip for head-box contact sheets. Inspect all15 clips visually. Check person-ID
correspondence across temporal neighbors; per-frame head order is not tracking.
Inference remains blocked until these mapping/identity gates pass and an exact
external evaluation protocol is registered. No GPU/Kaggle work or new model fit.

Outputs: ignored data/processed/uco-public-k2-v1 and
outputs/uco-public-k2-v1. Keep raw media and public per-person/source records
local; commit only code, registration and aggregate acceptance/failure evidence.
