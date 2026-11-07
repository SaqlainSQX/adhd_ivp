"use strict";
const $ = (id) => document.getElementById(id);
const names = {
  M1: "Uniform human",
  M2: "Uniform residual",
  M3: "Learned static",
  M4: "Learned temporal",
  M5: "Contextual surrogate",
  "q-quartiles": "Score quartiles",
  "entropy-quartiles": "Entropy quartiles",
};
const state = { summary: null, fraction: 0.1, replay: null, labels: false };
const pct = (v) => `${(100 * v).toFixed(3)}%`;
const pp = (v) => Number(v).toFixed(4);
const budget = (f) => Math.floor(f * 10316 + 0.5);
const node = (tag, cls, text) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
};
const setStatus = (id, text, error = false) => {
  $(id).textContent = text;
  $(id).classList.toggle("error", error);
};
async function api(url) {
  const response = await fetch(url);
  const data = await response.json();
  if (!response.ok)
    throw new Error(data.error || `Request failed (${response.status})`);
  return data;
}
function showPanel(id) {
  for (const e of document.querySelectorAll(".panel")) e.hidden = e.id !== id;
  for (const b of document.querySelectorAll(".nav-button")) {
    const active = b.dataset.panel === id;
    b.classList.toggle("active", active);
    b.setAttribute("aria-pressed", String(active));
  }
  window.scrollTo({ top: 0, behavior: "smooth" });
}
for (const b of document.querySelectorAll(".nav-button"))
  b.addEventListener("click", () => showPanel(b.dataset.panel));
function metric(value, label, hint) {
  const box = node("div", "metric");
  box.append(
    node("div", "metric-value", value),
    node("div", "metric-label", label),
  );
  if (hint) box.append(node("div", "metric-hint", hint));
  return box;
}
function getRows() {
  const n = budget(state.fraction),
    s = state.summary;
  let rows = ["M1", "M2", "M3", "M4", "M5"].map((method) => ({
    method,
    extension: false,
    ...s.main.results[`${method}-b${n}`],
  }));
  if (s.simple_controls)
    rows = rows.concat(
      ["q-quartiles", "entropy-quartiles"].map((method) => ({
        method,
        extension: true,
        ...s.simple_controls.results[`${method}-b${n}`],
      })),
    );
  return rows;
}
function drawResults() {
  const s = state.summary,
    n = budget(state.fraction),
    rows = getRows();
  $("budget-detail").textContent =
    `${n.toLocaleString()} labels / 10,316 pair-frames`;
  for (const b of $("budget-switch").children) {
    const active = Number(b.dataset.fraction) === state.fraction;
    b.classList.toggle("active", active);
    b.setAttribute("aria-pressed", String(active));
  }
  $("error-chart").replaceChildren();
  const maximum = Math.max(...rows.map((r) => r.rmse_pp)) * 1.05;
  for (const r of rows) {
    const row = node("div", "bar-row"),
      track = node("div", "bar-track"),
      fill = node(
        "div",
        `bar-fill${r.extension ? " extension" : r.method === "M4" ? " temporal" : ""}`,
      );
    fill.style.width = `${(100 * r.rmse_pp) / maximum}%`;
    track.append(fill);
    row.append(
      node("span", "bar-label", names[r.method]),
      track,
      node("span", "bar-number", r.rmse_pp.toFixed(3)),
    );
    $("error-chart").append(row);
  }
  $("result-rows").replaceChildren();
  for (const r of rows) {
    const tr = document.createElement("tr"),
      interval = r.intervals.normal;
    for (const text of [
      names[r.method],
      pp(r.rmse_pp),
      pp(r.bias_pp),
      `${(100 * interval.coverage).toFixed(1)}%`,
      pp(interval.mean_width_pp),
    ])
      tr.append(node("td", null, text));
    const cell = node("td"),
      tag = node(
        "span",
        `study-tag${r.extension ? " extension" : ""}`,
        r.extension ? "Exploratory control" : "Locked main",
      );
    cell.append(tag);
    tr.append(cell);
    $("result-rows").append(tr);
  }
  const best = rows.reduce((a, b) => (a.rmse_pp < b.rmse_pp ? a : b));
  $("finding-title").textContent =
    `Lowest observed error: ${names[best.method].toLowerCase()}.`;
  $("finding-body").textContent =
    `At this budget its RMSE is ${pp(best.rmse_pp)} percentage points. The main temporal extension did not beat static guidance. Simple controls are exploratory follow-ups on the same inspected corpus.`;
  const ci = s.coverage_extension;
  $("interval-results").replaceChildren();
  if (!ci) {
    $("interval-results").append(
      node(
        "p",
        "small-copy",
        "Interval diagnostics are not yet available in this local run.",
      ),
    );
    return;
  }
  const scroll = node("div", "table-scroll"),
    table = node("table"),
    head = node("thead"),
    hr = node("tr");
  for (const text of ["Method", "Interval", "Coverage", "Mean width (pp)"])
    hr.append(node("th", null, text));
  head.append(hr);
  table.append(head);
  const body = node("tbody");
  for (const method of ["M3", "M4"]) {
    const r = ci.results[`${method}-b${n}`];
    for (const [key, label] of [
      ["normal", "Original normal"],
      ["student_t", "Student-t (approx.)"],
      ["validation_calibrated", "Validation-calibrated"],
    ]) {
      const x = r.intervals[key],
        tr = node("tr");
      for (const text of [
        names[method],
        label,
        `${(100 * x.coverage).toFixed(1)}%`,
        x.mean_width_pp === null ? "Unbounded" : pp(x.mean_width_pp),
      ])
        tr.append(node("td", null, text));
      body.append(tr);
    }
  }
  table.append(body);
  scroll.append(table);
  $("interval-results").append(scroll);
}
function initSummary(s) {
  state.summary = s;
  $("overview-metrics").replaceChildren(
    metric(
      "53",
      "Verified public sources",
      "40 train · 3 validation · 10 test",
    ),
    metric(
      "20,000",
      "Checked main audit evaluations",
      "Independent query and estimate replay",
    ),
    metric(
      "1,032",
      "Labels at the primary 10% budget",
      "Same exact budget for every method",
    ),
    metric(
      `${(100 * (1 - (s.simple_controls ? s.simple_controls.results["q-quartiles-b1032"].rmse_pp : s.main.results["M3-b1032"].rmse_pp) / s.main.results["M2-b1032"].rmse_pp)).toFixed(1)}%`,
      s.simple_controls
        ? "Lower primary RMSE: score vs uniform"
        : "Lower primary RMSE: static vs uniform",
      s.simple_controls
        ? "Exploratory control / fixed corpus"
        : "Fixed-corpus observation; main study",
    ),
  );
  $("reference-prevalence").textContent = pct(s.main.reference_prevalence);
  $("model-mean").textContent = pct(s.main.model_only_mean);
  for (const f of [0.05, 0.1, 0.2, 0.4]) {
    const b = node("button", null, `${Math.round(f * 100)}%`);
    b.type = "button";
    b.dataset.fraction = f;
    b.addEventListener("click", () => {
      state.fraction = f;
      drawResults();
    });
    $("budget-switch").append(b);
  }
  for (const m of s.methods) {
    const o = node("option", null, names[m]);
    o.value = m;
    o.selected = m === "M3";
    $("replay-method").append(o);
  }
  drawResults();
  setStatus(
    "global-status",
    "Verified subset · frozen predictions · exact label budgets · exploratory course study",
  );
}
function queryTable() {
  const r = state.replay;
  $("query-rows").replaceChildren();
  for (const q of r.queries.slice(0, 12)) {
    const tr = node("tr");
    tr.append(
      node("td", null, q.id),
      node("td", null, q.q.toFixed(4)),
      node("td", null, state.labels ? String(q.label) : "Hidden"),
    );
    $("query-rows").append(tr);
  }
  $("query-preview-caption").textContent =
    `Preview of 12 of ${r.budget.toLocaleString()} queried pair-frames. 1 = mutual looking; 0 = benchmark negative.`;
  $("label-toggle").textContent = state.labels
    ? "Hide queried labels"
    : "Reveal queried labels";
  $("label-toggle").setAttribute("aria-pressed", String(state.labels));
}
function timeline() {
  const data = state.replay.timeline,
    svg = $("timeline");
  svg.replaceChildren();
  const ns = "http://www.w3.org/2000/svg",
    make = (tag, attrs) => {
      const el = document.createElementNS(ns, tag);
      for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
      return el;
    };
  const x = (i) => 36 + (i / Math.max(1, data.length - 1)) * 850,
    y = (q) => 140 - q * 120;
  for (const tick of [0, 0.5, 1]) {
    svg.append(
      make("line", {
        x1: 36,
        y1: y(tick),
        x2: 886,
        y2: y(tick),
        stroke: "#e2e8e5",
        "stroke-width": 1,
      }),
    );
    const text = make("text", {
      x: 6,
      y: y(tick) + 4,
      fill: "#62757e",
      "font-size": 11,
    });
    text.textContent = String(tick);
    svg.append(text);
  }
  for (const [field, color, width] of [
    ["context_mean", "#98bcae", 2],
    ["q", "#285f86", 1.6],
  ]) {
    let d = "";
    data.forEach((p, i) => {
      d += `${i === 0 || p.position - data[i - 1].position > 1 ? "M" : "L"}${x(i).toFixed(2)},${y(p[field]).toFixed(2)} `;
    });
    svg.append(
      make("path", { d, fill: "none", stroke: color, "stroke-width": width }),
    );
  }
  data.forEach((p, i) => {
    if (p.queried)
      svg.append(make("circle", { cx: x(i), cy: 156, r: 2, fill: "#ce7950" }));
  });
  const cursor = Number($("frame-slider").value);
  svg.append(
    make("line", {
      x1: x(cursor),
      x2: x(cursor),
      y1: 16,
      y2: 164,
      stroke: "#ce7950",
      "stroke-width": 1,
      "stroke-dasharray": "4 4",
    }),
  );
}
function updateFrame() {
  const data = state.replay.timeline,
    index = Number($("frame-slider").value),
    p = data[index];
  if (!p) return;
  $("frame-error").hidden = true;
  $("frame-image").hidden = false;
  $("frame-image").src = `/api/frame?id=${encodeURIComponent(p.id)}`;
  $("frame-position").textContent = String(p.position);
  $("frame-caption").textContent =
    `${state.replay.example.clip_id} · tracks ${state.replay.example.person_a} / ${state.replay.example.person_b} · q ${p.q.toFixed(4)} · ${p.queried ? "queried frame" : "public frame; reference not revealed"}`;
  timeline();
}
$("frame-image").addEventListener("error", () => {
  $("frame-image").hidden = true;
  $("frame-error").textContent =
    "This local frame could not be displayed. Check that downloaded media and the optional Pillow dependency are available.";
  $("frame-error").hidden = false;
});
$("frame-slider").addEventListener("input", () => {
  const p = state.replay.timeline[Number($("frame-slider").value)];
  $("frame-position").textContent = String(p.position);
  timeline();
});
$("frame-slider").addEventListener("change", updateFrame);
$("label-toggle").addEventListener("click", () => {
  state.labels = !state.labels;
  queryTable();
});
$("truth-toggle").addEventListener("click", () => {
  $("truth-result").hidden = !$("truth-result").hidden;
  $("truth-toggle").textContent = $("truth-result").hidden
    ? "Compare with benchmark truth"
    : "Hide benchmark comparison";
});
$("export-replay").addEventListener("click", () => {
  const r = state.replay;
  const payload = {
    method: r.method,
    fraction: r.fraction,
    draw: r.draw,
    budget: r.budget,
    estimate: r.estimate,
    query_file_sha256: r.query_file_sha256,
    verified: r.verified,
    scope: "Saved offline audit; approximate intervals; benchmark subset",
  };
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" }),
  );
  const a = document.createElement("a");
  a.href = url;
  a.download = `audit-${r.method}-b${r.budget}-draw${r.draw}.json`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
$("replay-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = $("replay-submit");
  button.disabled = true;
  setStatus(
    "replay-status",
    "Checking saved query hashes and reproducing the audit…",
  );
  try {
    const query = new URLSearchParams(new FormData(event.currentTarget));
    const r = await api(`/api/replay?${query}`);
    state.replay = r;
    state.labels = false;
    $("replay-content").hidden = false;
    $("replay-metrics").replaceChildren(
      metric(
        pct(r.estimate.prevalence),
        "Audited prevalence estimate",
        names[r.method],
      ),
      metric(
        `${pct(r.estimate.normal_low)}–${pct(r.estimate.normal_high)}`,
        "Approximate normal 95% interval",
        "Assess repeated-audit coverage in Results",
      ),
      metric(
        r.budget.toLocaleString(),
        "Queried labels",
        "Exact saved budget; no replacement",
      ),
      metric(
        "Reproduced",
        "Query plan, estimate and variance",
        "Matches the recorded experiment",
      ),
    );
    $("correction-steps").replaceChildren();
    for (const [label, value, cls] of [
      ["Full surrogate mean", pct(r.surrogate_mean), ""],
      [
        "Weighted residual correction",
        `${(100 * (r.estimate.prevalence - r.surrogate_mean)).toFixed(3)} pp`,
        "",
      ],
      ["Audited estimate", pct(r.estimate.prevalence), "total"],
    ]) {
      const step = node("div", `correction-step ${cls}`);
      step.append(node("span", null, label), node("strong", null, value));
      $("correction-steps").append(step);
    }
    $("truth-result").hidden = true;
    $("truth-toggle").textContent = "Compare with benchmark truth";
    $("truth-result").textContent =
      `Fixed benchmark truth: ${pct(state.summary.main.reference_prevalence)}. This draw's error: ${(100 * (r.estimate.prevalence - state.summary.main.reference_prevalence)).toFixed(3)} percentage points. Truth is used for evaluation, not sampling.`;
    $("frame-slider").max = Math.max(0, r.timeline.length - 1);
    const initial = Math.max(
      0,
      r.timeline.findIndex((p) => p.queried),
    );
    $("frame-slider").value = initial;
    queryTable();
    updateFrame();
    setStatus(
      "replay-status",
      `${names[r.method]} · draw ${r.draw} · ${r.budget.toLocaleString()} labels · saved audit verified`,
    );
  } catch (error) {
    setStatus("replay-status", error.message, true);
  } finally {
    button.disabled = false;
  }
});
api("/api/summary")
  .then(initSummary)
  .catch((error) =>
    setStatus(
      "global-status",
      `Unable to load local evidence: ${error.message}`,
      true,
    ),
  );
