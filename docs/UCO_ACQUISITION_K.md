# K1: UCO supplied-frame acquisition and alignment prerequisites

Registered 8 November 2026 after J's metadata review and before any UCO reference
readout or model inference. This stage downloads media only. No new score,
prevalence, performance comparison, parameter fit or label summary is authorized
by this acquisition registration.

## Fixed acquisition

- Author repository commit: `83392d99519a48432e5b34a70e0cfa0fe93895cf`.
- Use its original supplied-frame release:
  `http://rabinf24.uco.es/ucolaeo/ucolaeodb_v1.1.tgz`.
- Expected compressed bytes from the successful J HEAD: **4,066,161,261**;
  Last-Modified **Tue, 06 Apr 2021 14:59:08 GMT**. A mismatch stops the stage.
- New ignored destination: `data/raw/uco/acquisition-k-v1/ucolaeodb_v1.1.tgz.part`;
  completed file retains the same name with `.part` removed. No old input is
  overwritten. Compute and record SHA256 before trusting archive contents.
- Use curl with HTTP failure checking, at most three retries, 20-second connect
  timeout and a one-hour per-invocation wall limit. Resume only this exact file;
  require matching remote byte size and Last-Modified before each invocation.
  Curl must reject a resume if the server does not support it. Never launch a
  second downloader while one is running.
- Require at least 24 GiB free space before acquisition; compressed download
  plus later selected-frame extraction is capped at 20 GiB total. Observed free
  space at J: about134 GB. Do not allocate model/GPU/Kaggle resources here.
- Use the author research download route and retain attribution. No raw media,
  original annotations or author code enters Git or a hosted demo. No blanket
  media redistribution license is inferred from a model/code license. Inspect
  package README/terms as the next gate; obey any additional access restrictions
  before use. No browser cookies, login workarounds or third-party mirrors.

## After a complete, hashed download

1. Safely list archive members without extraction. Reject path traversal,
   absolute/drive paths, links and special files before any extraction step.
   Inspect only README/license documents, never execute package code.
2. Register a separate public-input preparation protocol, specifying exact
   path/case/frame-index mapping and maximum extracted bytes. Prefer the15
   official test clips from the pinned split file; preserve adjacent context
   images needed for offsets[-6,-3,0,3,6]. Do not infer persistent person tracks
   from per-frame head indices.
3. Match VSGaze's UCO test paths and normalized head geometry against supplied
   frames, independently check first/last and deterministic intermediate frames
   in every clip, and save visual evidence. `images_Idiap` in the MTGS loader is
   a loader root convention, not proof that original archive layout matches.
4. Only after media mapping succeeds, register the exact evaluation population,
   eligible binary/unknown mapping, frozen ChildPlay allocation/calibration
   recipe hashes, four exact budgets, new seed stream, primary endpoint and all
   secondary coverage/cost outcomes. No UCO-label tuning. A transfer result must
   disclose that UCO is a VSGaze backbone dataset family.

## Continuation and failure evidence

Runtime status: `outputs/uco-acquisition-k-v1/status.json`, curl logs and response
headers in the same ignored folder. At each continuation, read status and actual
processes/file size first. An interrupted download is resumable after checking
no matching downloader remains active; preserve the failed attempt log. A
complete file is not an alignment or evaluation success. Keep the10-minute
standing research automation active after this acquisition completes.
