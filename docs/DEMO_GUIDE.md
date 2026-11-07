# Run and present the course explorer

The local explorer displays completed benchmark results and replays saved audit
queries. It performs no GPU inference, model training or live-camera analysis.
The frontend uses plain HTML/CSS/JavaScript; Node is not needed to run it.

## Start on this PC

From `G:\ivp`:

```powershell
.\.venv\Scripts\python.exe scripts/serve_course_demo.py --port 8765
```

Wait for `Course explorer ready`, then open
[the local explorer](http://127.0.0.1:8765). Initial loading checks hashes and
reads cached feature tables. Stop with Ctrl+C in the serving terminal. The
server binds to loopback only. If the port is in use, reuse the existing project
server or choose another port; do not stop an unrelated process.

The current work session leaves a checked server running at that address.
If the desktop execution sandbox prevents browser connections, run the same
command in your normal project terminal. This requires no network exposure or
changes to firewall/security settings.

For a new project environment:

```powershell
uv sync --frozen --extra dev --extra research --extra demo --extra plots
uv run python scripts/serve_course_demo.py --port 8765
```

Use the established `.venv` when reproducing saved joblib models: the existing
run used scikit-learn 1.9.1; a differing sklearn version can affect portability.
Code and the lockfile are shared, but the original private local artifacts still
need to be obtained/reproduced separately. The explorer is not a sample-data app.

## Required local artifacts

- Completed main run, features, policies, query plans and draw records in
  `outputs/experiments/course-20261107-v1`.
- Prepared P02 public tables and oracle in `data/processed/vsgaze-17357752-v1`.
- Verified media acquisition metadata in
  `data/raw/childplay/verified-population-v2/acquisition.json` and the JPEG tar
  archives it references, for frame display.
- Strengthening outputs under `outputs/experiments/strengthening-20261107-v1`
  to show the new simple controls and interval diagnostics.

The server accepts explicit `--main`, `--processed`, `--acquisition` and
`--extension` roots for teammate installations. A missing optional extension
does not fabricate its results. Missing media produce a clear frame-display
message. Data, reference labels and media remain outside Git.

## A five-minute demonstration

1. **Results:** choose 10%. Explain that all methods receive 1,032 labels from
   the same 10,316-pair-frame population. Distinguish locked methods from the
   exploratory score/entropy controls. Scores are probabilities, RMSE is in
   percentage points, and coverage is a repeated-audit frequency.
2. **Change to 40%:** the best observed method changes. Point error alone is
   insufficient: inspect the score control's 45.9% normal coverage. Return to
   10% before explaining the primary comparison.
3. **Audit replay:** choose Learned static, 10%, draw 0 and Replay audit.
   The saved plan, estimate and variance must reproduce. This draw estimates
   3.456% using a 7.141% full-model mean plus a weighted residual correction.
4. **Inspect the frame:** move the sequence slider. The two colored boxes are
   supplied head tracks, not detections produced by this app. The score/query
   timeline contains public model outputs. Viewing a frame reveals no new label.
5. **Reveal queried labels:** only labels already in the saved audit plan appear.
   Use the separate benchmark-truth control to explain evaluation versus audit
   inputs. Download replay summary to save the seed/method/budget, estimate,
   interval and query-file hash; it does not export raw query labels.
6. **Compare Score quartiles:** keep the same exact budget. Different methods
   have registered different query streams, so a draw ID does not imply identical
   queried items. Judge methods by the 1,000-draw aggregate, not a favorable example.
7. **Method & limits:** finish with the estimator, shared backbone, development
   costs, media subset, three validation sources and the absence of clinical claims.

The separately registered exact stratified binary reference interval is evaluated
in the [strengthening report](../reports/course-project/strengthening-report.md).
The live replay intentionally retains the original approximate normal interval,
clearly labelled; it does not silently replace the locked audit's uncertainty.

## What has been checked

Nine live API replay cases cover all seven methods, plus boundary draws/budgets.
Exact query counts, unique IDs, original point/variance reproduction, image
serving and rejected invalid methods/draws/budgets/paths were checked. Browser
QA covers Results, budget switching, replay, label/truth toggles, image overlays,
the download, Method & limits, and a 390-pixel responsive viewport. Screenshots
and detailed live QA are retained under the ignored extension `demo-qa` folder.

The user interface is a demonstration of a completed offline benchmark. Its
reference-access boundary prevents accidental use of unqueried labels in the
estimator; it is not a hardened multi-user annotation or clinical product.
