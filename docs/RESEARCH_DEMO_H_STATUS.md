# H research explorer: completed

The additive research explorer is implemented and checked. The original
seven-method explorer, main reports, frozen policies and C–G2 numerical evidence
remain unchanged. No new inference, model fitting or dataset search occurred.

Open [the local research explorer](http://127.0.0.1:8766). The checked loopback
service uses scripts/serve_research_demo.py; launcher PID30660, listener PID30428.
It was started
hidden outside the network-restricted sandbox so browser QA can reach it.
Do not duplicate the service or stop an unrelated process. A temporary
aggregate-only service on8767 was used for fallback QA and has been stopped.

## Completed deliverables

- Portable aggregate-only six-view interface under demo/research, built from
  tracked snapshots. It remains useful without raw media, labels or query caches.
- Verified D replay for weighted score, same-query unweighted K4 and weighted
  uniform, including native q/weight separation, exact-query hash/RNG, saved
  point/FPC variance and integer exact-reference endpoint checks.
- Hidden-by-default sampled labels, explicit queried-label reveal, unqueried
  labels unavailable, separate aggregate truth control, cached media and supplied
  track boxes, public timeline/frame slider and aggregate-only JSON export.
- C downstream cost, E source losses, F conservative interval widths/failures,
  G1/G2 expected/realized label costs, and all original main outcomes retained.
- Updated walkthrough in RESEARCH_EXPLORER_GUIDE.md and candid assessment in
  COURSE_RESULTS_UPDATE.md, with links to all full appendices.

## QA evidence

Numerical/backend cases cover all four budgets and draw edges, shared K4/weighted
queries, sampled-only label reveal, missing caches and invalid inputs. The full
suite has78 passing tests on this PC; see outputs/h-full-tests-v3.log. Ruff
and node --check pass. Live HTTP checks cover invalid methods/draws/reveal,
duplicate arguments, non-allowlisted paths and a verified uniform replay.

Browser QA used the computer-use skill and the in-app browser. All six views,
budget changes, block-length selection, desktop1280 and mobile390 breakpoints,
an edge K4/40%/draw999 replay, weighted score/10% and uniform/5% replays, queried
reveal, unqueried exclusion, aggregate truth separation, slider, image rendering,
invalid draw1000 and a real downloaded export were checked. Mobile document
width375 at viewport390 showed no page overflow; tables have local scrolling.
Aggregate-only mode disables replay with a prerequisite message while evidence
views remain usable. Browser console showed no application errors after final
reload; temporary viewport overrides were reset and the primary tab retained.

Two UI issues were corrected before acceptance: fragment IDs initially caused
native anchor scrolling past the budget header, so view hashes use #view=...;
mobile method controls were widened and the horizontal nav scrollbar styled.
The initial browser visibility wait returned while the first cold replay was
still loading; later observed state confirmed success. The actual export helper
was slow but downloaded valid aggregate-only JSON. No numerical failure occurred.

Local screenshots/media checks remain under outputs/research-demo-h/qa.
The tracked preview reports/course-project/research-explorer-preview.jpg contains
only aggregate overview cards, with no benchmark frame or raw reference labels.
Downloaded JSON was inspected: no query/timeline arrays or raw record IDs/labels.
Scientific snapshot hashes and original explorer files are checked for changes
before Git sync. Raw outputs, screenshots with media and credentials stay ignored.

```powershell
.venv/Scripts/python.exe scripts/build_research_demo_data.py
.venv/Scripts/python.exe scripts/serve_research_demo.py --port 8766
.venv/Scripts/python.exe -m pytest -q --basetemp outputs/pytest-h-full-v3
.venv/Scripts/ruff.exe check src scripts tests
node --check demo/research/app.js
```

Next: feasibility/provenance review in EXTERNAL_VALIDATION_REVIEW_I.md. No new
performance experiment or GPU work is queued by H. The recurring10-minute
research continuation remains active, and should advance I from actual files.
