# External validation feasibility: I and the first J gate

8 November 2026. This review adds provenance evidence, not a performance gain.
The frozen course population, estimates, losses and comparisons remain intact.

## Local finding

No already available ChildPlay source currently qualifies as independent unseen
evidence. The metadata-only audit joins the original public source/split table,
both acquisition ledgers, frozen population and inference manifests. It never
opens new reference labels or media archive contents. Aggregate evidence is in
`research/i-local-feasibility.json`; the source-level ledger stays ignored in
`outputs/external-review-i-v1/source-ledger.json`.

| Membership | Train | Validation | Test | Total |
| --- | ---: | ---: | ---: | ---: |
| Original inventory | 68 | 6 | 21 | 95 |
| Frozen accepted population | 40 | 3 | 10 | 53 |
| Excluded | 28 | 3 | 11 | 42 |

The 42 exclusions comprise 20 frame-count alignment failures, one cadence
failure, one visual-alignment failure, 17 unavailable videos, two HTTP403
failures and one sign-in requirement. The first acquisition has 54 complete
archives; the quarantine review has 14. Fifteen excluded sources have existing
archives, with recorded sizes matching the files. Archive content hashes were
not recomputed in this availability check. All 53 accepted sources have cached
inference; one excluded source also has predictions. A cache does not establish
alignment or make a source eligible.

The original annotation-only inventory covers all 95 sources and already
contains label-only diagnostics. This establishes broad prior label-summary
exposure. It does not establish that every excluded source was individually
studied; that history is incomplete and cannot support a fresh-test claim.
The 15 existing excluded archives would require separate mapping/decode/visual
acceptance and still require disclosure of prior exposure. None is added back.

An additional check verified all 95 ledger rows, nine input hashes, actual
archive presence and 162 tracked hashes from seven prior evidence manifests.
No previous scientific file changed. See `research/i-independent-validation.json`.

## External candidates

| Candidate | Useful scope | Main requirements | Current decision |
| --- | --- | --- | --- |
| UCO-LAEO | ChildPlay-to-TV downstream audit-method transfer | Released aligned frames, head geometry, official split and new inference | Practical candidate; not a new backbone dataset family |
| AVA-LAEO | Audit prevalence in its selected annotated person-pairs | AVA person-key mapping, scene frames, head detection/tracks, temporal mapping and overlap audit | Annotation access works; input adapter remains substantial |
| TVHID-LAEO | Shot-level interaction assessment | Different estimand and shot/pair mapping | Not a drop-in pair-frame prevalence test |

UCO provides per-frame head boxes and pair labels. Its authors explicitly warn
that annotations align to supplied frames and may not align to video files.
Codes 1/2 are positive, 9 is uncertain, and the split is specified in
`code/uco_dbconfig.py`. Prefer their current extracted-frame release, not an
unverified re-decode. The official endpoint reports 4,066,161,261 compressed
bytes; no frames were downloaded in this review. A pinned release, safe
extraction, geometry checks, storage allowance and inference timing are needed.
[Author dataset documentation](https://github.com/AVAuco/ucolaeodb).

VSGaze includes ChildPlay, UCO-LAEO, VideoCoAtt, VideoAttentionTarget and
GazeFollow. Its normalized head/pair format may simplify an adapter; it is not
evidence of media alignment. [Official VSGaze release](https://zenodo.org/records/17357752).
The frozen MTGS checkpoint is trained on VSGaze and its card specifies
CC BY-NC 4.0. Thus UCO transfer can test our downstream estimator/allocation
recipe across datasets, with backbone-family exposure disclosed; it cannot be
described as wholly unseen pretraining data. A dataset-family list alone also
does not prove whether a particular test scene was in model training.
[Checkpoint card](https://huggingface.co/Idiap/mtgs-vsgaze/blob/main/README.md).

AVA-LAEO annotates a subset of AVA v2.2 train/validation frames selected using
person-watching actions. It has sparse, one-second anchor times and ambiguous
cases. This selection changes the target population: a result describes its
annotated eligible pairs, not prevalence throughout movies. TVHID's LAEO
annotations are at shot level. [Author paper, dataset section](https://arxiv.org/html/2101.02136#S4).
AVA-LAEO is not listed among VSGaze's constituent datasets; that alone proves
neither scene independence nor absence from broad backbone pretraining. Check
movie/source identifiers and shared content before making an independence claim.

## Actual access and schema checks

The author project links an AVA-LAEO annotation archive. The HEAD request and
bounded download both succeeded. It is 1,351,919 bytes, SHA256
`6de0e373bd92d676de259430fb376e384fff800d18a6f94a188a95a38c921881`.
It contains two CSV files (train and validation), one author parser, and a
directory entry. Only member metadata and the small parser were read; neither
CSV's label outcomes were inspected. [Author download page](https://www.robots.ox.ac.uk/~vgg/research/laeonet/main_cvpr2019.html).

The parser documents a row index, movie ID, timestamp, two human IDs and LAEO
label, joining human IDs against AVA v2.2 annotation column 7 to obtain body
boxes. It is illustrative code, including an apparent loop syntax typo; it was
not executed. Body boxes must not be relabeled as head boxes. Full-scene frames
and valid head/person correspondence are required for the existing temporal
MTGS model. Generic AVA action labels are not substitutes for LAEO references.
[Official AVA annotations](https://sites.research.google/gr/ava/download/).

The newer LAEO-Net++ code links preprocessed train/validation crops (3.58 GB and
940 MB) and tracks (624 MB). A web fetch of the validation SharePoint link
redirected to Microsoft sign-in; these assets were not acquired. They are not
required merely to inspect the public original annotation archive, and cropped
head pairs alone do not establish our full-scene input contract.
[Author training instructions](https://github.com/AVAuco/laeonetplus/blob/main/doc/training.md).

The public download descriptions do not establish a blanket redistribution
license for underlying TV/movie media. Keep any acquired material local, use
the original research access route, retain attribution and inspect release terms
before media acquisition. A model/code license does not license third-party
films. Exact media rights and source overlap remain unresolved gates, not a
claim that the annotation archive is inaccessible.

## Next bounded work

The registered [J metadata/alignment gate](EXTERNAL_METADATA_J.md) has completed
its initial HEAD and AVA archive-member steps. Next inspect official UCO split
and geometry loader documentation, compare that contract with the pinned MTGS
loader and prepared public-input schema, and estimate storage/inference work.
Prefer a clearly labeled downstream UCO transfer over claiming AVA independence
without head/scene alignment. If UCO is viable, register its exact population,
hashes, eligibility, budgets, seeds and frozen comparisons before outcomes.
No external reference analysis, model fit or GPU job has begun.
