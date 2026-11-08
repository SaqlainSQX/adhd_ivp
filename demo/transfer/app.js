"use strict";
const D=window.TRANSFER_DATA;
const names={uniform:"Uniform · weight 1",K4:"Score strata · weight 1","power-score":"Same strata · weight 0.5"};
const fmt=(n,d=3)=>Number(n).toFixed(d);
const pct=n=>fmt(n*100,1)+"%";
const get=(method,b)=>D.uco.rows.find(r=>r.method===method&&r.budget===b);
document.getElementById("gain").textContent=pct(1-D.uco.comparisons["K4/uniform-b521"].rmse_ratio);
document.getElementById("loss").textContent=pct(D.uco.comparisons["power-score/K4-b521"].rmse_ratio-1);
function renderBudget(){
 const b=Number(document.getElementById("budget").value);
 if(!D.budgets.includes(b))throw Error("Unknown budget");
 const rows=["uniform","K4","power-score"].map(m=>get(m,b));
 const max=Math.max(...rows.map(r=>r.rmse_pp))*1.2;
 const colors=["#6d7978","#187c6b","#c37532"];
 document.getElementById("chart").innerHTML=rows.map((r,i)=>`<div class="bar-row"><span class="bar-label">${names[r.method]}</span><div class="bar-track"><i style="width:${r.rmse_pp/max*100}%;background:${colors[i]}"></i></div><strong>${fmt(r.rmse_pp)} pp</strong></div>`).join("");
 const comparison=D.uco.comparisons[`power-score/K4-b${b}`];
 document.getElementById("chart-caption").textContent=`Budget ${b}: half/full RMSE ratio ${fmt(comparison.rmse_ratio)} [95% draw-bootstrap ${comparison.draw_bootstrap_95pct.map(v=>fmt(v)).join(" to ")}]. Lower RMSE is better. This is fixed-corpus estimation error, not recognition accuracy.`;
 const full=get("K4",b),uni=get("uniform",b);
 document.getElementById("interval-copy").textContent=`At ${b} labels, full-weight K4 normal coverage is ${pct(full.normal.coverage)}. Its exact reference interval covers ${pct(full.exact.coverage)} with mean width ${fmt(full.exact.mean_width_pp,2)} pp; uniform exact width is ${fmt(uni.exact.mean_width_pp,2)} pp.`;
 document.getElementById("results-body").innerHTML=D.uco.rows.map(r=>`<tr class="${r.budget===b?"focus":""}"><td>${r.budget}</td><td>${names[r.method]}</td><td>${fmt(r.rmse_pp,4)}</td><td>${pct(r.normal.coverage)}</td><td>${pct(r.exact.coverage)}</td><td>${fmt(r.exact.mean_width_pp,2)}</td></tr>`).join("");
}
document.getElementById("budget").addEventListener("change",renderBudget);renderBudget();
const child=D.variance.find(r=>r.dataset==="ChildPlay"&&r.budget===1032);
const uco=D.variance.find(r=>r.dataset==="UCO"&&r.budget===521);
document.getElementById("child-exact").textContent=`At 1,032 labels, exact design RMSE ratio is ${fmt(child.exact_RMSE_ratio_half_over_full)}; the saved Monte Carlo ratio is ${fmt(child.MC_RMSE_ratio_half_over_full)}.`;
document.getElementById("uco-exact").textContent=`At 521 labels, exact design RMSE ratio is ${fmt(uco.exact_RMSE_ratio_half_over_full)}; the saved Monte Carlo ratio is ${fmt(uco.MC_RMSE_ratio_half_over_full)}.`;
document.getElementById("variance-body").innerHTML=D.variance.map(r=>`<tr><td>${r.dataset}</td><td>${r.budget}</td><td class="${r.MC_RMSE_ratio_half_over_full>1?"bad":"good"}">${fmt(r.MC_RMSE_ratio_half_over_full,4)}</td><td>${fmt(r.exact_RMSE_ratio_half_over_full,4)}</td></tr>`).join("");
document.getElementById("history-copy").textContent=`The ChildPlay D half/full primary Monte Carlo ratio was ${fmt(D.childplay.primary_half_full_MC.rmse_ratio,4)}, after repeated ChildPlay test inspection. In the original main study, temporal/static RMSE was ${fmt(D.childplay.main_temporal_rmse_pp/D.childplay.main_static_rmse_pp,4)} at 1,032 labels (a loss). In the guided-block study, temporal/static ratio was ${fmt(D.childplay.block_temporal_static_ratio,4)} (also a loss).`;
for(const [name,p]of Object.entries(D.provenance)){const row=document.createElement("p");row.textContent=name;const code=document.createElement("div");code.className="hash";code.textContent=p.sha256;row.appendChild(code);document.getElementById("provenance").appendChild(row);}
function show(view){if(!["results","explanation","limits"].includes(view))view="results";for(const button of document.querySelectorAll("[data-view]")){const active=button.dataset.view===view;button.setAttribute("aria-selected",String(active));document.getElementById(button.dataset.view).hidden=!active;}history.replaceState(null,"",`#view=${view}`);}
for(const button of document.querySelectorAll("[data-view]"))button.addEventListener("click",()=>{show(button.dataset.view);window.scrollTo(0,0);});
document.querySelector(".brand").addEventListener("click",e=>{e.preventDefault();show("results");window.scrollTo(0,0);});
show(new URLSearchParams(location.hash.slice(1)).get("view"));
