# Transfer appendix: course walkthrough

Open http://127.0.0.1:8768 while the local service is running. The original
research explorer remains at http://127.0.0.1:8766. This appendix uses only
checksum-verified tracked aggregates; it never reads source media, oracle,
per-query records or model weights.

From the project environment, rebuild with
`.venv/Scripts/python.exe scripts/build_transfer_appendix.py`, then serve with
`.venv/Scripts/python.exe scripts/serve_transfer_appendix.py --port 8768`.
Check for an existing listener before starting another service. Stop only a
service you started; do not alter another agent's workload. Team review branch:
`codex/transfer-appendix-n-v1`. Earlier explorers/results are preserved.

## Five-minute presentation

1. At the top, distinguish the secondary allocation gain (25.6% lower RMSE
   versus uniform) from the primary half-weight loss (26.9% higher RMSE versus
   full weight). Both use521 labels. This is audit estimation, not recognition
   accuracy or a newly trained gaze model.
2. In Results & intervals, select260,521,1043 and2087. All12 method/budget
   cells remain in the table; the selected budget is highlighted. At260, half
   weight even loses to uniform. Bootstrap intervals concern repeated random
   audits on this fixed corpus, not independent videos or people.
3. Read the interval card: at521 labels the shared K4 exact reference interval
   has99.4% coverage but16.04 pp mean width, versus uniform7.41 pp. The two K4
   weights share queries and the same reference interval. Normal intervals are
   diagnostics; earlier coverage failures remain in the original explorer.
4. Open Why it reverses. Compare Monte Carlo and exact-design ratios; they are
   different quantities. Explain the identity B-0.75C, explicitly post-hoc and
   descriptive. No optimal weight or new policy was fitted on test labels.
5. Open Scope & reproducibility. Present the index repair, sampled visual/track
   limitations, raw-box preprocessing difference,15 clips/4 TV shows, VSGaze
   backbone-family exposure and no ADHD diagnosis. Show source checksums and the
   preserved earlier temporal/block losses. Follow links to the full reports.

Suggested claim: "Score-guided sampling helped on a second benchmark, but the
half-weight residual correction did not transfer." Keep the main ChildPlay
submission and show UCO as an honest transfer/limitations appendix.

## Portable aggregate export

The export link points to the allowlisted data.json payload. Its bytes were
retrieved over the running HTTP service, saved to
outputs/transfer-appendix-n-v1/transfer-evidence-summary.json and verified against
the static artifact. It contains no per-person/reference/query records. You can
also open http://127.0.0.1:8768/data.json and save that JSON directly.

The in-app browser's download-capture helper timed out; an actual physical
browser-downloaded file is **not** claimed as verified. The page's data endpoint,
payload and workspace-saved HTTP export are verified. Do not repeatedly call
downloadMedia or waitForEvent(download) in this environment; use the JSON URL
or an ordinary browser's save function if a local export file is needed.
