"use strict";
const D = window.RESEARCH_DATA;
const $ = (id) => document.getElementById(id);
const state = { budget: 1032, view: "overview", health: false, replay: null, frame: 0, frameTimer: null, exportURL: null };
const n = (v, digits = 4) => Number(v).toFixed(digits);
const pct = (v, digits = 3) => `${n(v * 100, digits)}%`;
function table(target, headings, rows) {
  $(target).innerHTML = `<table><thead><tr>${headings.map((h, i) => `<th class="${i ? "num" : ""}">${h}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => `<tr>${row.map((v, i) => `<td class="${i ? "num" : ""}">${v}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
}
function render() {
  const b = state.budget;
  $("gain").textContent = `${n((1 - D.frame.primary.rmse_ratio) * 100, 1)}%`;
  $("temporal-loss").textContent = `${n((D.block_primary.rmse_ratio - 1) * 100, 1)}%`;
  const base = D.frame.results["K4-b1032"].rmse_pp;
  const weighted = D.frame.results["power-score-b1032"].rmse_pp;
  $("primary-chart").innerHTML = [["Score correction · λ = 1", base, ""], ["Weighted correction · λ = 0.5", weighted, "teal"]].map(([label, value, color]) => `<div class="bar-row"><div class="bar-label"><span>${label}</span><strong>${n(value)} pp</strong></div><div class="bar-track"><div class="bar-fill ${color}" style="width:${value / (base * 1.15) * 100}%"></div></div></div>`).join("");
  $("primary-range").textContent = `RMSE ratio ${n(D.frame.primary.rmse_ratio, 3)} · draw-bootstrap 95% range ${D.frame.primary.draw_bootstrap_95pct.map((v) => n(v, 3)).join("–")} · 1,000 saved audits`;
  table("source-table", ["Source", "Pair-frames", "Positive references", "Unweighted RMSE pp", "Weighted RMSE pp", "Error ratio"], D.source_variation.rows.map((r) => [r.alias, r.frames.toLocaleString(), r.positives, n(r.base_rmse), n(r.weighted_rmse), n(r.ratio, 3)]));
  const names = { M1: "Uniform human labels", M2: "Uniform residual correction", M3: "Static error guidance", M4: "Temporal error guidance", M5: "Contextual surrogate · uniform queries" };
  table("main-table", ["Method", "RMSE pp", "Bias pp", "Normal coverage", "Mean normal width pp"], Object.entries(names).map(([key, label]) => { const s = D.main.results[`${key}-b${b}`]; return [label, n(s.rmse_pp), n(s.bias_pp), pct(s.intervals.normal.coverage, 1), n(s.intervals.normal.mean_width_pp, 3)]; }));
  const methods = { K4: "Score correction · λ = 1", "power-score": "Weighted score · λ = 0.5", "power-uniform": "Weighted uniform · λ = 0.5" };
  table("frame-table", ["Method", "RMSE pp", "Normal coverage", "Exact reference coverage", "Reference width pp"], Object.entries(methods).map(([key, label]) => { const s = D.frame.results[`${key}-b${b}`]; return [label, n(s.rmse_pp), pct(s.intervals.normal.coverage, 1), pct(s.intervals.exact_binary_reference.coverage, 1), n(s.intervals.exact_binary_reference.mean_width_pp, 3)]; }));
  const length = Number($("block-length").value);
  const rows = ["Q", "S", "T"].map((name) => { const s = D.guidance[`L${length}-${name}-b${b}`]; return [name === "Q" ? "Native score guidance · Q" : name === "S" ? "Static error guidance · S" : "Temporal error guidance · T", n(s.rmse_pp), n(s.mean_labels, 1), `${n(s.label_quantiles[1], 0)}–${n(s.label_quantiles[3], 0)}`, n(s.mean_blocks, 1), pct(s.normal_coverage, 1)]; });
  const u = D.blocks[`L${length}-w1-b${b}`];
  rows.push(["Uniform blocks · G1", n(u.rmse_pp), n(u.mean_labels, 1), `${n(u.realized_label_quantiles[1], 0)}–${n(u.realized_label_quantiles[3], 0)}`, n(u.mean_queried_blocks, 1), pct(u.normal_coverage, 1)]);
  table("block-table", ["Method", "RMSE pp", "Mean labels", "Labels 5–95%", "Mean blocks", "Normal coverage"], rows);
  table("cost-table", ["Training fraction", "Training labels", "+ validation labels", "RMSE pp at 10%"], ["0.01", "0.05", "0.2", "1"].map((f) => { const key = `score-labels-${f}`; return [pct(Number(f), 0), D.label_cost.training_labels[key].toLocaleString(), D.label_cost.validation_labels.toLocaleString(), n(D.label_cost.results[`${key}-b1032`].rmse_pp)]; }));
  const recipeNames = { equal: "Equal error", "inverse-fraction": "Inverse sampling fraction", "inverse-sqrt-count": "Inverse √query count" };
  table("interval-table", ["Design", "Error recipe", "Coverage", "Mean width pp", "Point outside"], ["M3", "M4", "K4", "power-uniform"].flatMap((name) => Object.entries(recipeNames).map(([recipe, label]) => { const s = D.intervals[`${name}-b${b}-${recipe}`]; return [name, label, pct(s.coverage, 1), n(s.mean_width_pp, 3), pct(s.point_outside_rate, 1)]; })));
}
function switchView(id) {
  if (!$(id)?.classList.contains("view")) return;
  document.querySelectorAll(".view").forEach((v) => { v.hidden = v.id !== id; });
  document.querySelectorAll(".nav").forEach((v) => { v.classList.toggle("active", v.dataset.view === id); v.setAttribute("aria-pressed", String(v.dataset.view === id)); });
  state.view = id;
  history.replaceState(null, "", `#view=${id}`);
  window.scrollTo({ top: 0, behavior: "instant" });
}
function status(text, error = false) { $("replay-status").textContent = text; $("replay-status").classList.toggle("error", error); }
function clearReplay() { state.replay = null; if (state.exportURL) URL.revokeObjectURL(state.exportURL); $("export").removeAttribute("href"); $("replay-content").hidden = true; if (state.health) status("Inputs changed. Replay the saved audit to verify this setting."); }
async function runReplay() {
  if (!state.health) return;
  const draw = Number($("draw").value);
  if (!$("draw").value.trim() || !Number.isInteger(draw) || draw < 0 || draw > 999) { status("Choose an integer draw from 0 to 999.", true); return; }
  $("run-replay").disabled = true; $("replay-content").hidden = true;
  status("Checking query hash, random plan, point estimate and variance…");
  try {
    const args = new URLSearchParams({ method: $("replay-method").value, fraction: D.fractions[D.budgets.indexOf(state.budget)], draw, reveal: $("reveal").checked ? "1" : "0" });
    const response = await fetch(`/api/replay?${args}`);
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Replay unavailable.");
    state.replay = result; state.frame = Math.max(0, result.timeline.findIndex((v) => v.queried));
    $("estimate").textContent = pct(result.estimate.prevalence);
    $("normal").textContent = `Approx. normal: ${pct(result.estimate.normal_low)} – ${pct(result.estimate.normal_high)}`;
    $("native-mean").textContent = pct(result.native_model_mean);
    $("weight-note").textContent = `Native q mean · correction weight λ = ${result.correction_weight}`;
    $("exact").textContent = `${pct(result.exact_binary_reference.low, 2)} – ${pct(result.exact_binary_reference.high, 2)}`;
    $("reference-note").textContent = result.exact_binary_reference.point_outside ? "For this draw, the residual point is outside the separately centered binary reference. Both are retained." : "The binary reference is separately centered; its coverage is evaluated across repeated audits.";
    $("audit-cost").textContent = result.budget.toLocaleString();
    $("frame-range").max = result.timeline.length - 1;
    $("frame-range").value = state.frame;
    $("replay-content").hidden = false;
    $("connection").textContent = "Local cache checked · verified offline replay";
    if (state.exportURL) URL.revokeObjectURL(state.exportURL);
    state.exportURL = URL.createObjectURL(new Blob([JSON.stringify(makeExport(result), null, 2)], { type: "application/json" }));
    $("export").href = state.exportURL;
    $("export").download = `gaze-audit-${result.method}-b${result.budget}-draw${result.draw}.json`;
    renderTimeline(); renderFrame();
    status(`Verified ${result.budget.toLocaleString()} saved queries · draw ${result.draw} · λ = ${result.correction_weight}. ${result.labels_revealed ? "Only queried labels are revealed." : "Reference labels are hidden."}`);
  } catch (error) { state.replay = null; status(error.message, true); }
  finally { $("run-replay").disabled = !state.health; }
}
function renderTimeline() {
  const rows = state.replay?.timeline; if (!rows?.length) return;
  const width = 1000, height = 180, left = 30, right = 980, top = 13, bottom = 151;
  const min = rows[0].position, span = Math.max(1, rows[rows.length - 1].position - min);
  const x = (r) => left + (r.position - min) / span * (right - left);
  const y = (r) => bottom - r.q * (bottom - top);
  const path = rows.map((r, i) => `${i ? "L" : "M"}${x(r).toFixed(2)},${y(r).toFixed(2)}`).join(" ");
  const current = rows[state.frame];
  $("timeline").innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Native score timeline with queried-frame dots and current frame cursor"><line x1="${left}" x2="${right}" y1="${bottom}" y2="${bottom}" stroke="#dbe5e4"/><text x="3" y="18" font-size="10" fill="#60747c">1</text><text x="3" y="153" font-size="10" fill="#60747c">0</text><path d="${path}" fill="none" stroke="#879ca5" stroke-width="1.8"/>${rows.filter((r) => r.queried).map((r) => `<circle cx="${x(r).toFixed(2)}" cy="${y(r).toFixed(2)}" r="3" fill="#087c74"/>`).join("")}<line x1="${x(current)}" x2="${x(current)}" y1="8" y2="157" stroke="#c47a3d" stroke-width="1.5"/><text x="${left}" y="176" font-size="10" fill="#60747c">Frame ${min}</text><text x="${right}" y="176" text-anchor="end" font-size="10" fill="#60747c">${rows[rows.length - 1].position}</text></svg>`;
  $("timeline").querySelector("svg").onclick = (event) => { const box = event.currentTarget.getBoundingClientRect(); const position = min + Math.max(0, Math.min(1, ((event.clientX - box.left) / box.width * 1000 - left) / (right - left))) * span; state.frame = rows.reduce((best, r, i) => Math.abs(r.position - position) < Math.abs(rows[best].position - position) ? i : best, 0); $("frame-range").value = state.frame; renderTimeline(); renderFrame(); };
}
function renderFrame() {
  const row = state.replay?.timeline[state.frame]; if (!row) return;
  $("frame-position").textContent = `Frame ${row.position}`;
  $("frame-q").textContent = n(row.q, 5);
  $("frame-query").textContent = row.queried ? "Queried in this audit" : "Not queried";
  $("frame-label").textContent = row.label === null ? (row.queried ? "Hidden · reveal queried labels to inspect" : "Unavailable · not queried") : (row.label === 1 ? "1 · mutual-looking reference" : "0 · other reference");
  clearTimeout(state.frameTimer);
  state.frameTimer = setTimeout(() => { const image = $("frame-image"); image.hidden = false; $("frame-fallback").hidden = true; image.src = `/api/frame?id=${encodeURIComponent(row.id)}`; }, 100);
}
function makeExport(r) { return { method: r.method, budget: r.budget, draw: r.draw, verified: r.verified, correction_weight: r.correction_weight, native_model_mean: r.native_model_mean, surrogate_mean: r.surrogate_mean, estimate: r.estimate, exact_binary_reference: r.exact_binary_reference, query_file_sha256: r.query_file_sha256, scope: "Offline fixed-corpus replay. Normal interval approximate; binary reference separately centered." }; }
$("export").onclick = () => { status("Audit summary download requested. It contains aggregate statistics and a query-file hash only."); };
document.querySelectorAll(".nav").forEach((v) => { v.onclick = () => switchView(v.dataset.view); });
document.querySelector(".brand").onclick = (event) => { event.preventDefault(); switchView("overview"); };
$("budget").onchange = () => { state.budget = Number($("budget").value); render(); clearReplay(); };
$("block-length").onchange = render;
$("run-replay").onclick = runReplay;
$("replay-method").onchange = clearReplay; $("draw").oninput = clearReplay;
$("reveal").onchange = () => { if (state.replay) runReplay(); };
$("frame-range").oninput = () => { state.frame = Number($("frame-range").value); renderTimeline(); renderFrame(); };
$("frame-image").onerror = () => { $("frame-image").hidden = true; $("frame-fallback").hidden = false; };
$("truth").onchange = async () => { $("truth-value").hidden = !$("truth").checked; if (!$("truth").checked) return; let value = D.main.truth; if (state.health) { try { const response = await fetch("/api/benchmark"); const data = await response.json(); if (response.ok) value = data.prevalence; } catch (_) { /* tracked aggregate remains available */ } } $("truth-value").textContent = `Benchmark prevalence: ${pct(value, 5)}. This aggregate truth is for evaluation and does not select the audit queries or weight.`; };
render(); switchView(location.hash.slice(1).replace(/^view=/, "") || "overview");
(async () => { try { if (location.protocol === "file:") throw new Error("file mode"); const response = await fetch("/api/health", { signal: AbortSignal.timeout(3000) }); const health = await response.json(); state.health = Boolean(response.ok && health.replay_available); } catch (_) { state.health = false; } $("connection").textContent = state.health ? "Local cache available · offline replay" : "Aggregate evidence · optional replay cache unavailable"; $("run-replay").disabled = !state.health; status(state.health ? "Choose a method and saved draw, then replay its recorded audit." : "Aggregate views work without raw data. For replay, run scripts/serve_research_demo.py with the accepted local main/D caches and P02 tables."); })();
