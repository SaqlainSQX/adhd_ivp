# L inference implementation and launch

8 November2026. Branch:`codex/uco-inference-l-v1`. The L comparison remains
registered in UCO_TRANSFER_L.md and configs/uco-transfer-l-v1.json. No score-based
tuning, model fit, new oracle mean or evaluation outcome has been computed.

New public adapter validates frame uniqueness, track slots, public pair
membership, native directional probabilities and min-of-directions q. It retains
the reviewed raw UCO border boxes and excludes placeholder boxes. Synthetic
tests cover nontrivial person-ID ordering, wrong native reconstruction,
nonfinite scores and a public-only fixture with no oracle file. All81 project
tests passed in17.52 seconds. Ruff passed. The first test attempt could not use
the sandbox's default temporary directory; rerunning with a new workspace-local
basetemp passed. No implementation logic was changed for that fixture error.

The actual public input contains2,366 context frames,2,357 anchor frames with
eligible pairs,5,219 pairs and at most7 real heads per frame. The script uses
the existing frozen prepare_window/prepare_public_frame, a64-frame CPU cache,
one zero-placeholder slot, fixed person-ID correspondence and zero padding.
Missing public annotations remain missing even if a JPEG exists. It checks exact
cached/uncached tensor equality on the first UCO window and FP32/AMP native
probability difference<=0.002, with no labels. It reuses the accepted same-model
auxiliary-pruning validation; no native social head is removed.

The inference script does not open the external oracle or ambiguity mask even
for hashing. It verifies all other registered public/runtime inputs and the
checkpoint, and records implementation/config hashes before model execution.
It saves per-clip prediction hashes and atomic runtime progress. A failure stays
in its original output; do not silently rerun into that directory or drop rows.

Resource inspection found no Python/Kaggle GPU workload, about1.6 GiB desktop
GPU use and low utilization. A second launch gate refused any Python GPU workload
or more than2,500 MiB existing use. The local GPU job was launched hidden with
a50% per-process CUDA memory limit,4 CPU threads and deterministic seed42.
Another project's supervisor was left untouched; no Kaggle credentials/jobs
were used. The launcher PID7104 and child31216 were observed alive, initially
in loading_model. PIDs are historical observations: inspect actual state.

Command: `.venv-mtgs/Scripts/python.exe -u scripts/infer_uco_transfer.py`.
Launch logs: outputs/uco-inference-l-launch-v1/stdout.log and stderr.log.
Authoritative runtime: outputs/inference/uco-transfer-l-v1/inference-provenance.json.
Read actual progress and live processes before acting; never duplicate the run.

On completion verify all5,219 unique finite scores and recorded hashes, then
implement the registered public-only query-plan stage. Generate/hash all query
streams before any oracle readout. Run the three-method/four-budget comparison,
independent12,000-draw replay and visual report checks in order. Preserve every
loss/tie and the locked ChildPlay evidence. Continue the10-minute standing prompt.
