# J: UCO contract review

Completed metadata review on 8 November 2026. See
`docs/research/j-uco-contract.json` for pinned hashes and measurements.

The pinned author split file defines eight validation and15 test clips with no
overlap. We parsed literal lists through Python AST, never imported downloaded
code. [Official split configuration](https://github.com/AVAuco/ucolaeodb/blob/83392d99519a48432e5b34a70e0cfa0fe93895cf/code/uco_dbconfig.py).

The supplied-frame demo uses lowercase clip names and six-digit JPEG frame
names. Its pair references are one-indexed head positions. Those positions are
not a guarantee of temporal identity. [Official demo](https://github.com/AVAuco/ucolaeodb/blob/83392d99519a48432e5b34a70e0cfa0fe93895cf/code/ucolaeo_demo.py).

The locally pinned VSGaze UCO HDF metadata reports17,451 train,1,658 validation
and2,366 test rows. Each has path, normalized head boxes, person IDs and social
pair fields. Only HDF column names/row counts were read: no object pickle was
deserialized, reference values read or class proportions computed.

The pinned MTGS loader expects `root/images_Idiap/<annotation path>`, temporal
offsets[-6,-3,0,3,6] under its default stride/context, and correspondence by
person IDs. Missing temporal frames are padded. It converts normalized head
boxes using image dimensions. This establishes an adapter contract, not proof
that the original supplied-frame archive already has that layout or identity
mapping. The existing project ChildPlay path parser is dataset-specific and
must not be reused unchanged for UCO.

The official current archive is about4.07 GB compressed. Free disk observed was
134,237,487,104 bytes. Historical ChildPlay inference rates were3.886–6.159
anchor frames/second: applying those to2,366 anchors gives a **6.4–10.1 minute
forecast**, excluding loading, mapping, differences in head counts and hardware
contention. It is not a UCO speed measurement or permission to use a busy GPU.

The author README provides research download/citation instructions and warns to
use the supplied aligned frames. It does not establish a general license to
redistribute underlying media. Acquisition stays local through the original
research route; package terms and geometry must be checked before evaluation.

Next is the registered [K1 acquisition](UCO_ACQUISITION_K.md). No UCO labels,
scores, predictions, fits or evaluation results have been inspected. Existing
performance evidence remains unchanged. The10-minute continuation was found
paused at the user's request to restart it; the app update returned ACTIVE and
the saved config independently confirmed a10-minute interval. Do not pause it
when a stage ends.

Validation: author commit and four source-file hashes pinned; split counts and
disjointness asserted; three HDF tables hashed and metadata read only. Ruff
reported one long line initially; formatting was corrected and the check passed.
No statistical result required revision. Runtime files stay in
`outputs/uco-contract-j-v1`; author code is not committed or executed.
