# Run the research explorer

The additive research explorer brings the completed C–G2 extensions into one
local interface. The original seven-method course explorer and all locked
scientific results remain unchanged. No GPU inference, model fitting or webcam
analysis runs in either explorer.

For a new project environment, `uv sync --frozen --extra demo` installs the CPU
dependencies and optional Pillow frame renderer. No CUDA environment or model
weight loading is needed for this research replay.

## Start

From the project root with the established CPU environment:

```powershell
.venv/Scripts/python.exe scripts/serve_research_demo.py --port 8766
```

Open [the research explorer](http://127.0.0.1:8766). A checked service is left
running on this PC. Reuse it if the port is occupied by this project; do not
stop an unrelated service. It binds to loopback only. The first replay reads and
hash-checks the accepted caches and can take several seconds; subsequent replays
reuse the public tables. Viewing a cached frame queries no new label.

For a teammate without the raw caches, open `demo/research/index.html` directly
or use Python's static server:

```powershell
python -m http.server 8766 --bind 127.0.0.1 --directory demo/research
```

The aggregate overview, tables and controls still work; replay explains its
missing prerequisites. To test that mode with the project server, add
`--aggregate-only`. Raw media, query arrays, reference labels and model weights
are deliberately absent from Git. A raw-cache checkout also needs the prepared
P02 tables, accepted main/D outputs and optional verified media archives.

Regenerate the portable aggregate bundle after a reviewed report update:

```powershell
.venv/Scripts/python.exe scripts/build_research_demo_data.py
```

The builder reads tracked aggregate JSON snapshots only. Its provenance hashes
normalize text line endings for cross-platform checkouts. It does not package
raw records, queries, label arrays or benchmark video frames.

## A six-minute course demonstration

1. **Overview:** identify the controlled D comparison at10%: RMSE0.2199 to0.1967
   pp with identical queried records and validation-selected lambda0.5. This is
   a modest exploratory fixed-corpus gain, not an independent test replication.
   The original B1 control's0.2079 pp used a different stream and stays separate.
2. **Frame methods:** compare the locked main methods at10%, then change to40%.
   The best point errors change, while weighted-score normal coverage falls to
   39.1%. RMSE is prevalence-estimation error, not per-frame classifier accuracy.
3. **Blocks & label cost:** choose length5 at10%. Score/static/temporal guidance
   improves on uniform blocks, but longer blocks still lose to frame queries at
   equal expected label cost. Read the actual-label range and query-task count;
   neither measures human time. The C2 curve reuses all25139 validation labels
   and the pretrained backbone even at5% downstream training labels.
4. **Interval reliability:** compare equal and public error-weight recipes.
   Primary width improvement2.59% is below the registered10% target; references
   remain broad. Exact binary references have a separate center and do not
   apply to block totals. Original normal intervals are retained.
5. **Replay an audit:** set10%, weighted score, draw0 and Replay. Native q mean
   stays7.141%; lambda0.5 applies to the residual correction. Query hash/RNG,
   point, FPC variance and exact reference endpoints must reproduce before the
   app marks the replay verified. Move the frame slider; boxes are supplied
   benchmark tracks. Reveal queried labels and observe that unqueried frames
   still have no label. Aggregate benchmark truth has its own explicit control.
6. **Limits:** finish with source heterogeneity, repeated test inspection,
   three validation sources, the53/95 media subset and absent clinical/time
   claims. Download the audit summary if useful; it contains aggregate numbers
   and a query-file hash, with no raw labels, images or record IDs.

The40% K4/draw999 replay is a useful fixed example of the residual point falling
outside its separately centered binary reference. Do not use one favorable or
unfavorable draw to infer repeated-audit coverage; use the1,000-draw tables.

## Evidence and checks

The interface has six views, all four recorded budgets, source-level losses,
fixed-weight replay for three D methods and portable aggregate-only fallback.
Read-only API routes validate method/budget/draw arguments and restrict frames
to the frozen test population. This is an offline teaching replay, not a security
sandbox for hiding labels from a developer with local data access.

Meaningful replay/visibility/fallback tests are in
`tests/test_research_explorer.py`. Live API checks cover invalid inputs and
non-allowlisted paths. Browser QA includes desktop and390px mobile layouts,
all views, the draw999 edge, queried-label reveal, unqueried-label exclusion,
truth separation, media rendering, JSON export and aggregate-only behavior.
Screenshots containing benchmark media stay local/ignored; the tracked preview
shows aggregate overview only. See `docs/RESEARCH_DEMO_H_STATUS.md` for status,
commands and evidence, and `docs/COURSE_RESULTS_UPDATE.md` for the assessment.
